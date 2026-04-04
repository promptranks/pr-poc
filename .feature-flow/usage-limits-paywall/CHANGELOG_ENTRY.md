# Changelog Entry: Usage Limits and Paywall

## [Unreleased]

### Added
- **Usage Limits:** Free users get 1 trial attempt for premium features (industry/role selection, full assessments)
- **Paywall Enforcement:** Results locked for free users using premium features
- **Webhook Handlers:** Added handlers for `invoice.payment_failed`, `invoice.payment_succeeded`, `customer.subscription.updated`
- **Usage Display:** Free users now see their trial usage (X/1) in dashboard and usage badge
- **Database Migration:** SQL script to fix existing premium users with incorrect limits

### Fixed
- **Critical Bug:** Premium users showing 0/0 assessments instead of 0/3
- **Critical Security:** Added assessment ownership verification to prevent unauthorized access
- **Usage Sync:** Usage limits now always sync with current subscription tier
- **Upgrade Flow:** Usage count preserved when upgrading from free to premium (1/1 → 1/3)

### Changed
- **Assessment Start:** Now checks for premium features (industry/role/full mode) and enforces limits
- **Section Endpoints:** KBA, PPA, PSV endpoints check `results_locked` before returning scores
- **Error Responses:** Free users hitting trial limit receive 402 error with upgrade prompt
- **Frontend:** Shows completion messages instead of scores when results are locked

### Security
- **CRITICAL FIX:** All assessment endpoints now verify ownership (prevents unauthorized access)
- **Authorization:** User-owned assessments require authentication and ownership match
- **Privacy:** Users can no longer access other users' assessments by knowing the UUID

## Migration Required

Run the database migration to fix existing premium users:
```bash
psql $DATABASE_URL -f apps/api/migrations/fix_premium_usage_limits.sql
```

## Breaking Changes

- Free users are now limited to 1 premium trial (previously unlimited with locked results)
- Assessment endpoints require ownership verification (anonymous assessments still work)
- 402 error response format changed to include `upgrade_required` flag

## Upgrade Notes

1. Deploy backend first (includes database migration)
2. Deploy frontend (handles new error responses)
3. Monitor webhook processing for any issues
4. Check usage tracking metrics in first 24 hours
