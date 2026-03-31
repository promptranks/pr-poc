-- Migration 001: Add content tier, subscription, and taxonomy fields
-- Applied to existing databases where init.sql has already run.
-- Safe to re-run (uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).
-- Date: 2026-03-26

-- Content Packs table (new)
CREATE TABLE IF NOT EXISTS content_packs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    tier_required VARCHAR(50) NOT NULL DEFAULT 'free'
        CHECK (tier_required IN ('free', 'pro', 'enterprise')),
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    published_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Industries table (new)
CREATE TABLE IF NOT EXISTS industries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    parent_id UUID REFERENCES industries(id),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_industries_parent ON industries(parent_id);

-- Roles table (new)
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    industry_id UUID REFERENCES industries(id),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, industry_id)
);
CREATE INDEX IF NOT EXISTS idx_roles_industry ON roles(industry_id);

-- Users: add subscription fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'free'
    CHECK (subscription_tier IN ('free', 'pro', 'enterprise'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- Questions: add content tier fields
ALTER TABLE questions ADD COLUMN IF NOT EXISTS content_tier VARCHAR(20) NOT NULL DEFAULT 'core';
ALTER TABLE questions ADD COLUMN IF NOT EXISTS content_pack_id UUID REFERENCES content_packs(id);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS source VARCHAR(20) NOT NULL DEFAULT 'seed';
ALTER TABLE questions ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS correct_count INTEGER DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_questions_content_tier ON questions(content_tier);
CREATE INDEX IF NOT EXISTS idx_questions_content_pack ON questions(content_pack_id);

-- Tasks: add content tier fields
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS content_tier VARCHAR(20) NOT NULL DEFAULT 'core';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS content_pack_id UUID REFERENCES content_packs(id);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source VARCHAR(20) NOT NULL DEFAULT 'seed';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS avg_score DOUBLE PRECISION;
CREATE INDEX IF NOT EXISTS idx_tasks_content_tier ON tasks(content_tier);
CREATE INDEX IF NOT EXISTS idx_tasks_content_pack ON tasks(content_pack_id);

-- Assessments: add industry/role FKs
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS industry_id UUID REFERENCES industries(id);
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS role_id UUID REFERENCES roles(id);

-- Badges: add issuer_domain
ALTER TABLE badges ADD COLUMN IF NOT EXISTS issuer_domain VARCHAR(255);
