-- Migration 004: Add indexes for leaderboard queries
-- These indexes optimize the "best score per user" aggregation
-- and time-filtered leaderboard queries.

-- Composite index for leaderboard queries: full-mode completed assessments with scores
CREATE INDEX IF NOT EXISTS idx_assessments_leaderboard
    ON assessments (user_id, final_score DESC)
    WHERE mode = 'full' AND status = 'completed' AND user_id IS NOT NULL AND final_score IS NOT NULL;

-- Index for time-filtered leaderboard queries
CREATE INDEX IF NOT EXISTS idx_assessments_completed_at_mode
    ON assessments (completed_at DESC)
    WHERE mode = 'full' AND status = 'completed';
