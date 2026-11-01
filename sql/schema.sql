-- Online Learning Platform schema (PostgreSQL), in Third Normal Form (3NF).
-- Running this file again drops and recreates every table, so it always
-- starts from a clean, empty database.

DROP TABLE IF EXISTS quizzes, lesson_completions, enrollments, lessons, modules,
    course_prerequisites, courses, students CASCADE;

CREATE TABLE students (
    student_id  SERIAL PRIMARY KEY,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE courses (
    course_id    SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT
);

-- Which courses must be completed before another course can be taken.
-- Example: (course_id = 2, prerequisite_id = 1) means "course 2 requires course 1".
CREATE TABLE course_prerequisites (
    course_id        INT NOT NULL REFERENCES courses (course_id),
    prerequisite_id  INT NOT NULL REFERENCES courses (course_id),
    PRIMARY KEY (course_id, prerequisite_id),
    CHECK (course_id <> prerequisite_id)
);

CREATE TABLE modules (
    module_id  SERIAL PRIMARY KEY,
    course_id  INT NOT NULL REFERENCES courses (course_id),
    title      TEXT NOT NULL,
    position   INT NOT NULL
);

CREATE TABLE lessons (
    lesson_id  SERIAL PRIMARY KEY,
    module_id  INT NOT NULL REFERENCES modules (module_id),
    title      TEXT NOT NULL,
    position   INT NOT NULL
);

CREATE TABLE enrollments (
    enrollment_id  SERIAL PRIMARY KEY,
    student_id     INT NOT NULL REFERENCES students (student_id),
    course_id      INT NOT NULL REFERENCES courses (course_id),
    enrolled_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (student_id, course_id)
);

-- One row each time a student finishes a lesson.
-- The primary key stops the same lesson being completed twice by the same student.
CREATE TABLE lesson_completions (
    lesson_id     INT NOT NULL REFERENCES lessons (lesson_id),
    student_id    INT NOT NULL REFERENCES students (student_id),
    completed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (lesson_id, student_id)
);

-- Quiz content is stored as JSONB because every quiz has a different
-- number of questions and options.
CREATE TABLE quizzes (
    quiz_id    SERIAL PRIMARY KEY,
    lesson_id  INT NOT NULL REFERENCES lessons (lesson_id),
    content    JSONB NOT NULL
);