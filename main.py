"""Demo: run every feature of the learning platform data service.

Run scripts/setup_db.py first, so the database holds the sample data.

Usage:
    poetry run python main.py
"""

from learning_platform.cache import (
    clear_cached_completion,
    get_cached_completion,
    get_redis_client,
)
from learning_platform.db import get_connection
from learning_platform.enrollment import EnrollmentError, enroll_student
from learning_platform.forum import (
    create_thread,
    get_course_threads,
    get_threads_collection,
)
from learning_platform.progress import (
    complete_lesson,
    get_dashboard,
    get_lesson_timing,
    get_recent_activity,
)
from learning_platform.quizzes import add_quiz, get_quiz_questions

ADVANCED_PYTHON = 2
FIRST_ADVANCED_LESSON = 21

SAMPLE_QUIZ = {
    "title": "Variables quiz",
    "questions": [
        {
            "question": "Which keyword defines a function?",
            "options": ["def", "fun"],
            "answer": "def",
        },
        {
            "question": "What does len('abc') return?",
            "options": ["2", "3"],
            "answer": "3",
        },
    ],
}


def show_dashboard(conn, student_id: int) -> None:
    """Print a student's course progress and recent activity."""
    print(f"\n=== Dashboard for student {student_id} ===")
    for course in get_dashboard(conn, student_id):
        print(
            f"  {course['title']}: {course['completed_lessons']}/{course['total_lessons']} "
            f"lessons ({course['completion_percentage']}%)"
        )
    print("  Recent activity:")
    for activity in get_recent_activity(conn, student_id, limit=3):
        print(
            f"    lesson {activity['lesson_id']} at {activity['completed_at']:%Y-%m-%d %H:%M}"
        )


def try_enroll(conn, student_id: int, course_id: int) -> None:
    """Try to enroll a student and print the result."""
    try:
        enrollment_id = enroll_student(conn, student_id, course_id)
        print(
            f"  Student {student_id} enrolled in course {course_id} (enrollment {enrollment_id})"
        )
    except EnrollmentError as error:
        print(f"  Student {student_id} not enrolled: {error}")


def main() -> None:
    """Walk through enrollment, progress, timing, caching, quizzes and the forum."""
    redis_client = get_redis_client()
    threads = get_threads_collection()

    with get_connection() as conn:
        show_dashboard(conn, student_id=20)

        print("\n=== Enrollment (transactional, with prerequisite check) ===")
        try_enroll(conn, student_id=1, course_id=ADVANCED_PYTHON)
        try_enroll(conn, student_id=20, course_id=ADVANCED_PYTHON)
        try_enroll(conn, student_id=20, course_id=ADVANCED_PYTHON)

        print("\n=== Progress tracking with the Redis cache ===")
        recorded = complete_lesson(conn, student_id=20, lesson_id=FIRST_ADVANCED_LESSON)
        print(
            f"  Completed lesson {FIRST_ADVANCED_LESSON}: newly recorded = {recorded}"
        )
        clear_cached_completion(redis_client, student_id=20, course_id=ADVANCED_PYTHON)
        first = get_cached_completion(redis_client, conn, 20, ADVANCED_PYTHON)
        second = get_cached_completion(redis_client, conn, 20, ADVANCED_PYTHON)
        print(f"  From PostgreSQL: {first}%  |  From Redis cache: {second}%")

        print("\n=== Lesson completion timing (LAG) for student 20, course 1 ===")
        for row in get_lesson_timing(conn, student_id=20, course_id=1)[:4]:
            print(
                f"  lesson {row['lesson_id']}: {row['time_since_previous']} since previous"
            )

        print("\n=== Quiz stored as JSONB ===")
        if not get_quiz_questions(conn, lesson_id=1):
            add_quiz(conn, lesson_id=1, content=SAMPLE_QUIZ)
        for question in get_quiz_questions(conn, lesson_id=1):
            print(f"  {question['question']} {question['options']}")

    print("\n=== Forum threads in MongoDB ===")
    create_thread(
        threads,
        course_id=1,
        student_id=20,
        title="Tips for lesson 5?",
        body="Stuck on loops.",
    )
    course_threads = get_course_threads(threads, course_id=1)
    print(
        f"  Course 1 has {len(course_threads)} thread(s). Latest: {course_threads[-1]['title']}"
    )


if __name__ == "__main__":
    main()