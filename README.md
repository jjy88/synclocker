# SyncLocker

Company: SyncApp. Product: SyncLocker, a backend service for reserving short-term storage lockers at ski resorts and event venues.

Course: SOEN 387, Fall 2026. Stack: FastAPI, PostgreSQL, Docker (database), OpenAPI 3.

## Status (milestone)

Implemented:
- REST API with a published OpenAPI contract (`openapi.json`)
- Layered design: `app/api` (interface), `app/services` (domain rules), `app/repositories` (SQL)
- PostgreSQL persistence with two ordered migrations (`migrations/`)
- Locker holds protected against double booking (pessimistic row locking inside one transaction)
- Idempotency-Key on `POST /sessions/{session_id}/holds`
- JWT bearer authentication; ownership checks in the service layer
- Testing front end at `/ui/`

Not implemented yet (planned for the final checkpoint):
- `POST /holds/{hold_id}/checkout` returns `501 Not Implemented`. Stripe integration, the background payment worker, retry with backoff and refund handling are not built yet, so no reservation can be created through the API yet.
- Payment-related migration, Docker image for the API, health checks, structured logs with correlation id.

## Run it

Requirements: Python 3.11+, Docker (for PostgreSQL).

```bash
cp .env.example .env            # then edit JWT_SECRET
docker compose up -d db         # PostgreSQL on localhost:5432
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
set -a && source .env && set +a # load environment variables
python -m app.migrate           # apply migrations
python -m scripts.seed          # demo data: location loc_demo, sessions, lockers
python -m uvicorn app.main:app --port 8000
```

Open http://localhost:8000/ui/ for the test console and http://localhost:8000/docs for the interactive API docs.

## Concurrency demo

With the service running:

```bash
python -m scripts.race_test --users 20 --lockers 1
```

It creates a fresh session with one large locker, fires 20 simultaneous hold requests, and checks that exactly one returns 201, the other 19 return 409, and the database holds exactly one active hold.

## Tests

```bash
python -m pytest -q
```

The tests need `DATABASE_URL` and `JWT_SECRET` in the environment (same values as above). They create their own data and do not need the server to be running.

If you change a route or schema, regenerate the contract: `python -m scripts.export_openapi`. A test fails if `openapi.json` is out of date.

## How double booking is prevented

`hold_service.create_hold` runs in one transaction:
1. Claim the idempotency key.
2. `SELECT ... FOR UPDATE` on all lockers of the requested size at the location, ordered by id. A concurrent request waits here until the first transaction finishes.
3. Take the first locker that has no live hold (status HELD and not past `expires_at`) and no confirmed reservation, and insert the hold. An expired hold is simply ignored by this check, so it no longer blocks the locker.
4. If none is free, raise `NoLockerAvailable` (409). The transaction rolls back, including the idempotency key.

## API summary

| Method and path | Auth | Notes |
|---|---|---|
| POST /auth/register, POST /auth/login | no | login returns a JWT |
| GET /locations/{location_id}/sessions | no | list rental sessions |
| GET /sessions/{session_id}/availability | no | every locker with an `available` flag |
| POST /sessions/{session_id}/holds | yes | needs `Idempotency-Key` header; 201, 400, 401, 404, 409 |
| GET /holds/{hold_id} | yes | owner only (403 otherwise) |
| POST /holds/{hold_id}/checkout | yes | 501 for now |
| GET /me/reservations | yes | own reservations only |
| DELETE /reservations/{reservation_id} | yes | owner only (403 otherwise); 204 |

Errors returned by the operations above use the same shape: `{"error": {"code": "...", "message": "..."}}`. Requests to URLs that do not exist get the framework default 404 response.

Known limitations: reusing an `Idempotency-Key` with a different request body returns the first stored response instead of an error, and a hold can be created for a rental session that has already ended.

Idempotency keys are scoped per user and stored without expiry in this MVP. Only successful responses are stored; a failed attempt (for example 409) can be retried with the same key. A retry with the same key returns the stored response without creating a second hold.
