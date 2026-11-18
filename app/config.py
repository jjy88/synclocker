import os


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# Secrets and connection strings come from the environment only, never from source code.
DATABASE_URL = _required("DATABASE_URL")
JWT_SECRET = _required("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))
HOLD_TTL_MINUTES = int(os.environ.get("HOLD_TTL_MINUTES", "10"))
