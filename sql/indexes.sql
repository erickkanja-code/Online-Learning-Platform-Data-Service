-- Index for the dashboard's recent activity query
-- (measured with scripts/explain_dashboard.py).
--
-- The query finds one student's completions, newest first. The primary key
-- (lesson_id, student_id) starts with lesson_id, so PostgreSQL cannot use it
-- to find rows by student_id alone, and has to scan the whole table.
-- This index is sorted by student, then by completion time, so PostgreSQL
-- can jump straight to one student's rows, already in time order.
CREATE INDEX IF NOT EXISTS idx_lesson_completions_student_time
    ON lesson_completions (student_id, completed_at);

-- Refresh the statistics PostgreSQL uses to choose a plan.
ANALYZE lesson_completions;