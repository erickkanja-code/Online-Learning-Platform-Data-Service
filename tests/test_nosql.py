"""Tests for JSONB quizzes, the Redis progress cache and MongoDB forum threads."""

import fakeredis
import mongomock
import pytest

from learning_platform.cache import (
    cache_key,
    clear_cached_completion,
    get_cached_completion,
)
from learning_platform.forum import create_thread, get_course_threads
from learning_platform.quizzes import add_quiz, get_quiz_questions
from tests.conftest import complete_lessons

QUIZ = {
    "title": "Lesson 1 quiz",
    "questions": [
        {"question": "2 + 2?", "options": ["3", "4"], "answer": "4"},
        {"question": "Capital of France?", "options": ["Paris", "Rome"], "answer": "Paris"},
    ],
}


# --- JSONB quizzes (real test database) ------------------------------------


def test_quiz_questions_are_stored_and_read_back_from_jsonb(conn):
    add_quiz(conn, lesson_id=1, content=QUIZ)

    assert get_quiz_questions(conn, lesson_id=1) == QUIZ["questions"]


def test_lesson_without_quiz_has_no_questions(conn):
    assert get_quiz_questions(conn, lesson_id=2) == []


# --- Redis cache (fake in-memory Redis) ------------------------------------


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis()


def test_first_request_calculates_and_caches(conn, redis_client):
    complete_lessons(conn, student_id=1, lesson_ids=[1])

    assert get_cached_completion(redis_client, conn, student_id=1, course_id=1) == 50.0
    assert float(redis_client.get(cache_key(1, 1))) == 50.0


def test_second_request_comes_from_cache(conn, redis_client):
    get_cached_completion(redis_client, conn, student_id=1, course_id=1)
    complete_lessons(conn, student_id=1, lesson_ids=[1])

    # Still 0.0: the answer came from Redis, not from the updated database.
    assert get_cached_completion(redis_client, conn, student_id=1, course_id=1) == 0.0


def test_clearing_the_cache_gives_a_fresh_value(conn, redis_client):
    get_cached_completion(redis_client, conn, student_id=1, course_id=1)
    complete_lessons(conn, student_id=1, lesson_ids=[1])

    clear_cached_completion(redis_client, student_id=1, course_id=1)

    assert get_cached_completion(redis_client, conn, student_id=1, course_id=1) == 50.0


def test_cached_value_expires(conn, redis_client):
    get_cached_completion(redis_client, conn, student_id=1, course_id=1)

    assert 0 < redis_client.ttl(cache_key(1, 1)) <= 300


# --- MongoDB forum (fake in-memory MongoDB) --------------------------------


@pytest.fixture
def threads():
    return mongomock.MongoClient()["learning_platform"]["forum_threads"]


def test_create_and_list_threads(threads):
    create_thread(threads, course_id=1, student_id=1, title="Help with loops", body="...")
    create_thread(threads, course_id=1, student_id=2, title="Nice course", body="...")

    titles = {thread["title"] for thread in get_course_threads(threads, course_id=1)}

    assert titles == {"Help with loops", "Nice course"}


def test_threads_are_listed_per_course(threads):
    create_thread(threads, course_id=1, student_id=1, title="Course 1 question", body="...")
    create_thread(threads, course_id=2, student_id=1, title="Course 2 question", body="...")

    result = get_course_threads(threads, course_id=2)

    assert len(result) == 1
    assert result[0]["title"] == "Course 2 question"
    assert "_id" not in result[0]