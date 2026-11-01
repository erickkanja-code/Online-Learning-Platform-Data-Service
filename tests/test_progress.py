"""Tests for completing lessons, the dashboard and lesson timing."""

from datetime import datetime, timedelta, timezone

import pytest

from learning_platform.enrollment import enroll_student
from learning_platform.progress import (
    NotEnrolledError,
    complete_lesson,
    get_completion_percentage,
    get_dashboard,
    get_lesson_timing,
)


def count_completions(conn, student_id):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM lesson_completions WHERE student_id = %s",
            (student_id,),
        )
        return cur.fetchone()[0]


def test_complete_lesson_records_progress(conn):
    enroll_student(conn, student_id=1, course_id=1)

    assert complete_lesson(conn, student_id=1, lesson_id=1) is True
    assert get_completion_percentage(conn, student_id=1, course_id=1) == 50.0


def test_completing_a_lesson_twice_keeps_one_row(conn):
    enroll_student(conn, student_id=1, course_id=1)
    complete_lesson(conn, student_id=1, lesson_id=1)

    assert complete_lesson(conn, student_id=1, lesson_id=1) is False
    assert count_completions(conn, student_id=1) == 1


def test_cannot_complete_lesson_without_enrollment(conn):
    with pytest.raises(NotEnrolledError):
        complete_lesson(conn, student_id=1, lesson_id=1)

    assert count_completions(conn, student_id=1) == 0


def test_cannot_complete_lesson_of_another_course(conn):
    enroll_student(conn, student_id=1, course_id=1)

    with pytest.raises(NotEnrolledError):
        complete_lesson(conn, student_id=1, lesson_id=3)


def test_dashboard_shows_progress_per_enrolled_course(conn):
    enroll_student(conn, student_id=1, course_id=1)
    complete_lesson(conn, student_id=1, lesson_id=1)

    assert get_dashboard(conn, student_id=1) == [
        {
            "course_id": 1,
            "title": "Basics",
            "total_lessons": 2,
            "completed_lessons": 1,
            "completion_percentage": 50.0,
        }
    ]


def test_dashboard_with_two_courses(conn):
    enroll_student(conn, student_id=1, course_id=1)
    complete_lesson(conn, student_id=1, lesson_id=1)
    complete_lesson(conn, student_id=1, lesson_id=2)
    enroll_student(conn, student_id=1, course_id=2)

    percentages = [row["completion_percentage"] for row in get_dashboard(conn, 1)]

    assert percentages == [100.0, 0.0]


def test_dashboard_ignores_other_students_progress(conn):
    enroll_student(conn, student_id=1, course_id=1)
    enroll_student(conn, student_id=2, course_id=1)
    complete_lesson(conn, student_id=2, lesson_id=1)

    assert get_dashboard(conn, student_id=1)[0]["completed_lessons"] == 0


def test_dashboard_is_empty_without_enrollments(conn):
    assert get_dashboard(conn, student_id=1) == []


def test_lesson_timing_uses_previous_completion(conn):
    start = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO lesson_completions (lesson_id, student_id, completed_at) "
                "VALUES (1, 1, %s), (2, 1, %s)",
                (start, start + timedelta(hours=5)),
            )

    timing = get_lesson_timing(conn, student_id=1, course_id=1)

    assert [row["lesson_id"] for row in timing] == [1, 2]
    assert timing[0]["time_since_previous"] is None
    assert timing[1]["time_since_previous"] == timedelta(hours=5)
    
from learning_platform.progress import (
    NotEnrolledError,
    complete_lesson,
    get_completion_percentage,
    get_dashboard,
    get_lesson_timing,
    get_recent_activity,
)

def test_recent_activity_is_newest_first_and_limited(conn):
    start = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO lesson_completions (lesson_id, student_id, completed_at) "
                "VALUES (1, 1, %s), (2, 1, %s), (3, 1, %s), (1, 2, %s)",
                (start, start + timedelta(hours=1), start + timedelta(hours=2), start),
            )

    activity = get_recent_activity(conn, student_id=1, limit=2)

    assert [row["lesson_id"] for row in activity] == [3, 2]