# Testing Guide - Latest Fixes (2026-03-31)

## What Was Fixed

### Issue 1: Results Page Authentication ✅
**Problem:** After completing an assessment while logged in, the page still asked users to register/sign-in to claim the badge.

**Fix:**
- Results page now checks `AuthContext` for authentication status
- If user is authenticated, badge is auto-claimed immediately
- Only unauthenticated users see the register/sign-in form
- After claim, authenticated users see CTAs: "View Badge", "View Leaderboard" (full only), "Back to Dashboard"

**Files Changed:**
- `apps/web/src/pages/Results.tsx`

---

### Issue 2: Post-Payment Assessment Resume ✅
**Problem:** After successful payment, user was redirected to dashboard instead of continuing their selected assessment.

**Fix:**
- Stripe success_url changed from `/dashboard?session_id=...` to `/?checkout=success&session_id=...`
- Landing page now detects checkout return and shows success message
- Pending assessment context (industry/role/mode) is preserved in sessionStorage
- After tier update is detected, system automatically resumes the exact assessment user selected

**Files Changed:**
- `apps/api/app/services/stripe_service.py`
- `apps/web/src/pages/Landing.tsx`

---

### Issue 3: Subscription Status Not Updating ✅
**Problem:** After successful payment, user tier remained "free" instead of updating to "premium".

**Fix:**
- Added comprehensive logging to webhook handler and tier update logic
- Webhook now logs: event type, user email, tier changes
- This will help diagnose if webhook is being called and where it might be failing
- Frontend dashboard already has polling logic to detect tier updates

**Files Changed:**
- `apps/api/app/routers/payments.py`
- `apps/api/app/services/stripe_service.py`

**Note:** If tier still doesn't update, check:
1. Stripe webhook is configured in Stripe Dashboard
2. Webhook endpoint URL is correct: `https://prk.promptranks.org/payments/webhook`
3. Webhook signing secret matches `.env` value
4. Check API logs for webhook delivery

---

### Issue 4: Results Page CTAs ✅
**Problem:** After claiming badge, no clear path to dashboard or leaderboard.

**Fix:**
- Added "Back to Dashboard" button for all assessments
- Added "View Leaderboard" button for full assessments only
- Buttons appear after badge is claimed
- Clean, consistent navigation flow

**Files Changed:**
- `apps/web/src/pages/Results.tsx`

---

## Testing Instructions

### Prerequisites
Services have been rebuilt and restarted. Verify they're running:
```bash
docker ps
```

You should see:
- `prk-poc-web`
- `prk-poc-api`
- `prk-poc-postgres`
- `prk-poc-redis`

---

## Test Scenarios

### Test 1: Authenticated User - Free Assessment - Badge Auto-Claim

**Steps:**
1. Sign in to the platform (password or OAuth)
2. From landing page, do NOT select industry/role
3. Click "Quick Assessment"
4. Complete KBA phase
5. Complete PPA phase
6. Wait for results page

**Expected:**
- ✅ Results page shows immediately (no register/sign-in form)
- ✅ Badge is auto-claimed
- ✅ You see: "Badge Claimed!" with badge SVG
- ✅ You see buttons: "View Badge" and "Back to Dashboard"
- ✅ No "View Leaderboard" button (quick assessment)

**If Failed:**
- Check browser console for errors
- Verify you're actually authenticated (check for auth token in localStorage)

---

### Test 2: Unauthenticated User - Free Assessment - Manual Claim

**Steps:**
1. Open landing page in incognito/private window
2. Do NOT select industry/role
3. Click "Quick Assessment"
4. Complete assessment
5. On results page, you should see register/sign-in form
6. Register with new email or sign in
7. Wait for auto-claim

**Expected:**
- ✅ Results page shows register/sign-in form
- ✅ After auth, badge is auto-claimed
- ✅ You see CTAs: "View Badge" and "Back to Dashboard"

---

### Test 3: Premium Flow - Industry/Role Selection - Payment - Resume

**Steps:**
1. Sign out (or use incognito)
2. On landing page, select an industry from dropdown
3. Select a role from dropdown
4. Click "Quick Assessment"
5. Auth modal appears → sign in or register
6. Upgrade modal appears → select "Monthly" plan
7. Complete Stripe checkout with test card: `4242 4242 4242 4242`
8. After payment, you're redirected back to landing

**Expected:**
- ✅ Landing page shows: "Payment successful! Verifying your premium access..."
- ✅ After a few seconds, message disappears
- ✅ Assessment automatically starts with your selected industry/role
- ✅ You complete assessment
- ✅ Badge is auto-claimed
- ✅ You see all CTAs

**If Failed:**
- Check if you're redirected to landing (not dashboard)
- Check browser console for errors
- Check if `pending_premium_assessment` is in sessionStorage
- Check API logs for webhook delivery

---

### Test 4: Subscription Tier Update Verification

**Steps:**
1. Before payment, go to `/dashboard`
2. Note your tier badge shows "FREE"
3. Complete payment flow (Test 3)
4. Return to `/dashboard`

**Expected:**
- ✅ Tier badge now shows "PREMIUM"
- ✅ Usage card appears: "0 / 3 full assessments used"
- ✅ Analytics section is visible
- ✅ Subscription card shows: "Premium Plan - $19/month"

**If Failed - Tier Still Shows FREE:**

Check webhook delivery:
```bash
docker logs prk-poc-api | grep -i webhook
```

You should see:
```
Webhook: Received Stripe webhook, signature present: True
Webhook: Event type: checkout.session.completed
Webhook: Processing checkout.session.completed
Webhook: Updating user {email} from tier 'free' to 'premium'
Webhook: Successfully updated user {email} to premium tier
```

If you don't see these logs:
1. Webhook is not configured in Stripe Dashboard
2. Go to: https://dashboard.stripe.com/test/webhooks
3. Add endpoint: `https://prk.promptranks.org/payments/webhook`
4. Select events: `checkout.session.completed`, `customer.subscription.deleted`
5. Copy signing secret to `.env` as `STRIPE_WEBHOOK_SECRET`
6. Restart API container

---

### Test 5: Full Assessment - Leaderboard CTA

**Steps:**
1. Sign in as premium user
2. Select industry/role
3. Click "Full Assessment"
4. Complete all three phases (KBA, PPA, PSV)
5. View results page

**Expected:**
- ✅ Badge auto-claimed
- ✅ You see three buttons: "View Badge", "View Leaderboard", "Back to Dashboard"
- ✅ Click "View Leaderboard" → navigates to `/leaderboard`
- ✅ Click "Back to Dashboard" → navigates to `/dashboard`

---

### Test 6: Payment Cancellation

**Steps:**
1. Start premium flow (select industry/role)
2. Authenticate
3. Upgrade modal appears
4. Select plan and click upgrade
5. On Stripe checkout page, click browser back button
6. You return to landing page

**Expected:**
- ✅ Landing page shows: "Payment was cancelled. You can try again anytime."
- ✅ Message disappears after 5 seconds
- ✅ Your industry/role selection is still preserved
- ✅ You can click "Quick Assessment" again to retry

---

### Test 7: Annual Plan Selection

**Steps:**
1. Start premium flow
2. In upgrade modal, select "Annual" plan
3. Complete Stripe checkout
4. Return to dashboard

**Expected:**
- ✅ Stripe checkout shows $190/year price
- ✅ After payment, subscription card shows: "Premium Plan - $190/year"

---

### Test 8: Direct Sign-In Flow

**Steps:**
1. Sign out
2. From landing page, click "Sign In" (if available) or navigate to `/dashboard`
3. Sign in with password

**Expected:**
- ✅ After sign-in, you land on `/dashboard` immediately
- ✅ No need to sign in twice
- ✅ Dashboard loads with your data

---

## Validation Results

### Build Status ✅
```
Frontend: Built successfully (719.27 kB)
Backend: Syntax valid
Tests: 5 passed (test_payments.py)
```

### Deployment Status ✅
```
Services rebuilt and restarted:
- prk-poc-api (with logging)
- prk-poc-web (with fixes)
```

---

## Known Issues to Watch For

### 1. Webhook Delay
If tier doesn't update immediately after payment:
- Dashboard polls 6 times (9 seconds total)
- If still not updated, you'll see: "Payment succeeded. Subscription sync is still in progress..."
- This is normal if webhook is delayed
- Refresh page manually after a few seconds

### 2. SessionStorage Limitation
If you close the browser tab during payment:
- Pending assessment context is lost
- You'll need to select industry/role again
- This is expected behavior (sessionStorage is tab-specific)

### 3. Test Mode Cards
Only these test cards work in Stripe sandbox:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Real cards will fail

---

## Debugging Tips

### Check Authentication State
```javascript
// In browser console
localStorage.getItem('auth_token')
localStorage.getItem('auth_user')
```

### Check Pending Assessment
```javascript
// In browser console
sessionStorage.getItem('pending_premium_assessment')
sessionStorage.getItem('auth_intent')
```

### Check API Logs
```bash
# All logs
docker logs prk-poc-api

# Webhook logs only
docker logs prk-poc-api | grep -i webhook

# Recent errors
docker logs prk-poc-api | grep -i error | tail -20
```

### Check Database Tier
```bash
docker exec -it prk-poc-postgres psql -U postgres -d promptranks -c "SELECT email, subscription_tier FROM users WHERE email = 'your@email.com';"
```

---

## Success Criteria

All tests pass when:
- ✅ Authenticated users see badge auto-claimed
- ✅ Unauthenticated users see register/sign-in form
- ✅ After payment, assessment resumes with exact industry/role
- ✅ Subscription tier updates to premium after payment
- ✅ Results page shows appropriate CTAs
- ✅ Dashboard reflects premium status
- ✅ One-click sign-in works (no double sign-in)
- ✅ Monthly and annual plans both work

---

## Next Steps After Testing

1. **If all tests pass:**
   - Document any edge cases you found
   - Consider adding more test cards for different scenarios
   - Test with real Stripe account (live mode)

2. **If webhook doesn't fire:**
   - Configure webhook in Stripe Dashboard
   - Test webhook delivery with Stripe CLI
   - Verify signing secret matches

3. **If assessment doesn't resume:**
   - Check browser console for errors
   - Verify sessionStorage has pending assessment
   - Check if landing page resume effect is firing

---

## Contact

If you encounter issues not covered here:
1. Check browser console for errors
2. Check API logs for backend errors
3. Verify all environment variables are set
4. Ensure containers are running and healthy

For webhook configuration help, see:
https://stripe.com/docs/webhooks/quickstart
