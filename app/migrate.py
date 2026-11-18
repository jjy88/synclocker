"""Apply SQL files in migrations/ in filename order. Usage: python -m app.migrate"""
import pathlib

import psycopg

from app import config

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent.parent / "migrations"


def run() -> list[str]:
    applied_now = []
    with psycopg.connect(config.DATABASE_URL) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        conn.commit()
        done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in done:
                continue
            conn.execute(path.read_text())
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
            conn.commit()
            applied_now.append(path.name)
    return applied_now


if __name__ == "__main__":
    applied = run()
    print("Applied:", ", ".join(applied) if applied else "nothing (already up to date)")
