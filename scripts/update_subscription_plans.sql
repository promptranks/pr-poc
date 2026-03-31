-- Update Subscription Plans for PromptRanks v1
-- Date: 2026-03-28

-- Delete old plans
DELETE FROM subscription_plans;

-- Insert new plans
INSERT INTO subscription_plans (id, name, tier, price_cents, billing_period, content_packs, features, max_assessments_per_month, is_active, created_at)
VALUES
  -- Free tier
  (
    gen_random_uuid(),
    'Free',
    'free',
    0,
    'monthly',
    '["core-kba", "core-ppa-quick"]'::jsonb,
    '["Unlimited quick assessments", "Basic badge", "Public leaderboard"]'::jsonb,
    0,
    true,
    NOW()
  ),

  -- Premium Monthly
  (
    gen_random_uuid(),
    'Premium Monthly',
    'premium',
    1900,
    'monthly',
    '["core-kba", "core-ppa-full", "core-psv", "industry-targeting"]'::jsonb,
    '["3 full assessments per month", "Industry & role targeting", "Full results & analytics", "Assessment history", "Skill gap analysis", "Priority support"]'::jsonb,
    3,
    true,
    NOW()
  ),

  -- Premium Annual
  (
    gen_random_uuid(),
    'Premium Annual',
    'premium',
    19000,
    'yearly',
    '["core-kba", "core-ppa-full", "core-psv", "industry-targeting"]'::jsonb,
    '["3 full assessments per month", "Industry & role targeting", "Full results & analytics", "Assessment history", "Skill gap analysis", "Priority support", "Save $38/year"]'::jsonb,
    3,
    true,
    NOW()
  ),

  -- Enterprise (custom pricing)
  (
    gen_random_uuid(),
    'Enterprise',
    'enterprise',
    0,
    'custom',
    '["everything"]'::jsonb,
    '["Unlimited full assessments", "Team management", "API access", "Custom branding", "Advanced analytics", "Dedicated support", "Custom content packs", "SSO integration"]'::jsonb,
    NULL,
    true,
    NOW()
  );

-- Verify
SELECT id, name, tier, price_cents, billing_period, max_assessments_per_month, is_active FROM subscription_plans ORDER BY price_cents;
