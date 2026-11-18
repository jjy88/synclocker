import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
import psycopg.errors

from app import config
from app.db import pool
from app.errors import EmailTaken, Unauthorized
from app.ids import new_id
from app.repositories import users as users_repo

_PBKDF2_ROUNDS = 200_000


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _PBKDF2_ROUNDS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def register(email: str, password: str) -> dict:
    email = email.strip().lower()
    user_id = new_id("usr")
    try:
        with pool.connection() as conn:
            users_repo.insert(conn, user_id, email, _hash_password(password))
    except psycopg.errors.UniqueViolation:
        raise EmailTaken()
    return {"user_id": user_id, "email": email}


def login(email: str, password: str) -> dict:
    email = email.strip().lower()
    with pool.connection() as conn:
        user = users_repo.get_by_email(conn, email)
    # Same error for unknown email and wrong password, so the API does not reveal which emails exist.
    if user is None or not _verify_password(password, user["password_hash"]):
        raise Unauthorized("Invalid email or password")
    return {"access_token": _issue_token(user["id"]), "token_type": "bearer"}


def _issue_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> str:
    """Return the user id inside a valid token. Any problem becomes 401.

    The algorithm list is fixed to HS256, so a token that claims alg=none or another
    algorithm is rejected. The signature is checked against our secret, so a forged or
    modified token is rejected. exp and sub must be present.
    """
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        raise Unauthorized("Invalid or expired token")
    return payload["sub"]
