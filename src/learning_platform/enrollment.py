"""Transactional course enrollment with a prerequisite check."""

from psycopg2.errors import UniqueViolation

from learning_platform.progress import get_completion_percentage


class EnrollmentError(Exception):
    """Base class for all enrollment errors."""


class AlreadyEnrolledError(EnrollmentError):
    """Raised when the student is already enrolled in the course."""

    def __init__(self, student_id: int, course_id: int) -> None:
        """Create the error for the given student and course."""
        super().__init__(f"Student {student_id} is already enrolled in course {course_id}")


class PrerequisiteNotMetError(EnrollmentError):
    """Raised when the student has not completed every prerequisite course."""

    def __init__(self, course_id: int, missing: list[int]) -> None:
        """Create the error, listing the prerequisite courses not yet completed."""
        super().__init__(f"Course {course_id} requires completing courses {missing}")
        self.missing = missing


def find_missing_prerequisites(conn, student_id: int, course_id: int) -> list[int]:
    """Return the IDs of prerequisite courses the student has not fully completed."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT prerequisite_id FROM course_prerequisites "
            "WHERE course_id = %s ORDER BY prerequisite_id",
            (course_id,),
        )
        prerequisite_ids = [row[0] for row in cur.fetchall()]

    missing = []
    for prerequisite_id in prerequisite_ids:
        if get_completion_percentage(conn, student_id, prerequisite_id) < 100:
            missing.append(prerequisite_id)
    return missing


def enroll_student(conn, student_id: int, course_id: int) -> int:
    """Enroll a student in a course and return the new enrollment ID.

    The prerequisite check and the insert run in one transaction: if anything
    fails, the whole transaction is rolled back and nothing is saved.

    Raises:
        PrerequisiteNotMetError: If a prerequisite course is not completed.
        AlreadyEnrolledError: If the student is already enrolled in the course.
    """
    with conn:
        missing = find_missing_prerequisites(conn, student_id, course_id)
        if missing:
            raise PrerequisiteNotMetError(course_id, missing)

        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO enrollments (student_id, course_id) "
                    "VALUES (%s, %s) RETURNING enrollment_id",
                    (student_id, course_id),
                )
            except UniqueViolation:
                raise AlreadyEnrolledError(student_id, course_id)
            return cur.fetchone()[0]