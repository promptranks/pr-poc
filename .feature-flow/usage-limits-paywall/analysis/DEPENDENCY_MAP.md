# Dependency Map: Usage Limits and Paywall

## File Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                     Entry Points                             │
├─────────────────────────────────────────────────────────────┤
│ apps/api/app/routers/payments.py                            │
│ apps/api/app/routers/assessment.py                          │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│ StripeService            │  │ UsageService             │
│ (stripe_service.py)      │  │ (usage_service.py)       │
└──────────────────────────┘  └──────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────────────────────────────────────────────┐
│                    Database Models                        │
├──────────────────────────────────────────────────────────┤
│ User (user.py)                                           │
│ StripeCustomer (stripe_customer.py)                      │
│ UserUsage (user_usage.py)                                │
│ Assessment (assessment.py)                               │
└──────────────────────────────────────────────────────────┘
```

## Call Graph by Feature

### 1. Assessment Start Flow

```
POST /assessments/start
  └─> assessment.py:start_assessment()
      ├─> UsageService.check_limit()
      │   └─> UsageService.get_or_create_usage()
      │       └─> UsageService.get_tier_limit()
      ├─> UsageService.increment_usage()
      │   └─> UsageService.get_or_create_usage()
      └─> Create Assessment with results_locked flag
```

**Files Involved:**
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/assessment.py` (lines 268-286)
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/services/usage_service.py` (entire file)
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/models/user_usage.py`
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/models/assessment.py`

### 2. Section Score Submission Flow

```
POST /assessments/{id}/kba/submit
  └─> assessment.py:submit_kba()
      ├─> Load Assessment
      ├─> Score answers
      └─> Return scores (NO results_locked check)

POST /assessments/{id}/ppa/execute
  └─> assessment.py:execute_ppa()
      ├─> Load Assessment via _load_assessment()
      ├─> Execute LLM task
      └─> Return output (NO results_locked check)

POST /assessments/{id}/psv/submit
  └─> assessment.py:submit_psv()
      ├─> Load Assessment via _load_assessment()
      ├─> Compute PSV score
      └─> Return score (NO results_locked check)
```

**Files Involved:**
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/assessment.py` (lines 361-421, 496-600, 696-750)

### 3. Stripe Webhook Flow

```
POST /payments/webhook
  └─> payments.py:stripe_webhook()
      ├─> Verify signature
      └─> Route by event type:
          ├─> checkout.session.completed
          │   └─> StripeService.handle_checkout_completed()
          │       ├─> Update User.subscription_tier = "premium"
          │       └─> Update StripeCustomer.stripe_subscription_id
          │       └─> [MISSING] Update UserUsage.full_assessments_limit
          │
          ├─> customer.subscription.deleted
          │   └─> StripeService.handle_subscription_deleted()
          │       ├─> Update User.subscription_tier = "free"
          │       └─> Clear StripeCustomer.stripe_subscription_id
          │
          └─> [MISSING] invoice.payment_failed
          └─> [MISSING] invoice.payment_succeeded
          └─> [MISSING] customer.subscription.updated
```

**Files Involved:**
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/payments.py` (lines 136-166)
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/services/stripe_service.py` (lines 94-146)

### 4. Usage Tracking Flow

```
UsageService.get_or_create_usage()
  ├─> get_current_period() → (period_start, period_end)
  ├─> get_tier_limit(tier) → limit
  ├─> Query UserUsage by user_id + period_start
  └─> If not exists:
      └─> Create new UserUsage(used=0, limit=limit)
  └─> If exists:
      └─> [MISSING] Sync limit with current tier
```

**Files Involved:**
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/services/usage_service.py` (lines 26-52)

## Data Flow Diagram

```
┌──────────────┐
│ User Actions │
└──────┬───────┘
       │
       ├─> Start Assessment
       │   ├─> Check: Is premium feature used? (industry/role/full)
       │   ├─> Check: User tier (free/premium/enterprise)
       │   ├─> Check: Usage limit (via UsageService)
       │   ├─> Increment: Usage counter
       │   └─> Set: results_locked flag
       │
       ├─> Submit Section Scores
       │   ├─> [SHOULD] Check: results_locked flag
       │   └─> Return: Scores or locked message
       │
       └─> Upgrade via Stripe
           ├─> Stripe Checkout
           ├─> Webhook: checkout.session.completed
           ├─> Update: User.subscription_tier
           └─> [SHOULD] Update: UserUsage.full_assessments_limit
```

## Database Schema Dependencies

### UserUsage Table
```sql
CREATE TABLE user_usage (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    full_assessments_used INTEGER DEFAULT 0,
    full_assessments_limit INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**Dependencies:**
- Foreign key to `users.id`
- Used by: UsageService
- Updated by: Assessment start, Stripe webhook (should be)

### Assessment Table
```sql
CREATE TABLE assessments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    mode assessment_mode NOT NULL,
    status assessment_status DEFAULT 'in_progress',
    industry_id UUID REFERENCES industries(id),
    role_id UUID REFERENCES roles(id),
    results_locked BOOLEAN DEFAULT FALSE,
    -- ... other fields
);
```

**Dependencies:**
- Foreign key to `users.id`, `industries.id`, `roles.id`
- `results_locked` field controls paywall behavior
- Used by: Assessment router endpoints

## Critical Integration Points

### 1. Assessment Start → Usage Service
**Location:** `assessment.py:268-286`
**Current State:** Only checks full mode
**Required Change:** Check industry/role selection too

### 2. Section Endpoints → Results Lock Check
**Locations:**
- `assessment.py:361` (submit_kba)
- `assessment.py:496` (execute_ppa)
- `assessment.py:696` (submit_psv)

**Current State:** No results_locked check
**Required Change:** Check assessment.results_locked before returning scores

### 3. Stripe Webhook → Usage Service
**Location:** `stripe_service.py:94-125`
**Current State:** Only updates user tier
**Required Change:** Update current month's usage limit

### 4. Usage Service → Tier Sync
**Location:** `usage_service.py:26-52`
**Current State:** Creates usage with limit, but doesn't update existing records
**Required Change:** Always sync limit with current tier

## Shared State Concerns

### Race Conditions
1. **Concurrent assessment starts**: Multiple requests could increment usage simultaneously
   - Mitigation: Database transaction isolation
   - Current: Uses SQLAlchemy async sessions with commit

2. **Webhook + Assessment start**: User upgrades while starting assessment
   - Mitigation: Webhook updates usage limit, assessment checks current tier
   - Risk: Low (webhook processes quickly)

### Data Consistency
1. **User tier vs Usage limit mismatch**: Premium user with limit=0
   - Root cause: Usage record created before upgrade
   - Solution: Always sync limit in get_or_create_usage()

2. **Free user with used > limit**: Free user took 1 trial, limit shows 0
   - Expected behavior: Free users can use 1 trial (limit=0 but allow 1)
   - Solution: Special handling in check_limit() for free tier

## External Dependencies

### Stripe API
- Webhook events: checkout.session.completed, customer.subscription.deleted
- Required: Webhook signature verification
- Environment: STRIPE_WEBHOOK_SECRET

### Database
- PostgreSQL with UUID support
- Async SQLAlchemy sessions
- Transaction isolation for concurrent updates

### Frontend
- Must handle 402 Payment Required errors
- Must check results_locked flag in responses
- Must show paywall modal when locked

## Testing Dependencies

### Unit Tests Required
- UsageService.check_limit() with free tier
- UsageService.get_or_create_usage() with tier changes
- Assessment start logic with industry/role selection

### Integration Tests Required
- Full flow: Free user → 1 trial → upgrade → 1/3 used
- Webhook processing → Usage limit update
- Section score endpoints with results_locked

### E2E Tests Required
- Complete assessment flow with paywall
- Stripe checkout → Webhook → Dashboard update
