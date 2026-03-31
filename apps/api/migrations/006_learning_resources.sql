-- Migration: Create learning_resources table
-- Created: 2026-03-29

CREATE TABLE learning_resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  url TEXT NOT NULL,
  pillar VARCHAR(1),
  min_level INT,
  max_level INT,
  resource_type VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learning_resources_pillar ON learning_resources(pillar);
CREATE INDEX idx_learning_resources_level ON learning_resources(min_level, max_level);
