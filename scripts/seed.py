"""Insert demo data. Safe to run more than once. Usage: python -m scripts.seed"""
import psycopg

from app import config


def seed() -> None:
    with psycopg.connect(config.DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO locations (id, name) VALUES ('loc_demo', 'Demo Ski Resort') ON CONFLICT DO NOTHING"
        )
        # Session times are relative to today so the demo data never goes stale.
        conn.execute(
            "INSERT INTO rental_sessions (id, location_id, name, starts_at, ends_at, price_cents) VALUES "
            "('ses_demo_day', 'loc_demo', 'Full day', now() + interval '1 day', now() + interval '2 days', 1500), "
            "('ses_demo_half', 'loc_demo', 'Half day', now() + interval '1 day', now() + interval '1 day 4 hours', 900) "
            "ON CONFLICT DO NOTHING"
        )
        conn.execute(
            "INSERT INTO lockers (id, location_id, size) VALUES "
            "('lkr_101', 'loc_demo', 'small'), ('lkr_102', 'loc_demo', 'medium'), "
            "('lkr_103', 'loc_demo', 'medium'), ('lkr_104', 'loc_demo', 'large') "
            "ON CONFLICT DO NOTHING"
        )
    print("Seeded location loc_demo with sessions ses_demo_day, ses_demo_half and lockers lkr_101..lkr_104")


if __name__ == "__main__":
    seed()
