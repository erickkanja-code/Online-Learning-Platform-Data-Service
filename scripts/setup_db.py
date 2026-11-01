"""Create the tables and load the sample data.

Usage:
    poetry run python scripts/setup_db.py
"""

from learning_platform.db import get_connection, run_sql_file


def main() -> None:
    """Run the schema file, then the seed file."""
    with get_connection() as conn:
        run_sql_file(conn, "sql/schema.sql")
        run_sql_file(conn, "sql/seed.sql")
    print("Database created and seeded.")


if __name__ == "__main__":
    main()