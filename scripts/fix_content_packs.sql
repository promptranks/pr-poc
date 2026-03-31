-- Fix Content Packs - Remove duplicates and update existing
-- Date: 2026-03-28

-- First, delete the duplicate core-kba that was just inserted
DELETE FROM content_packs WHERE slug = 'core-kba' AND id <> 'b985b3b9-43ce-4ca3-843a-c1545dc32664';

-- Update the existing pack1 to be Core KBA
UPDATE content_packs
SET
  name = 'Core KBA',
  slug = 'core-kba',
  description = 'Foundational knowledge-based assessment questions covering all 5 PECAM pillars',
  tier_required = 'free',
  version = '1.0.0',
  published_at = NOW(),
  updated_at = NOW()
WHERE id = 'b985b3b9-43ce-4ca3-843a-c1545dc32664';

-- Verify
SELECT id, name, slug, tier_required, is_active FROM content_packs ORDER BY tier_required, name;
