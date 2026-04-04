-- Migration: Fix Premium User Usage Limits
-- Date: 2026-04-04
-- Purpose: Update existing premium users with incorrect limits (0 -> 3)

-- Fix existing premium users with incorrect limits
UPDATE user_usage
SET full_assessments_limit = 3,
    updated_at = NOW()
WHERE user_id IN (
    SELECT id FROM users WHERE subscription_tier = 'premium'
)
AND full_assessments_limit != 3
AND period_start >= DATE_TRUNC('month', CURRENT_DATE)::DATE;

-- Verify results
SELECT u.email, u.subscription_tier, uu.full_assessments_used, uu.full_assessments_limit
FROM user_usage uu
JOIN users u ON u.id = uu.user_id
WHERE u.subscription_tier = 'premium'
AND uu.period_start >= DATE_TRUNC('month', CURRENT_DATE)::DATE;
