-- Migration: Add badge_claimed tracking to assessments table
-- This enables deferred badge claiming (lazy approach)

ALTER TABLE assessments
ADD COLUMN IF NOT EXISTS badge_claimed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS badge_claimed_at TIMESTAMP WITH TIME ZONE;

-- Index for efficient unclaimed badge queries
CREATE INDEX idx_assessments_badge_claimed ON assessments(badge_claimed) WHERE badge_claimed = FALSE;

-- Comments for documentation
COMMENT ON COLUMN assessments.badge_claimed IS 'Tracks whether user has claimed their badge for this assessment';
COMMENT ON COLUMN assessments.badge_claimed_at IS 'Timestamp when badge was claimed';
