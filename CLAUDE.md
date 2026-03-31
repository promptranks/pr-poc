# PromptRanks PoC — Development Instructions

## Project Overview
Open-source AI prompt engineering assessment platform using the PECAM framework.
Tech stack: FastAPI + React/TypeScript + PostgreSQL + Redis + Claude API.

## Key Rules
- **Dual license**: Code is MIT, content (questions/tasks/docs) is CC-BY-SA 4.0
- **Security**: Never commit API keys, use .env for secrets, validate all user input
- **Bcrypt for passwords**: Use bcrypt directly (not Passlib), 72-byte limit
- **SHA256 for tokens**: JWT and session tokens use SHA256
- **Anti-cheat**: Assessment pages must enforce tab-lock and timer

## Architecture
- `apps/api/` — FastAPI backend (Python 3.12)
- `apps/web/` — React 18 + TypeScript + Vite frontend
- `content/` — KBA questions and PPA tasks in YAML (CC-BY-SA)
- `infra/` — Docker, Postgres schema, Nginx
- `scripts/` — Seed data, utilities

## Development
```bash
docker compose up -d          # Start all services
docker compose exec api pytest  # Run backend tests
cd apps/web && npm run dev    # Frontend dev server
```

## Conventions
- Python: ruff for linting, mypy for types
- TypeScript: ESLint + Prettier
- Commits: Conventional Commits (feat:, fix:, docs:, content:)
- Branches: feature/* from develop, squash-merge PRs
- Questions/tasks: YAML format in content/, follow existing examples

## Design System — Matrix Theme (v2)

All frontend pages MUST follow the PromptRanks v2 matrix/cyberpunk theme. Reference: https://v2.promptranks.org

### CSS Variables
```css
:root {
  /* Matrix greens */
  --matrix-green: #00ff41;
  --matrix-green-dim: #008f11;
  --matrix-green-glow: rgba(0,255,65,0.4);
  --matrix-green-subtle: rgba(0,255,65,0.08);
  --matrix-green-border: rgba(0,255,65,0.2);

  /* Backgrounds */
  --bg-page: #000000;
  --bg-card: rgba(0,15,0,0.6);
  --bg-card-hover: rgba(0,25,0,0.8);

  /* Text */
  --text-primary: #00ff41;
  --text-secondary: #008f11;
  --text-white: #c0ffc0;

  /* Borders & Shadows */
  --border: rgba(0,255,65,0.1);
  --border-hover: rgba(0,255,65,0.3);
  --shadow-glow: 0 0 30px rgba(0,255,65,0.3);
  --shadow-card: 0 8px 32px rgba(0,0,0,0.8);

  /* Radius */
  --radius: 4px;
  --radius-lg: 8px;
  --radius-xl: 12px;

  /* Fonts */
  --font-heading: 'Press Start 2P', monospace;
  --font-body: 'Share Tech Mono', monospace;

  /* Accent (for CTAs, badges, gradients) */
  --accent-purple: #6D5FFA;
  --accent-pink: #EC41FB;
  --gradient-cta: linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%);
}
```

### Session Resume Notes — 2026-03-31 (Latest)

### Critical fixes completed in this session

#### Issue 1: Results page authentication check ✅
**Problem:** Authenticated users completing assessments still saw register/sign-in form instead of auto-claimed badge.

**Fix:**
- `apps/web/src/pages/Results.tsx` now checks `AuthContext` for authentication
- Auto-claims badge for authenticated users via `POST /assessments/{id}/claim` with Bearer token
- Only shows register/sign-in form for unauthenticated users
- Added CTAs after claim: "View Badge", "View Leaderboard" (full only), "Back to Dashboard"

#### Issue 2: Post-payment assessment resume ✅
**Problem:** After successful Stripe payment, user was redirected to dashboard instead of continuing their selected assessment with industry/role.

**Fix:**
- Changed Stripe `success_url` from `/dashboard?session_id=...` to `/?checkout=success&session_id=...`
- Landing page now detects checkout return and shows success message
- Pending assessment context (mode, industryId, roleId) preserved in sessionStorage
- After tier update detected, system automatically resumes exact assessment user selected

**Files:**
- `apps/api/app/services/stripe_service.py` - line 65
- `apps/web/src/pages/Landing.tsx` - added checkout detection effect

#### Issue 3: Subscription tier update logging ✅
**Problem:** After successful payment, user tier remained "free" - unclear if webhook was firing.

**Fix:**
- Added comprehensive logging to webhook handler and tier update logic
- Logs now show: webhook receipt, event type, user email, tier changes
- This enables diagnosis of webhook delivery issues

**Files:**
- `apps/api/app/routers/payments.py` - webhook endpoint
- `apps/api/app/services/stripe_service.py` - handle_checkout_completed

**Webhook logs to check:**
```bash
docker logs prk-poc-api | grep -i webhook
```

Expected output:
```
Webhook: Received Stripe webhook, signature present: True
Webhook: Event type: checkout.session.completed
Webhook: Updating user {email} from tier 'free' to 'premium'
Webhook: Successfully updated user {email} to premium tier
```

#### Issue 4: Results page CTAs ✅
**Problem:** After claiming badge, no clear navigation to dashboard or leaderboard.

**Fix:**
- Added "Back to Dashboard" button for all assessments
- Added "View Leaderboard" button for full assessments only
- Buttons appear in CTA section after badge claim

### Validation completed after fixes
- Frontend build: ✅ Passed (719.27 kB)
- Backend tests: ✅ 5 passed (test_payments.py)
- Services rebuilt: ✅ api and web containers recreated

### Documentation created
1. **Promptranks_User_Conversion_Journey.md** - Comprehensive business logic with mermaid flowchart covering all user paths
2. **TESTING_GUIDE.md** - Step-by-step testing instructions for all 8 test scenarios

### Current dev status
All 4 reported issues have been fixed and deployed:
1. ✅ Authenticated users see badge auto-claimed
2. ✅ Post-payment assessment resumes with exact industry/role selection
3. ✅ Webhook logging added for subscription sync debugging
4. ✅ Results page shows dashboard/leaderboard CTAs

### Ready for manual browser testing
The following test scenarios should now work:
1. Authenticated user completes free assessment → badge auto-claimed → sees CTAs
2. Unauthenticated user completes assessment → register/sign-in → badge auto-claimed
3. Free user selects industry/role → auth → upgrade → payment → assessment resumes with exact selection
4. Subscription tier updates to premium after successful payment (check webhook logs if fails)
5. Full assessment shows "View Leaderboard" CTA
6. One-click sign-in works (no double sign-in needed)
7. Monthly and annual plans both work
8. Payment cancellation returns to landing with message

### If subscription tier doesn't update after payment
This indicates webhook is not being delivered. Check:
1. Stripe webhook configured at: https://dashboard.stripe.com/test/webhooks
2. Endpoint URL: `https://prk.promptranks.org/payments/webhook`
3. Events selected: `checkout.session.completed`, `customer.subscription.deleted`
4. Signing secret in `.env` matches Stripe dashboard
5. API logs show webhook receipt: `docker logs prk-poc-api | grep -i webhook`

If webhook is not configured, tier will never update. Dashboard polling can't help if webhook never fires.

### Deployment reminder for future changes
Frontend changes require rebuild:
```bash
docker compose -f /Volumes/DEV/Scopelabs.work/opensource/prk-poc/docker-compose.yml --project-directory /Volumes/DEV/Scopelabs.work/opensource/prk-poc up -d --build web
```

Backend changes require recreate:
```bash
docker compose -f /Volumes/DEV/Scopelabs.work/opensource/prk-poc/docker-compose.yml --project-directory /Volumes/DEV/Scopelabs.work/opensource/prk-poc up -d api
```

Both:
```bash
docker compose -f /Volumes/DEV/Scopelabs.work/opensource/prk-poc/docker-compose.yml --project-directory /Volumes/DEV/Scopelabs.work/opensource/prk-poc up -d --build api web
```

### Session Resume Notes — 2026-03-31 (Earlier)
- `apps/web/src/components/AuthModal.tsx`
  - password sign-in/sign-up now uses `AuthContext.login(...)` before navigation
  - fixes the previous behavior where sign-in appeared to require two attempts before dashboard routing worked
- `apps/web/src/pages/AuthCallback.tsx`
  - OAuth callback now also uses `AuthContext.login(...)`
  - keeps in-memory auth state aligned immediately after successful SSO callback
- `apps/web/src/components/UpgradeModal.tsx`
  - supports both `premium_monthly` and `premium_annual`
  - stores `pending_subscription_plan` and `pending_subscription_upgrade` in `sessionStorage` before redirecting to Stripe Checkout
- `apps/api/app/routers/payments.py`
  - checkout request is now strictly typed to `premium_monthly | premium_annual`
- `apps/api/app/services/stripe_service.py`
  - checkout plan mapping now uses:
    - monthly → `STRIPE_PREMIUM_PRICE_ID`
    - annual → `STRIPE_YEARLY_PRICE_ID`
  - checkout session metadata now includes the selected `plan`
- `apps/web/src/pages/Landing.tsx`
  - premium gating no longer clears pending premium assessment state prematurely for free users
  - pending quick/full assessment with selected industry/role is preserved across auth and upgrade flow
  - resume effect now waits for taxonomy readiness and keeps pending state when upgrade is still required
- `apps/web/src/pages/Dashboard.tsx`
  - added post-checkout handling for `session_id` return from Stripe
  - dashboard now retries subscription refresh after checkout to absorb webhook delay
  - added visible assessment CTA buttons on dashboard
  - selected subscription plan is passed down to subscription display
- `apps/web/src/components/SubscriptionCard.tsx`
  - premium subscription copy now reflects monthly vs annual based on stored selected plan

### Stripe/runtime status confirmed earlier in this overall workstream
- `.env` already contains working Stripe sandbox config:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PREMIUM_PRICE_ID`
  - `STRIPE_YEARLY_PRICE_ID`
  - `STRIPE_WEBHOOK_SECRET`
- Stripe sandbox checkout was previously confirmed to open successfully.

### Focused validation completed after the latest implementation
- Frontend build passed:
  - `npm --prefix /Volumes/DEV/Scopelabs.work/opensource/prk-poc/apps/web run build`
- Backend targeted tests passed in running API container:
  - `tests/test_payments.py`
  - `tests/test_auth.py`
  - `tests/test_dashboard.py`
  - `tests/test_usage.py`
- Result: `29 passed`

### Important validation note
- One failed command in this session was **not** a project failure:
  - I first used the wrong container name `prk-poc-api-1`
  - actual container name is `prk-poc-api`
  - after rerunning with the correct container name, all targeted backend tests passed

### Current dev status
- Code changes for the reported issues are now implemented and locally validated:
  1. direct sign-in should no longer require two attempts
  2. upgrade modal supports monthly + annual plans
  3. backend checkout uses the correct monthly/annual Stripe price ids
  4. dashboard now refreshes after Stripe return instead of staying stale on free immediately
  5. pending premium quick/full assessment context is no longer cleared too early
  6. dashboard now has assessment CTA buttons
  7. subscription card no longer hardcodes monthly-only copy

### Still needs live browser testing
These are the next manual checks to run in the browser after rebuild/restart if needed:
1. Sign in once with password → confirm immediate navigation to `/dashboard`
2. Google SSO → confirm immediate logged-in dashboard/auth state
3. Start with industry + role + Quick as free user → authenticate → upgrade → confirm return path resumes the exact pending quick assessment
4. Repeat with Full assessment → confirm exact full assessment resumes
5. After successful Stripe sandbox checkout, confirm dashboard tier/upgrade UI refreshes from free to premium after return
6. Confirm dashboard CTA buttons route correctly back into assessment flow
7. Confirm monthly and annual checkout options both open Stripe Checkout correctly
8. Confirm subscription card copy matches the selected monthly or annual plan after return

### Deployment reminder for testing these latest frontend changes
Because `web` is image-built rather than source-mounted, browser testing requires rebuilding the web service after frontend edits:
```bash
docker compose -f /Volumes/DEV/Scopelabs.work/opensource/prk-poc/docker-compose.yml --project-directory /Volumes/DEV/Scopelabs.work/opensource/prk-poc up -d --build web
```

If backend Python code also needs to be refreshed in the running stack, recreate `api` as well:
```bash
docker compose -f /Volumes/DEV/Scopelabs.work/opensource/prk-poc/docker-compose.yml --project-directory /Volumes/DEV/Scopelabs.work/opensource/prk-poc up -d --build api web
```

### Highest-priority resume point for the next session
- Rebuild/recreate the services if the browser is still serving old behavior
- Then manually test the 8 browser checks above in order
- If post-checkout tier still stays free, inspect whether Stripe webhook delivery is reaching `/payments/webhook` and updating `users.subscription_tier`
