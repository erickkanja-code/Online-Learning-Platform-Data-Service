"""Progress tracking: how far each student is through their courses."""


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