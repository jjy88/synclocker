-- Migration 002: idempotency keys for state-changing operations
-- A key belongs to one user. Only successful responses are stored.
-- Keys are kept without expiry in this MVP.

CREATE TABLE idempotency_keys (
    user_id       TEXT NOT NULL REFERENCES users (id),
    key           TEXT NOT NULL,
    response_body JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, key)
);
