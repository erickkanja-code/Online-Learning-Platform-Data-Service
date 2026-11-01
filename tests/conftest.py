"""Shared test fixtures: a fresh test database for every test."""

import os
from pathlib import Path

import psycopg2
import pytest

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/learning_platform_test",
)
SCHEMA_FILE = Path(__file__).parent.parent / "sql" / "schema.sql"

# Small, known data for tests:
#   Course 1 "Basics"   -> 1 module -> lessons 1 and 2
#   Course 2 "Advanced" -> 1 module -> lesson 3, and requires course 1
#   Students 1 (Alice) and 2 (Bob)
TEST_DATA = """
INSERT INTO students (full_name, email) VALUES
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com');
INSERT INTO courses (title) VALUES ('Basics'), ('Advanced');
INSERT INTO course_prerequisites (course_id, prerequisite_id) VALUES (2, 1);
INSERT INTO modules (course_id, title, position) VALUES (1, 'Module 1', 1), (2, 'Module 1', 1);
INSERT INTO lessons (module_id, title, position) VALUES
    (1, 'Lesson 1', 1),
    (1, 'Lesson 2', 2),
    (2, 'Lesson 1', 1);
"""


@pytest.fixture
def conn():
    """Give each test a connection to a freshly created test database."""
    connection = psycopg2.connect(TEST_DATABASE_URL)
    with connection:
        with connection.cursor() as cur:
            cur.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
            cur.execute(TEST_DATA)
    yield connection
    connection.close()


def complete_lessons(conn, student_id, lesson_ids):
    """Mark lessons as completed by inserting rows directly (test helper)."""
    with conn:
        with conn.cursor() as cur:
            for lesson_id in lesson_ids:
                cur.execute(
                    "INSERT INTO lesson_completions (lesson_id, student_id) VALUES (%s, %s)",
                    (lesson_id, student_id),
                )


def count_enrollments(conn, student_id, course_id):
    """Return how many enrollment rows exist for this student and course."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM enrollments WHERE student_id = %s AND course_id = %s",
            (student_id, course_id),
        )
        return cur.fetchone()[0]