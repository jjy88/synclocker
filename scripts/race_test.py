"""Concurrency demo: many users try to hold the same locker at the same moment.

It creates a fresh location with LOCKERS large lockers and a fresh session, registers N users,
makes all N threads wait at a barrier, then releases them together. With correct locking,
exactly LOCKERS requests get 201 and all others get 409.

Usage (service must be running):
    python -m scripts.race_test --base-url http://localhost:8000 --users 20 --lockers 1
"""
import argparse
import collections
import sys
import threading
import uuid

import httpx
import psycopg

from app import config


def create_world(lockers: int) -> str:
    tag = uuid.uuid4().hex[:8]
    loc, ses = f"loc_race_{tag}", f"ses_race_{tag}"
    with psycopg.connect(config.DATABASE_URL) as conn:
        conn.execute("INSERT INTO locations (id, name) VALUES (%s, 'Race test')", (loc,))
        conn.execute(
            "INSERT INTO rental_sessions (id, location_id, name, starts_at, ends_at, price_cents) "
            "VALUES (%s, %s, 'Race session', now() + interval '1 day', now() + interval '2 days', 1000)",
            (ses, loc),
        )
        for i in range(lockers):
            conn.execute(
                "INSERT INTO lockers (id, location_id, size) VALUES (%s, %s, 'large')",
                (f"lkr_{tag}_{i}", loc),
            )
    return ses


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--users", type=int, default=20)
    parser.add_argument("--lockers", type=int, default=1)
    args = parser.parse_args()

    session_id = create_world(args.lockers)
    print(f"Session {session_id}: {args.lockers} large locker(s), {args.users} users")

    tokens = []
    with httpx.Client(base_url=args.base_url, timeout=30) as client:
        for _ in range(args.users):
            email = f"race_{uuid.uuid4().hex[:10]}@example.com"
            client.post("/auth/register", json={"email": email, "password": "password123"}).raise_for_status()
            r = client.post("/auth/login", json={"email": email, "password": "password123"})
            r.raise_for_status()
            tokens.append(r.json()["access_token"])

    barrier = threading.Barrier(args.users)
    results: list[int] = []
    lock = threading.Lock()

    def worker(token: str) -> None:
        with httpx.Client(base_url=args.base_url, timeout=30) as c:
            barrier.wait()  # all threads fire at the same moment
            r = c.post(
                f"/sessions/{session_id}/holds",
                json={"size": "large"},
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())},
            )
        with lock:
            results.append(r.status_code)

    threads = [threading.Thread(target=worker, args=(t,)) for t in tokens]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    counts = collections.Counter(results)
    print("Status codes:", dict(counts))

    with psycopg.connect(config.DATABASE_URL) as conn:
        active = conn.execute(
            "SELECT count(*), count(DISTINCT locker_id) FROM holds WHERE session_id = %s AND status = 'HELD'",
            (session_id,),
        ).fetchone()
    print(f"Active holds in database: {active[0]} on {active[1]} distinct locker(s)")

    ok = (
        counts.get(201, 0) == min(args.lockers, args.users)
        and counts.get(409, 0) == args.users - min(args.lockers, args.users)
        and active[0] == active[1] == counts.get(201, 0)
    )
    print("PASS: no double booking" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
