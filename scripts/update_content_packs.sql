-- Update Content Packs for PromptRanks v1
-- Date: 2026-03-28

-- Delete old content pack
DELETE FROM content_packs;

-- Insert new content packs
INSERT INTO content_packs (id, name, slug, description, tier_required, version, published_at, is_active, created_at)
VALUES
  (
    gen_random_uuid(),
    'Core KBA',
    'core-kba',
    'Foundational knowledge-based assessment questions covering all 5 PECAM pillars',
    'free',
    '1.0.0',
    NOW(),
    true,
    NOW()
  ),
  (
    gen_random_uuid(),
    'Core PPA Quick',
    'core-ppa-quick',
    'Single multi-pillar practical task for quick assessment',
    'free',
    '1.0.0',
    NOW(),
    true,
    NOW()
  ),
  (
    gen_random_uuid(),
    'Core PPA Full',
    'core-ppa-full',
    'Comprehensive practical tasks covering all PECAM pillars',
    'premium',
    '1.0.0',
    NOW(),
    true,
    NOW()
  ),
  (
    gen_random_uuid(),
    'Core PSV',
    'core-psv',
    'Portfolio submission and validation for full assessments',
    'premium',
    '1.0.0',
    NOW(),
    true,
    NOW()
  ),
  (
    gen_random_uuid(),
    'Industry Targeting',
    'industry-targeting',
    'Industry and role-specific question contextualization',
    'premium',
    '1.0.0',
    NULL,
    false,
    NOW()
  );

-- Verify
SELECT id, name, slug, tier_required, is_active FROM content_packs ORDER BY tier_required, name;
