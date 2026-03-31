-- Migration: Create pending_assessments table for database-backed state management
-- This replaces sessionStorage with persistent database state

CREATE TABLE IF NOT EXISTS pending_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('quick', 'full')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'abandoned')),
    assessment_id UUID REFERENCES assessments(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '24 hours',

    CONSTRAINT unique_session_id UNIQUE(session_id)
);

-- Indexes for efficient queries
CREATE INDEX idx_pending_assessments_user_id ON pending_assessments(user_id);
CREATE INDEX idx_pending_assessments_session_id ON pending_assessments(session_id);
CREATE INDEX idx_pending_assessments_expires_at ON pending_assessments(expires_at);
CREATE INDEX idx_pending_assessments_status ON pending_assessments(status);

-- Comments for documentation
COMMENT ON TABLE pending_assessments IS 'Stores pending assessment state for both authenticated and anonymous users';
COMMENT ON COLUMN pending_assessments.session_id IS 'Unique session identifier for anonymous users, stored in localStorage';
COMMENT ON COLUMN pending_assessments.user_id IS 'Optional user ID for authenticated users';
COMMENT ON COLUMN pending_assessments.expires_at IS 'Automatic expiration after 24 hours for cleanup';
