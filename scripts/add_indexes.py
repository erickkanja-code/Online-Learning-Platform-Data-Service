"""Add the performance indexes to the database.

Usage:
    poetry run python scripts/add_indexes.py
"""

from learning_platform.db import get_connection, run_sql_file


def main() -> None:
    """Run the index file."""
    with get_connection() as conn:
        run_sql_file(conn, "sql/indexes.sql")
    print("Indexes created.")


if __name__ == "__main__":
    main()