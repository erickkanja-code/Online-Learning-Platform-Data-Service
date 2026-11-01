"""PostgreSQL connection pool and helpers."""

import os
from contextlib import contextmanager
from pathlib import Path

from psycopg2.pool import SimpleConnectionPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/learning_platform"
)

pool = SimpleConnectionPool(minconn=1, maxconn=5, dsn=DATABASE_URL)


@contextmanager
def get_connection():
    """Borrow a connection from the pool and always give it back afterwards."""
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


def run_sql_file(conn, path: str | Path) -> None:
    """Run every SQL statement in a file, as one transaction."""
    sql = Path(path).read_text(encoding="utf-8")
    with conn:
        with conn.cursor() as cur:
            cur.execute(sql)