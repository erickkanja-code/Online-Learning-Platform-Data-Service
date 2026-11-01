"""Forum discussion threads stored in MongoDB."""

import os
from datetime import datetime, timezone

from pymongo import MongoClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")


def get_threads_collection():
    """Return the MongoDB collection that holds forum threads."""
    client = MongoClient(MONGO_URL)
    return client["learning_platform"]["forum_threads"]


def create_thread(collection, course_id: int, student_id: int, title: str, body: str) -> str:
    """Start a new discussion thread in a course's forum and return its ID."""
    result = collection.insert_one(
        {
            "course_id": course_id,
            "student_id": student_id,
            "title": title,
            "body": body,
            "created_at": datetime.now(timezone.utc),
        }
    )
    return str(result.inserted_id)


def get_course_threads(collection, course_id: int) -> list[dict]:
    """Return every thread in a course's forum, oldest first."""
    threads = collection.find({"course_id": course_id}, {"_id": 0})
    return list(threads.sort("created_at", 1))