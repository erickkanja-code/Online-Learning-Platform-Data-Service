"""Show how PostgreSQL runs the dashboard's recent activity query, with real timings.

Usage:
    poetry run python scripts/explain_dashboard.py
"""

from learning_platform.db import get_connection
from learning_platform.progress import RECENT_ACTIVITY_QUERY

STUDENT_ID = 20


def main() -> None:
    """Run EXPLAIN ANALYZE on the recent activity query and print the plan."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "EXPLAIN ANALYZE " + RECENT_ACTIVITY_QUERY,
                {"student_id": STUDENT_ID, "limit": 5},
            )
            for (line,) in cur.fetchall():
                print(line)


if __name__ == "__main__":
    main()