-- Migration 001: core rental tables

CREATE TABLE users (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE locations (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE rental_sessions (
    id          TEXT PRIMARY KEY,
    location_id TEXT NOT NULL REFERENCES locations (id),
    name        TEXT NOT NULL,
    starts_at   TIMESTAMPTZ NOT NULL,
    ends_at     TIMESTAMPTZ NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    CHECK (ends_at > starts_at)
);

CREATE TABLE lockers (
    id          TEXT PRIMARY KEY,
    location_id TEXT NOT NULL REFERENCES locations (id),
    size        TEXT NOT NULL CHECK (size IN ('small', 'medium', 'large'))
);

CREATE TABLE holds (
    id         TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES rental_sessions (id),
    locker_id  TEXT NOT NULL REFERENCES lockers (id),
    user_id    TEXT NOT NULL REFERENCES users (id),
    status     TEXT NOT NULL CHECK (status IN ('HELD', 'EXPIRED', 'CONVERTED', 'RELEASED')),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reservations (
    id         TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES rental_sessions (id),
    locker_id  TEXT NOT NULL REFERENCES lockers (id),
    hold_id    TEXT NOT NULL UNIQUE REFERENCES holds (id),
    user_id    TEXT NOT NULL REFERENCES users (id),
    status     TEXT NOT NULL CHECK (status IN ('CONFIRMED', 'CANCELLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
