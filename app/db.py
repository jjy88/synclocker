from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app import config

# The pool is opened in the application lifespan (see main.py).
# `with pool.connection() as conn:` is one transaction: commit on success, rollback on exception.
pool = ConnectionPool(
    config.DATABASE_URL,
    min_size=2,
    max_size=20,
    open=False,
    kwargs={"row_factory": dict_row},
)
