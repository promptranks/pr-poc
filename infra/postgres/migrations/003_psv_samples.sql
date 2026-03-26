-- Migration 003: Replace psv_criteria with psv_samples
-- PSV now tests meta-cognition: user evaluates pre-scored samples,
-- system compares user's level rating against ground truth.
-- Safe to re-run (uses IF NOT EXISTS / IF EXISTS).
-- Date: 2026-03-26

-- Drop old psv_criteria table (admin-only, no user data)
DROP TABLE IF EXISTS psv_criteria;

-- PSV Samples: pre-scored prompt+output pairs for user evaluation
CREATE TABLE IF NOT EXISTS psv_samples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    pillar CHAR(1) NOT NULL CHECK (pillar IN ('P', 'E', 'C', 'M', 'A')),
    difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 3),
    task_context TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    ground_truth_level INTEGER NOT NULL CHECK (ground_truth_level BETWEEN 1 AND 5),
    ground_truth_rationale TEXT,
    content_tier VARCHAR(20) NOT NULL DEFAULT 'core'
        CHECK (content_tier IN ('core', 'premium', 'enterprise', 'local')),
    content_pack_id UUID REFERENCES content_packs(id),
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_psv_samples_pillar ON psv_samples(pillar);
CREATE INDEX IF NOT EXISTS idx_psv_samples_active ON psv_samples(is_active);
