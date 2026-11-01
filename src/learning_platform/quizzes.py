"""Quizzes stored as JSONB in PostgreSQL."""

from psycopg2.extras import Json


def add_quiz(conn, lesson_id: int, content: dict) -> int:
    """Save a quiz for a lesson and return the new quiz ID.

    content is a normal Python dictionary, for example:
        {"title": "Variables quiz",
         "questions": [{"question": "...", "options": ["..."], "answer": "..."}]}
    """
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO quizzes (lesson_id, content) VALUES (%s, %s) RETURNING quiz_id",
                (lesson_id, Json(content)),
            )
            return cur.fetchone()[0]


def get_quiz_questions(conn, lesson_id: int) -> list[dict]:
    """Return the questions of a lesson's quiz, or an empty list if it has none.

    The -> operator reads one key out of the JSONB document inside PostgreSQL.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT content -> 'questions' FROM quizzes WHERE lesson_id = %s",
            (lesson_id,),
        )
        row = cur.fetchone()
    if row is None:
        return []
    return row[0]