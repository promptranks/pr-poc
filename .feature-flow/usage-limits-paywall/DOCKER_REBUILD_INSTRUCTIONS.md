# Docker Rebuild Instructions

## Summary

All implementation complete, tests passing (22/22), and database migration executed successfully. Ready for docker rebuild and GUI testing.

## What Was Done

1. ✅ **Backend Implementation** - Usage limits, paywall enforcement, webhook handlers
2. ✅ **Frontend Implementation** - Locked scores, upgrade modals, usage display
3. ✅ **Security Fix** - Critical ownership verification added
4. ✅ **Tests Fixed** - All 22 tests passing
5. ✅ **Database Migration** - 3 premium users updated with correct limits

## Docker Rebuild Steps

### 1. Rebuild and Restart Containers

```bash
cd /Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc

# Rebuild the containers with new code
docker compose build

# Restart the services
docker compose up -d

# Check logs to verify startup
docker compose logs -f api
```

### 2. Verify Services Are Running

```bash
# Check all containers are healthy
docker compose ps

# Should see:
# - prk-poc-api (healthy)
# - prk-poc-web (healthy)
# - prk-poc-postgres (healthy)
# - prk-poc-redis (healthy)
```

### 3. Test the Implementation

Open your browser and test these scenarios:

#### Test Case 1: Existing Premium User
1. Login as `admin@adamchins.com` (premium user)
2. Go to Dashboard
3. **Expected:** Shows "0/3 Full Assessments" (not 0/0)
4. Start a full assessment
5. **Expected:** Can complete and see all scores
6. Dashboard should show "1/3 Full Assessments"

#### Test Case 2: Free User - First Premium Attempt
1. Create a new free user account
2. Start an assessment with:
   - Mode: Full
   - Select an industry
   - Select a role
3. **Expected:** Assessment starts successfully
4. Complete KBA section
5. **Expected:** See message "✓ Section completed. Upgrade to Premium to view your scores."
6. Complete all sections
7. **Expected:** Final results show upgrade modal instead of scores

#### Test Case 3: Free User - Second Premium Attempt
1. Using the same free user from Test Case 2
2. Try to start another premium assessment
3. **Expected:** Get error "Free trial used. Upgrade to Premium for 3 full assessments per month."
4. **Expected:** Upgrade modal appears

#### Test Case 4: Free User Upgrades
1. Using the same free user (1/1 trial used)
2. Click upgrade and complete Stripe checkout (use test card: 4242 4242 4242 4242)
3. After successful payment, go to Dashboard
4. **Expected:** Shows "1/3 Full Assessments" (usage preserved)
5. Start another full assessment
6. **Expected:** Can start and see all scores
7. Dashboard should show "2/3 Full Assessments"

#### Test Case 5: Industry/Role Paywall
1. Create a new free user
2. Start a quick assessment (not full mode)
3. Select an industry (but no role)
4. **Expected:** Assessment starts with locked results
5. Complete assessment
6. **Expected:** Cannot see scores, upgrade modal shown

## Troubleshooting

### If containers fail to start:

```bash
# Check logs
docker compose logs api
docker compose logs web

# Common issues:
# - Port conflicts: Check if ports 3000, 8000, 5432, 6379 are available
# - Environment variables: Check .env file exists
```

### If database migration didn't apply:

```bash
# Re-run migration manually
docker exec -i prk-poc-postgres psql -U promptranks -d promptranks << 'EOF'
UPDATE user_usage
SET full_assessments_limit = 3, updated_at = NOW()
WHERE user_id IN (SELECT id FROM users WHERE subscription_tier = 'premium')
AND full_assessments_limit != 3
AND period_start >= DATE_TRUNC('month', CURRENT_DATE)::DATE;
EOF
```

### If frontend changes not visible:

```bash
# Clear browser cache or use incognito mode
# Or rebuild web container specifically:
docker compose build web
docker compose up -d web
```

## Expected Behavior Summary

| User Type | Action | Expected Result |
|-----------|--------|----------------|
| Premium (0/3) | Start full assessment | ✅ Allowed, shows scores, becomes 1/3 |
| Premium (3/3) | Start full assessment | ❌ Blocked with "Limit reached" |
| Free (0/1) | Start premium assessment | ✅ Allowed, results locked, becomes 1/1 |
| Free (1/1) | Start premium assessment | ❌ Blocked with "Free trial used" |
| Free → Premium | After upgrade | Usage preserved (1/1 → 1/3) |
| Enterprise | Start any assessment | ✅ Always allowed, unlimited |
| Anonymous | Start premium assessment | ✅ Allowed, results locked |

## API Endpoints Changed

- `POST /assessments/start` - Now checks usage limits
- `POST /assessments/{id}/kba/submit` - Returns locked message if results_locked
- `POST /assessments/{id}/ppa/execute` - Returns locked message if results_locked
- `POST /assessments/{id}/psv/submit` - Returns locked message if results_locked
- `GET /assessments/{id}/results` - Shows paywall if results_locked
- All assessment endpoints now verify ownership

## Security Note

All assessment endpoints now require ownership verification. This prevents:
- Users accessing other users' assessments
- Bypassing paywall by accessing locked results
- Privacy violations

## Next Steps After Testing

1. If all tests pass in GUI, merge the feature branch:
   ```bash
   git checkout main
   git merge feature/usage-limits-paywall
   git push origin main
   ```

2. Create a GitHub PR for code review (optional)

3. Deploy to production when ready

## Support

If you encounter any issues:
- Check logs: `docker compose logs -f`
- Review documentation: `.feature-flow/usage-limits-paywall/FEATURE_DOCUMENTATION.md`
- Review security audit: `.feature-flow/usage-limits-paywall/validation/SECURITY_AUDIT.md`
