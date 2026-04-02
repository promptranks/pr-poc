-- Migration: Fix subscription tier constraint to use 'premium' instead of 'pro'
-- Date: 2026-04-02
-- Description: The codebase uses 'premium' but the database constraint only allowed 'pro'

-- Update existing 'pro' users to 'premium'
UPDATE users SET subscription_tier = 'premium' WHERE subscription_tier = 'pro';

-- Drop old constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_subscription_tier_check;

-- Add new constraint with 'premium' instead of 'pro'
ALTER TABLE users ADD CONSTRAINT users_subscription_tier_check
  CHECK (subscription_tier IN ('free', 'premium', 'enterprise'));
