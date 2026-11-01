"""Tests for transactional enrollment."""

import pytest

from learning_platform.enrollment import (
    AlreadyEnrolledError,
    PrerequisiteNotMetError,
    enroll_student,
    find_missing_prerequisites,
)
from learning_platform.progress import get_completion_percentage
from tests.conftest import complete_lessons, count_enrollments


def test_enroll_in_course_without_prerequisites(conn):
    enrollment_id = enroll_student(conn, student_id=1, course_id=1)

    assert enrollment_id == 1
    assert count_enrollments(conn, 1, 1) == 1


def test_enrolling_twice_raises_and_keeps_one_row(conn):
    enroll_student(conn, student_id=1, course_id=1)

    with pytest.raises(AlreadyEnrolledError):
        enroll_student(conn, student_id=1, course_id=1)

    assert count_enrollments(conn, 1, 1) == 1


def test_missing_prerequisite_blocks_enrollment_and_saves_nothing(conn):
    with pytest.raises(PrerequisiteNotMetError) as exc_info:
        enroll_student(conn, student_id=1, course_id=2)

    assert exc_info.value.missing == [1]
    assert count_enrollments(conn, 1, 2) == 0


def test_partly_completed_prerequisite_is_not_enough(conn):
    complete_lessons(conn, student_id=1, lesson_ids=[1])

    with pytest.raises(PrerequisiteNotMetError):
        enroll_student(conn, student_id=1, course_id=2)


def test_completed_prerequisite_allows_enrollment(conn):
    complete_lessons(conn, student_id=1, lesson_ids=[1, 2])

    enroll_student(conn, student_id=1, course_id=2)

    assert count_enrollments(conn, 1, 2) == 1


def test_another_students_progress_does_not_count(conn):
    complete_lessons(conn, student_id=2, lesson_ids=[1, 2])

    assert find_missing_prerequisites(conn, student_id=1, course_id=2) == [1]


def test_connection_still_works_after_a_failed_enrollment(conn):
    with pytest.raises(PrerequisiteNotMetError):
        enroll_student(conn, student_id=1, course_id=2)

    enroll_student(conn, student_id=1, course_id=1)

    assert count_enrollments(conn, 1, 1) == 1


@pytest.mark.parametrize(
    ("lesson_ids", "expected"), [([], 0.0), ([1], 50.0), ([1, 2], 100.0)]
)
def test_completion_percentage(conn, lesson_ids, expected):
    complete_lessons(conn, student_id=1, lesson_ids=lesson_ids)

    assert get_completion_percentage(conn, student_id=1, course_id=1) == expected