# Test Execution Guide: Usage Limits & Paywall

**Purpose:** Step-by-step guide to execute tests once environment is fixed.

---

## Prerequisites

### 1. Fix Environment Issue

The current pip environment has a timeout issue. To resolve:

```bash
# Option 1: Use a different Python environment
cd /Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Option 2: Fix conda environment
conda install pip
pip install -r requirements.txt

# Option 3: Install stripe directly
pip install stripe==11.1.0
```

### 2. Verify Installation

```bash
python -c "import stripe; print('Stripe installed successfully')"
python -c "import pytest; print('Pytest installed successfully')"
```

---

## Test Execution Commands

### Run All New Tests

```bash
cd /Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api

# Run usage limits tests
pytest tests/test_usage_limits.py -v

# Run updated payment tests
pytest tests/test_payments.py -v

# Run all tests
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only (UsageService)
pytest tests/test_usage_limits.py -v -k "test_get_tier_limit or test_check_limit or test_increment"

# Integration tests only (Assessment flow)
pytest tests/test_usage_limits.py -v -k "test_free_user or test_premium_user or test_anonymous"

# Webhook tests only
pytest tests/test_payments.py -v -k "test_webhook"

# Paywall tests only
pytest tests/test_usage_limits.py -v -k "paywall or locked"
```

### Run with Coverage

```bash
# Coverage for all tests
pytest --cov=app --cov-report=html --cov-report=term tests/

# Coverage for specific modules
pytest --cov=app.services.usage_service --cov=app.services.stripe_service tests/

# View HTML coverage report
open htmlcov/index.html
```

### Run with Detailed Output

```bash
# Show print statements
pytest tests/test_usage_limits.py -v -s

# Show full diff on failures
pytest tests/test_usage_limits.py -v --tb=long

# Stop on first failure
pytest tests/test_usage_limits.py -v -x
```

---

## Expected Test Results

### All Tests Should Pass

```
tests/test_usage_limits.py::test_get_tier_limit_all_tiers PASSED
tests/test_usage_limits.py::test_get_or_create_usage_creates_new_record PASSED
tests/test_usage_limits.py::test_get_or_create_usage_syncs_limit PASSED
tests/test_usage_limits.py::test_check_limit_free_user_no_usage PASSED
tests/test_usage_limits.py::test_check_limit_free_user_trial_used PASSED
tests/test_usage_limits.py::test_check_limit_premium_user_under_limit PASSED
tests/test_usage_limits.py::test_check_limit_premium_user_at_limit PASSED
tests/test_usage_limits.py::test_check_limit_enterprise_user_unlimited PASSED
tests/test_usage_limits.py::test_increment_usage_increments_counter PASSED
tests/test_usage_limits.py::test_free_user_first_premium_attempt_allowed PASSED
tests/test_usage_limits.py::test_free_user_second_premium_attempt_blocked PASSED
tests/test_usage_limits.py::test_premium_user_can_start_full_assessment PASSED
tests/test_usage_limits.py::test_premium_user_at_limit_blocked PASSED
tests/test_usage_limits.py::test_anonymous_user_premium_features_locked PASSED
tests/test_usage_limits.py::test_results_locked_hides_kba_scores PASSED
tests/test_usage_limits.py::test_industry_selection_triggers_paywall PASSED
tests/test_usage_limits.py::test_role_selection_triggers_paywall PASSED
tests/test_usage_limits.py::test_monthly_reset_creates_new_usage_record PASSED
tests/test_usage_limits.py::test_upgrade_preserves_usage_count PASSED
tests/test_usage_limits.py::test_fresh_premium_user_gets_full_quota PASSED
tests/test_usage_limits.py::test_assessment_expiry_no_refund PASSED
tests/test_usage_limits.py::test_enterprise_user_no_limits PASSED

tests/test_payments.py::test_webhook_upgrade_preserves_usage PASSED
tests/test_payments.py::test_webhook_fresh_premium_user PASSED

======================== 24 passed in X.XXs ========================
```

### Expected Coverage

Target coverage for modified files:
- `app/services/usage_service.py`: > 90%
- `app/services/stripe_service.py`: > 85%
- `app/routers/assessment.py`: > 80%

---

## Troubleshooting

### Test Failures

If tests fail, check:

1. **Database state:** Tests use in-memory SQLite, should be clean
2. **Fixtures:** Ensure `test_user` and `seeded_db` fixtures work
3. **Imports:** Verify all modules import correctly
4. **Environment:** Check `.env` file has required variables

### Common Issues

**Issue: "No module named 'stripe'"**
```bash
pip install stripe==11.1.0
```

**Issue: "Assessment not found"**
- Check that `seeded_db` fixture is used
- Verify database is seeded with questions

**Issue: "Invalid assessment ID"**
- Ensure UUID conversion works correctly
- Check assessment creation in test

**Issue: "HTTPException not raised"**
- Verify test expectations match implementation
- Check status codes (402 vs 403)

---

## Manual Verification

If automated tests still cannot run, perform manual verification:

### Test Case 1: Premium User
```bash
# 1. Create premium user in database
# 2. Login and navigate to dashboard
# 3. Verify shows "0/3 Full Assessments"
# 4. Start full assessment
# 5. Verify shows "1/3 Full Assessments"
# 6. Complete assessment
# 7. Verify all scores visible
```

### Test Case 2: Free User First Attempt
```bash
# 1. Create free user account
# 2. Start full assessment with industry/role
# 3. Verify assessment starts successfully
# 4. Complete KBA section
# 5. Verify message: "Upgrade to Premium to view scores"
# 6. Complete PPA section
# 7. Verify message: "Upgrade to Premium to view results"
# 8. View final results
# 9. Verify upgrade modal shown
```

### Test Case 3: Free User Second Attempt
```bash
# 1. Use free user from Test Case 2 (1/1 used)
# 2. Try to start another full assessment
# 3. Verify 402 error with upgrade prompt
# 4. Verify cannot start assessment
```

### Test Case 4: Upgrade Flow
```bash
# 1. Use free user with 1/1 used
# 2. Click "Upgrade to Premium"
# 3. Complete Stripe checkout (test mode)
# 4. Verify redirected to dashboard
# 5. Verify shows "1/3 Full Assessments"
# 6. Start another full assessment
# 7. Verify shows "2/3 Full Assessments"
# 8. Complete assessment
# 9. Verify all scores visible
```

---

## Database Migration

Before running tests in staging/production, run the migration:

```bash
# Connect to database
psql -h <host> -U <user> -d <database>

# Run migration
\i /Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/migrations/fix_premium_usage_limits.sql

# Verify results
SELECT u.email, u.subscription_tier, uu.full_assessments_used, uu.full_assessments_limit
FROM users u
LEFT JOIN user_usage uu ON u.id = uu.user_id
WHERE u.subscription_tier = 'premium'
ORDER BY u.created_at DESC
LIMIT 10;
```

Expected output:
```
email                    | subscription_tier | used | limit
-------------------------|-------------------|------|------
admin@adamchins.com      | premium          | 0    | 3
premium-user@test.com    | premium          | 1    | 3
```

---

## Continuous Integration

Add to CI/CD pipeline:

```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd apps/api
          pytest tests/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./apps/api/coverage.xml
```

---

## Success Criteria

Tests are considered successful when:

- ✅ All 27 tests pass
- ✅ Coverage > 80% for modified files
- ✅ No regressions in existing tests
- ✅ Manual verification confirms all 8 test cases work
- ✅ Database migration runs successfully

---

## Next Steps After Tests Pass

1. **Code Review:** Review test coverage and implementation
2. **Staging Deployment:** Deploy to staging environment
3. **Manual Testing:** Perform full manual verification on staging
4. **Performance Testing:** Verify no performance degradation
5. **Production Deployment:** Deploy to production with monitoring
6. **Monitor Metrics:** Track conversion rates, error rates, usage patterns

---

## Contact

If tests fail or issues arise:
- Review QUALITY_REPORT.md for implementation details
- Check BACKEND_IMPLEMENTATION_SUMMARY.md for code locations
- Review FEATURE_PRD.md for requirements
- Check logs for detailed error messages

---

**Last Updated:** 2026-04-04
