# PromptRanks Webapp v1 - Product Requirements Document

**Version:** 1.0
**Date:** 2026-03-28
**Status:** Draft for Review

---

## Executive Summary

Transform PromptRanks from an open assessment tool into a conversion-optimized SaaS platform with freemium monetization. Free users get unlimited quick assessments; premium users ($19/mo) get 3 full assessments/month with industry/role targeting; enterprise users get unlimited access.

**Key Strategy:** Let free users complete full assessments but gate the results behind paywall to maximize conversion at the moment of highest engagement.

---

## Current State Analysis

### Existing Architecture
- **Frontend:** React + TypeScript (Vite), deployed at prk.promptranks.org
- **Backend:** FastAPI + PostgreSQL + Redis, deployed at api.promptranks.org
- **Auth:** Basic email/password with JWT tokens
- **Assessment Flow:**
  - Landing → Start (mode selection) → KBA → PPA → (PSV for full) → Results → Badge claim
  - No user requirement until badge claim
  - No limits on assessment attempts
  - No industry/role selection (fields exist in DB but unused in UI)

### Current User Model
```python
# apps/api/app/models/user.py
- id, email, name, password_hash
- subscription_tier: "free" (default)
- subscription_expires_at: nullable
- is_active, last_login_at, created_at, updated_at
```

### Current Assessment Model
```python
# apps/api/app/models/assessment.py
- mode: "quick" | "full"
- status: "in_progress" | "completed" | "voided" | "expired"
- industry, role (string, nullable)
- industry_id, role_id (UUID, nullable, FK to taxonomy)
- user_id (nullable - anonymous allowed)
```

### Gaps Identified
1. **No conversion checkpoints** - users can do unlimited full assessments anonymously
2. **No usage tracking** - no monthly assessment count per user
3. **No paywall enforcement** - results always visible
4. **No OAuth providers** - only email/password
5. **No magic link auth** - friction for quick signup
6. **No personal dashboard** - nowhere to view history, manage subscription
7. **No payment integration** - no Stripe/billing
8. **No enterprise tier** - only free tier exists in DB

---

## Product Requirements

### 1. Freemium Model & Limits

#### 1.1 Tier Definitions

| Tier | Price | Quick Assessments | Full Assessments | Industry/Role | Features |
|------|-------|-------------------|------------------|---------------|----------|
| **Free** | $0 | Unlimited | 0/month (can take but can't see results) | ❌ | Basic badge, leaderboard |
| **Premium** | $19/month | Unlimited | 3/month | ✅ | Full results, history, analytics, priority support |
| **Enterprise** | Custom | Unlimited | Unlimited | ✅ | Team management, API access, custom branding, dedicated support |

#### 1.2 Usage Tracking

**New DB Table: `user_usage`**
```sql
CREATE TABLE user_usage (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  period_start DATE NOT NULL,  -- first day of month
  period_end DATE NOT NULL,    -- last day of month
  full_assessments_used INT DEFAULT 0,
  full_assessments_limit INT NOT NULL,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE(user_id, period_start)
);
```

**Logic:**
- On assessment start: check `user_usage` for current month
- If limit reached and tier = premium: block with upgrade modal
- If tier = free and mode = full: allow assessment but mark as `results_locked = true`
- Reset counter on 1st of each month (cron job or lazy check)

#### 1.3 Paywall Strategy

**Free User Full Assessment Flow:**
1. User selects "Full Assessment" on landing page
2. ✅ Allow industry/role selection (show "Premium" badge but don't block)
3. ✅ Allow KBA phase completion
4. ✅ Allow PPA phase completion
5. ✅ Allow PSV phase completion
6. ❌ **BLOCK at Results page** - show paywall modal instead of scores
7. Modal: "Unlock your results with Premium" + pricing + CTA

**Premium User Limit Reached:**
1. User clicks "Start Full Assessment"
2. Check `user_usage.full_assessments_used >= 3`
3. Show modal: "You've used 3/3 assessments this month. Upgrade to Enterprise for unlimited access."
4. Block assessment start

---

### 2. Authentication & Onboarding

#### 2.1 Sign In/Up Methods

**Providers:**
- Google OAuth 2.0
- GitHub OAuth
- Magic Link (passwordless email)
- Email/Password (existing)

**UI Placement:**
- Landing page: "Sign In" link in header
- Assessment start: Optional "Sign in to save progress" (dismissible)
- Results paywall: Required for free users, "Sign up to unlock results"

#### 2.2 Landing Page Updates

**Current CTA Section:**
```tsx
// Two buttons: "Quick Assessment" and "Full Assessment"
```

**New Design:**
```tsx
<div style={styles.heroPanel}>
  {/* Existing content */}

  <div style={styles.buttonRow}>
    <button onClick={startQuick}>Start Quick Assessment</button>
    <button onClick={startFull}>
      Start Full Assessment
      <span style={styles.proBadge}>PRO</span>
    </button>
  </div>

  {/* NEW: Auth links below buttons */}
  <div style={styles.authLinks}>
    <span style={styles.authPrompt}>Already have an account?</span>
    <button onClick={openSignIn} style={styles.linkButton}>Sign In</button>
    <span style={styles.authDivider}>·</span>
    <button onClick={openSignUp} style={styles.linkButton}>Sign Up</button>
  </div>
</div>
```

**Industry/Role Selection:**
- Show dropdowns for both quick and full modes
- Add "Premium Feature" badge next to industry/role dropdowns
- Free users can see options but selections only apply for premium users
- Store selections in assessment record regardless of tier

#### 2.3 Auth Modal Component

**New Component: `AuthModal.tsx`**
- Tabs: "Sign In" | "Sign Up"
- Methods displayed as buttons with icons:
  - "Continue with Google" (OAuth)
  - "Continue with GitHub" (OAuth)
  - "Continue with Email" (magic link)
  - Divider: "or use password"
  - Email + Password fields (collapsible)

**Magic Link Flow:**
1. User enters email
2. API sends email with JWT token link
3. User clicks link → auto-login → redirect to dashboard or assessment
4. Token expires in 15 minutes

---

### 3. Personal Dashboard

#### 3.1 Dashboard Layout

**Route:** `/dashboard`

**Sections:**
1. **Header:** User name, avatar, tier badge, "Upgrade" button (if not enterprise)
2. **Usage Stats:** Current month progress bar (e.g., "2/3 full assessments used")
3. **Assessment History:** Table with columns:
   - Date
   - Mode (Quick/Full)
   - Score
   - Level
   - Badge link
   - "View Details" button
4. **Analytics:** (Premium/Enterprise only)
   - Score trend chart (line graph over time)
   - Pillar radar comparison (latest vs average)
   - Skill gap analysis (weakest pillars highlighted)
   - Recommended focus areas
5. **Subscription Management:**
   - Current plan details
   - Billing cycle
   - Payment method
   - "Manage Subscription" → Stripe portal
   - "Upgrade" or "Cancel" buttons

#### 3.2 Recommended Features (Premium+)

**Algorithm:**
- Identify lowest 2 pillar scores from latest assessment
- Suggest: "Focus on [Pillar Name] - Try these resources: [links]"
- Show: "Take another assessment in [X days] to track improvement"

**Learning Paths:**
- Curated external resources (articles, courses, tools)
- Stored in new table: `learning_resources`
- Filtered by pillar and level

---

### 4. Payment Integration

#### 4.1 Stripe Setup

**Products:**
- Premium Monthly: $19/month
- Premium Annual: $190/year (save $38)
- Enterprise: Custom (contact sales form)

**Webhook Events:**
- `checkout.session.completed` → activate subscription
- `invoice.payment_succeeded` → extend subscription
- `invoice.payment_failed` → send reminder, grace period 3 days
- `customer.subscription.deleted` → downgrade to free

#### 4.2 Upgrade Flow

**From Landing Page:**
1. User clicks "Start Full Assessment" (free tier)
2. Completes assessment
3. Hits paywall at results
4. Clicks "Upgrade to Premium"
5. Redirect to Stripe Checkout
6. On success → redirect to `/dashboard?session_id={id}`
7. Webhook activates subscription
8. User sees unlocked results

**From Dashboard:**
1. User clicks "Upgrade" button
2. Show pricing modal with monthly/annual toggle
3. Click plan → Stripe Checkout
4. On success → redirect to dashboard with success message

#### 4.3 Subscription Management

**Stripe Customer Portal:**
- Embedded via `stripe.createPortalSession()`
- Allows: update payment method, view invoices, cancel subscription
- Cancel: immediate downgrade to free, no refund (pro-rated credit for annual)

---

### 5. Database Schema Changes

#### 5.1 New Tables

**`user_usage`** (already defined above)

**`oauth_accounts`**
```sql
CREATE TABLE oauth_accounts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  provider VARCHAR(50) NOT NULL,  -- 'google', 'github'
  provider_user_id VARCHAR(255) NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  expires_at TIMESTAMP,
  created_at TIMESTAMP,
  UNIQUE(provider, provider_user_id)
);
```

**`magic_links`**
```sql
CREATE TABLE magic_links (
  id UUID PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  token VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP,
  created_at TIMESTAMP
);
```

**`learning_resources`**
```sql
CREATE TABLE learning_resources (
  id UUID PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  url TEXT NOT NULL,
  pillar VARCHAR(1),  -- P, E, C, A, M
  min_level INT,
  max_level INT,
  resource_type VARCHAR(50),  -- 'article', 'video', 'course', 'tool'
  created_at TIMESTAMP
);
```

**`stripe_customers`**
```sql
CREATE TABLE stripe_customers (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id) UNIQUE,
  stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
  stripe_subscription_id VARCHAR(255),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### 5.2 Modified Tables

**`users`** - add columns:
```sql
ALTER TABLE users ADD COLUMN avatar_url TEXT;
ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50);  -- null if email/password
ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);
```

**`assessments`** - add column:
```sql
ALTER TABLE assessments ADD COLUMN results_locked BOOLEAN DEFAULT FALSE;
```

---

### 6. API Endpoints

#### 6.1 New Auth Endpoints

**OAuth:**
- `GET /auth/google` - redirect to Google OAuth
- `GET /auth/google/callback` - handle OAuth callback
- `GET /auth/github` - redirect to GitHub OAuth
- `GET /auth/github/callback` - handle OAuth callback

**Magic Link:**
- `POST /auth/magic-link` - send magic link email
  - Body: `{ email: string }`
  - Response: `{ message: "Check your email" }`
- `GET /auth/magic-link/verify?token={token}` - verify and login
  - Response: `{ token: string, user: {...} }`

#### 6.2 New Usage Endpoints

- `GET /users/me/usage` - get current month usage
  - Response: `{ period_start, period_end, used, limit, tier }`
- `POST /assessments/check-limit` - check if user can start assessment
  - Body: `{ mode: "quick" | "full" }`
  - Response: `{ allowed: boolean, reason?: string }`

#### 6.3 New Dashboard Endpoints

- `GET /users/me/dashboard` - get dashboard data
  - Response: `{ user, usage, assessments[], analytics }`
- `GET /users/me/assessments` - list user's assessments
  - Query: `?page=1&limit=10&mode=all|quick|full`
- `GET /assessments/{id}/details` - get full assessment breakdown
  - Response: `{ assessment, pillar_scores, recommendations }`

#### 6.4 New Payment Endpoints

- `POST /payments/create-checkout` - create Stripe checkout session
  - Body: `{ plan: "premium_monthly" | "premium_annual" }`
  - Response: `{ checkout_url: string }`
- `POST /payments/webhook` - Stripe webhook handler
- `POST /payments/create-portal` - create Stripe portal session
  - Response: `{ portal_url: string }`
- `GET /payments/subscription` - get current subscription details

---

### 7. Frontend Components

#### 7.1 New Pages

1. **`/dashboard`** - Personal dashboard (described in 3.1)
2. **`/pricing`** - Pricing page with tier comparison
3. **`/auth/verify`** - Magic link landing page

#### 7.2 New Components

1. **`AuthModal.tsx`** - Sign in/up modal with OAuth + magic link
2. **`PaywallModal.tsx`** - Results paywall for free users
3. **`UpgradeModal.tsx`** - Pricing + upgrade CTA
4. **`UsageBadge.tsx`** - Shows "2/3 assessments used" in header
5. **`AssessmentHistoryTable.tsx`** - Sortable table of past assessments
6. **`AnalyticsCharts.tsx`** - Score trends + radar comparison
7. **`SubscriptionCard.tsx`** - Current plan + manage button

#### 7.3 Modified Components

**`Landing.tsx`:**
- Add auth links below CTA buttons
- Add "PRO" badge to full assessment button
- Add industry/role dropdowns with "Premium" indicator
- Add `AuthModal` integration

**`Results.tsx`:**
- Check `assessment.results_locked` flag
- If locked: show `PaywallModal` instead of scores
- If unlocked: show existing results + "Save to Dashboard" CTA

**`App.tsx`:**
- Add `/dashboard` route (protected)
- Add `/pricing` route
- Add `/auth/verify` route
- Add auth context provider

---

### 8. Email Templates

#### 8.1 Magic Link Email
**Subject:** Sign in to PromptRanks
**Body:**
```
Hi there,

Click the link below to sign in to your PromptRanks account:

[Sign In Button] → https://prk.promptranks.org/auth/verify?token={token}

This link expires in 15 minutes.

If you didn't request this, ignore this email.

---
PromptRanks Team
```

#### 8.2 Welcome Email (New User)
**Subject:** Welcome to PromptRanks!
**Body:**
```
Welcome to PromptRanks!

You're all set. Here's what you can do:

✓ Take unlimited quick assessments
✓ View your scores on the leaderboard
✓ Earn verifiable badges

Want more? Upgrade to Premium for:
• 3 full assessments per month
• Industry & role targeting
• Detailed analytics
• Priority support

[Upgrade to Premium]

Happy prompting!
```

#### 8.3 Upgrade Confirmation
**Subject:** Welcome to PromptRanks Premium!
**Body:**
```
You're now a Premium member!

Your benefits:
• 3 full assessments per month
• Industry & role-specific insights
• Advanced analytics dashboard
• Priority support

[Go to Dashboard]

Questions? Reply to this email.
```

#### 8.4 Usage Limit Warning
**Subject:** You've used 2/3 assessments this month
**Body:**
```
Heads up!

You've used 2 of your 3 full assessments this month.

Your limit resets on {reset_date}.

Need more? Upgrade to Enterprise for unlimited assessments.

[View Plans]
```

---

### 9. Conversion Optimization

#### 9.1 Paywall Messaging

**Free User at Results:**
```
🔒 Unlock Your Full Assessment Results

You scored [REDACTED] and earned Level [REDACTED]

See your complete breakdown:
✓ Final score & level badge
✓ PECAM pillar analysis
✓ Personalized recommendations
✓ Shareable certificate

[Upgrade to Premium - $19/month] [View Pricing]

Already have an account? [Sign In]
```

**Premium User at Limit:**
```
⚠️ Assessment Limit Reached

You've completed 3/3 full assessments this month.

Your limit resets on {date}.

Need unlimited assessments?

[Upgrade to Enterprise] [Contact Sales]
```

#### 9.2 Upgrade Prompts

**Dashboard Banner (Free Users):**
```
🚀 Upgrade to Premium and unlock full assessments with industry targeting

[See Plans] [Dismiss]
```

**Post-Quick-Assessment (Free Users):**
```
Great job! Want deeper insights?

Premium members get:
• 3 full assessments/month
• Industry-specific scoring
• Advanced analytics

[Try Full Assessment] [Learn More]
```

---

### 10. Analytics & Tracking

#### 10.1 Key Metrics

**Conversion Funnel:**
1. Landing page visits
2. Assessment starts (quick vs full)
3. Assessment completions
4. Results page views
5. Paywall impressions (free users)
6. Upgrade clicks
7. Checkout starts
8. Successful payments

**User Metrics:**
- Free → Premium conversion rate
- Premium → Enterprise conversion rate
- Monthly churn rate
- Average assessments per user
- Time to first upgrade

#### 10.2 Event Tracking

**Frontend Events (PostHog/Mixpanel):**
- `assessment_started` - { mode, tier, has_account }
- `assessment_completed` - { mode, score, level, tier }
- `paywall_shown` - { mode, score }
- `upgrade_clicked` - { source: "paywall" | "dashboard" | "banner" }
- `checkout_started` - { plan }
- `checkout_completed` - { plan, amount }

**Backend Events:**
- Log all API calls with user_id, tier, endpoint
- Track usage limit checks
- Track failed payment attempts

---

### 11. Development Sprints

#### Sprint 1: Auth Foundation (Week 1)
**Goal:** Implement OAuth + magic link authentication

**Tasks:**
1. Add `oauth_accounts` and `magic_links` tables
2. Implement Google OAuth flow (backend + frontend)
3. Implement GitHub OAuth flow (backend + frontend)
4. Implement magic link flow (backend + frontend + email)
5. Create `AuthModal` component
6. Update Landing page with auth links
7. Add auth context provider
8. Test all auth flows

**Deliverables:**
- Users can sign in/up with Google, GitHub, or magic link
- Existing email/password auth still works
- Auth modal integrated on landing page

---

#### Sprint 2: Usage Tracking & Limits (Week 2)
**Goal:** Implement tier-based assessment limits

**Tasks:**
1. Add `user_usage` table
2. Add `results_locked` column to assessments
3. Implement usage tracking service
4. Add `POST /assessments/check-limit` endpoint
5. Add `GET /users/me/usage` endpoint
6. Update assessment start flow to check limits
7. Update Results page to check `results_locked` flag
8. Create `PaywallModal` component
9. Test limit enforcement for free and premium users

**Deliverables:**
- Free users can complete full assessments but can't see results
- Premium users limited to 3 full assessments/month
- Usage resets monthly
- Paywall modal shows at results for free users

---

#### Sprint 3: Dashboard & History (Week 3)
**Goal:** Build personal dashboard with assessment history

**Tasks:**
1. Create `/dashboard` route and page component
2. Implement `GET /users/me/dashboard` endpoint
3. Implement `GET /users/me/assessments` endpoint
4. Create `AssessmentHistoryTable` component
5. Create `UsageBadge` component for header
6. Add navigation to dashboard from results page
7. Implement assessment details view
8. Add "Save to Dashboard" CTA on results page
9. Test dashboard with multiple assessments

**Deliverables:**
- Users can view all past assessments
- Dashboard shows current usage stats
- Assessment details page shows full breakdown

---

#### Sprint 4: Analytics & Recommendations (Week 4)
**Goal:** Add analytics dashboard for premium users

**Tasks:**
1. Add `learning_resources` table
2. Seed learning resources data
3. Implement analytics calculation service
4. Create `AnalyticsCharts` component (score trends, radar)
5. Implement skill gap analysis algorithm
6. Add recommendations section to dashboard
7. Add `GET /assessments/{id}/details` endpoint with recommendations
8. Test analytics with multiple assessments over time

**Deliverables:**
- Premium users see score trends and pillar comparisons
- Personalized recommendations based on weakest pillars
- Learning resources suggested per pillar

---

#### Sprint 5: Stripe Integration (Week 5)
**Goal:** Implement payment processing and subscription management

**Tasks:**
1. Set up Stripe account and products
2. Add `stripe_customers` table
3. Implement Stripe checkout flow
4. Add `POST /payments/create-checkout` endpoint
5. Add `POST /payments/webhook` endpoint
6. Implement webhook handlers (subscription events)
7. Add `POST /payments/create-portal` endpoint
8. Create `UpgradeModal` component with pricing
9. Create `/pricing` page
10. Add subscription management to dashboard
11. Test full payment flow (checkout → webhook → activation)
12. Test subscription cancellation and renewal

**Deliverables:**
- Users can upgrade to premium via Stripe
- Webhooks automatically activate/deactivate subscriptions
- Users can manage subscriptions via Stripe portal
- Pricing page shows all tiers

---

#### Sprint 6: Industry/Role & Polish (Week 6)
**Goal:** Enable industry/role selection and polish UX

**Tasks:**
1. Update Landing page to show industry/role dropdowns
2. Add "Premium" badges to industry/role selectors
3. Update assessment start flow to save industry/role
4. Add industry/role filters to dashboard
5. Update leaderboard to support industry/role filtering
6. Implement email templates (welcome, upgrade, limit warning)
7. Add email sending service (SendGrid/Postmark)
8. Add conversion tracking events
9. Polish all modals and transitions
10. Add loading states and error handling
11. Mobile responsive testing
12. End-to-end testing of full user journey

**Deliverables:**
- Industry/role selection works for premium users
- All email notifications sent correctly
- Smooth UX across all flows
- Mobile-friendly design
- Analytics tracking in place

---

### 12. Success Metrics

**Launch Goals (Month 1):**
- 1,000 total users
- 10% free → premium conversion rate
- 50 paying subscribers
- $950 MRR

**Growth Goals (Month 3):**
- 5,000 total users
- 15% conversion rate
- 300 paying subscribers
- $5,700 MRR
- 5 enterprise customers

**Key Success Indicators:**
- Average 2+ assessments per user
- <5% monthly churn
- 4.5+ star rating from premium users
- 80%+ paywall → checkout click-through rate

---

## Appendix

### A. Tech Stack Summary

**Frontend:**
- React 18 + TypeScript
- Vite
- React Router
- Recharts (for analytics)
- Stripe.js

**Backend:**
- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy (async)
- Stripe Python SDK
- OAuth libraries (authlib)

**Infrastructure:**
- Docker + Docker Compose
- Nginx reverse proxy
- SendGrid/Postmark for email
- PostHog/Mixpanel for analytics

### B. Security Considerations

1. **OAuth tokens:** Store encrypted, rotate on refresh
2. **Magic links:** Single-use, 15-min expiry, rate-limited
3. **Stripe webhooks:** Verify signature on all webhook events
4. **Assessment results:** Check user ownership before unlocking
5. **Rate limiting:** 10 requests/min per IP on auth endpoints
6. **CORS:** Whitelist only production domains

### C. Open Questions for Review

1. **Pricing:** Is $19/month optimal? Should we A/B test $15 vs $19?
2. **Limits:** Should premium users get 3 or 5 full assessments/month?
3. **Grace period:** Should we allow 1 extra assessment if user upgrades mid-month?
4. **Refunds:** Pro-rated refunds on cancellation or no refunds?
5. **Enterprise:** Should we show enterprise pricing or "Contact Sales" only?
6. **Leaderboard:** Should premium users have separate leaderboard or unified?
7. **Badges:** Should free users get badges for quick assessments?

---

**End of PRD**

**Next Steps:**
1. Review and approve this PRD
2. Prioritize sprints based on business goals
3. Assign sprint ownership
4. Begin Sprint 1 development
5. Set up staging environment for testing
