-- Sample data: 4 courses, 4 modules per course, 5 lessons per module,
-- 5,000 students, 10,000 enrollments and about 100,000 lesson completions.
-- Everything is calculated from IDs, so the data is the same on every run.

INSERT INTO courses (title, description) VALUES
    ('Python Basics', 'Variables, loops and functions'),
    ('Advanced Python', 'Generators, decorators and testing'),
    ('SQL Fundamentals', 'Tables, joins and aggregation'),
    ('Data Engineering', 'Pipelines with Python and SQL');

-- Advanced Python requires Python Basics.
-- Data Engineering requires Python Basics and SQL Fundamentals.
INSERT INTO course_prerequisites (course_id, prerequisite_id) VALUES
    (2, 1),
    (4, 1),
    (4, 3);

-- 4 modules for every course.
INSERT INTO modules (course_id, title, position)
SELECT c.course_id, 'Module ' || n, n
FROM courses c
CROSS JOIN generate_series(1, 4) AS n
ORDER BY c.course_id, n;

-- 5 lessons for every module, so every course has 20 lessons.
INSERT INTO lessons (module_id, title, position)
SELECT m.module_id, 'Lesson ' || n, n
FROM modules m
CROSS JOIN generate_series(1, 5) AS n
ORDER BY m.module_id, n;

-- 5,000 students.
INSERT INTO students (full_name, email)
SELECT 'Student ' || n, 'student' || n || '@example.com'
FROM generate_series(1, 5000) AS n;

-- Every student is enrolled in the two courses without prerequisites:
-- Python Basics (1) and SQL Fundamentals (3), starting 60 days ago.
INSERT INTO enrollments (student_id, course_id, enrolled_at)
SELECT s.student_id, c.course_id, now() - interval '60 days'
FROM students s
CROSS JOIN courses c
WHERE c.course_id IN (1, 3);

-- Each student completes the first (student_id % 21) lessons of each course,
-- in order, roughly one per day. So student 1 has done 1 lesson per course,
-- student 10 has done 10, and student 20 has finished both courses (20 lessons).
INSERT INTO lesson_completions (lesson_id, student_id, completed_at)
SELECT l.lesson_id,
       e.student_id,
       e.enrolled_at
           + ((m.position - 1) * 5 + l.position) * interval '1 day'
           + (l.lesson_id * 7 % 24) * interval '1 hour'
FROM enrollments e
JOIN modules m ON m.course_id = e.course_id
JOIN lessons l ON l.module_id = m.module_id
WHERE (m.position - 1) * 5 + l.position <= e.student_id % 21;