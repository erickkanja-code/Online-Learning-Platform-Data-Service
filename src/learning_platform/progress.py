"""Progress tracking: completing lessons, completion percentages and timing."""

# The student dashboard: completion percentage for every course the student is
# enrolled in. Uses GROUP BY (one result row per course) and a subquery (to
# find the student's enrolled courses). Stored as a constant so the
# EXPLAIN ANALYZE script in Step 7 can reuse exactly the same query.
DASHBOARD_QUERY = """
    SELECT c.course_id,
           c.title,
           COUNT(l.lesson_id) AS total_lessons,
           COUNT(lc.lesson_id) AS completed_lessons,
           ROUND(COUNT(lc.lesson_id) * 100.0 / COUNT(l.lesson_id), 2) AS completion_percentage
    FROM courses c
    JOIN modules m ON m.course_id = c.course_id
    JOIN lessons l ON l.module_id = m.module_id
    LEFT JOIN lesson_completions lc
           ON lc.lesson_id = l.lesson_id AND lc.student_id = %(student_id)s
    WHERE c.course_id IN (
        SELECT course_id FROM enrollments WHERE student_id = %(student_id)s
    )
    GROUP BY c.course_id, c.title
    ORDER BY c.course_id
"""
# The dashboard's "recent activity" panel: the student's latest completed
# lessons, newest first. Step 7 measures this query with EXPLAIN ANALYZE and
# speeds it up with an index (see sql/indexes.sql).
RECENT_ACTIVITY_QUERY = """
    SELECT lesson_id, completed_at
    FROM lesson_completions
    WHERE student_id = %(student_id)s
    ORDER BY completed_at DESC
    LIMIT %(limit)s
"""

class NotEnrolledError(Exception):
    """Raised when a student tries to complete a lesson of a course they are not in."""

    def __init__(self, student_id: int, lesson_id: int) -> None:
        """Create the error for the given student and lesson."""
        super().__init__(
            f"Student {student_id} is not enrolled in the course of lesson {lesson_id}"
        )


def complete_lesson(conn, student_id: int, lesson_id: int) -> bool:
    """Record that a student finished a lesson.

    Returns True if the completion was recorded, or False if the student had
    already completed this lesson (the original completion time is kept).

    Raises:
        NotEnrolledError: If the student is not enrolled in the lesson's course.
    """
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM lessons l
                JOIN modules m ON m.module_id = l.module_id
                JOIN enrollments e ON e.course_id = m.course_id
                WHERE l.lesson_id = %s AND e.student_id = %s
                """,
                (lesson_id, student_id),
            )
            if cur.fetchone() is None:
                raise NotEnrolledError(student_id, lesson_id)

            cur.execute(
                """
                INSERT INTO lesson_completions (lesson_id, student_id)
                VALUES (%s, %s)
                ON CONFLICT (lesson_id, student_id) DO NOTHING
                """,
                (lesson_id, student_id),
            )
            return cur.rowcount == 1


def get_completion_percentage(conn, student_id: int, course_id: int) -> float:
    """Return the percentage (0 to 100) of a course's lessons the student has completed."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(
                ROUND(COUNT(lc.lesson_id) * 100.0 / NULLIF(COUNT(l.lesson_id), 0), 2),
                0
            )
            FROM modules m
            JOIN lessons l ON l.module_id = m.module_id
            LEFT JOIN lesson_completions lc
                   ON lc.lesson_id = l.lesson_id AND lc.student_id = %s
            WHERE m.course_id = %s
            """,
            (student_id, course_id),
        )
        return float(cur.fetchone()[0])


def get_dashboard(conn, student_id: int) -> list[dict]:
    """Return progress for every course the student is enrolled in."""
    with conn.cursor() as cur:
        cur.execute(DASHBOARD_QUERY, {"student_id": student_id})
        rows = cur.fetchall()

    return [
        {
            "course_id": course_id,
            "title": title,
            "total_lessons": total,
            "completed_lessons": completed,
            "completion_percentage": float(percentage),
        }
        for course_id, title, total, completed, percentage in rows
    ]


def get_lesson_timing(conn, student_id: int, course_id: int) -> list[dict]:
    """Return each completed lesson with the time since the previous completion.

    Uses the LAG() window function to look at the previous row. The first
    completion has no previous one, so its time_since_previous is None.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT l.lesson_id,
                   lc.completed_at,
                   lc.completed_at - LAG(lc.completed_at) OVER (ORDER BY lc.completed_at)
                       AS time_since_previous
            FROM lesson_completions lc
            JOIN lessons l ON l.lesson_id = lc.lesson_id
            JOIN modules m ON m.module_id = l.module_id
            WHERE lc.student_id = %s AND m.course_id = %s
            ORDER BY lc.completed_at
            """,
            (student_id, course_id),
        )
        rows = cur.fetchall()

    return [
        {
            "lesson_id": lesson_id,
            "completed_at": completed_at,
            "time_since_previous": time_since_previous,
        }
        for lesson_id, completed_at, time_since_previous in rows
    ]

def get_recent_activity(conn, student_id: int, limit: int = 5) -> list[dict]:
    """Return the student's most recently completed lessons, newest first."""
    with conn.cursor() as cur:
        cur.execute(RECENT_ACTIVITY_QUERY, {"student_id": student_id, "limit": limit})
        rows = cur.fetchall()

    return [
        {"lesson_id": lesson_id, "completed_at": completed_at}
        for lesson_id, completed_at in rows
    ]

    
