# Codebase Analysis: Usage Limits & Paywall System

## Architecture Overview

The backend uses a FastAPI + SQLAlchemy async architecture with PostgreSQL for persistence and Redis for caching/leaderboards. The system implements a three-tier subscription model (free, premium, enterprise) with usage tracking and Stripe payment integration.

### Tech Stack
- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL (asyncpg driver)
- **Cache**: Redis
- **Payments**: Stripe
- **Auth**: JWT (HTTPBearer)
- **Testing**: pytest + pytest-asyncio

## Current State

### 1. Subscription Tiers

Defined in `User` model (`app/models/user.py`):
```python
subscription_tier = Column(String, default="free")  # free, pro, enterprise
subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
```

**Tier Limits** (from `UsageService`):
- **Free**: 0 full assessments/month (results locked)
- **Premium**: 3 full assessments/month
- **Enterprise**: 999 full assessments/month (effectively unlimited)

### 2. Usage Tracking System

**Model**: `UserUsage` (`app/models/user_usage.py`)
```python
user_id: UUID (FK to users)
period_start: Date (1st of month)
period_end: Date (last day of month)
full_assessments_used: Integer
full_assessments_limit: Integer
```

**Service**: `UsageService` (`app/services/usage_service.py`)
- Monthly billing periods (calendar month)
- Auto-creates usage records on first access
- Tracks only full assessments (quick assessments are unlimited)
- No automatic reset mechanism (relies on period_start matching)

**Key Methods**:
- `get_tier_limit(tier)`: Returns limit for tier
- `get_current_period()`: Returns (period_start, period_end) tuple
- `get_or_create_usage(user_id, tier, db)`: Fetches or creates usage record
- `check_limit(user_id, tier, db)`: Returns (can_access, used, limit)
- `increment_usage(user_id, tier, db)`: Increments usage counter

### 3. Assessment Flow with Gating

**Endpoint**: `POST /assessments/start` (`app/routers/assessment.py:234`)

**Gating Logic**:
1. **Premium Industry/Role Check** (line 259-266):
   - Premium industries: healthcare, finance, legal, enterprise
   - Premium roles (full mode only): architect, director, vp, cto, ciso
   - Returns 402 if user not premium/enterprise

2. **Usage Limit Check** (line 269-286):
   - Only for full assessments
   - Premium users: check limit, increment if allowed, 403 if exceeded
   - Free users: allow but set `results_locked=True`
   - Enterprise users: no limit
   - Anonymous users: allow but set `results_locked=True`

3. **Results Locking**:
   - `results_locked` flag on Assessment model
   - Set to `True` for free/anonymous users on full assessments
   - Returned in results response but not enforced server-side

### 4. Stripe Integration

**Service**: `StripeService` (`app/services/stripe_service.py`)

**Implemented Features**:
- Checkout session creation (monthly/annual plans)
- Customer portal session creation
- Webhook handlers:
  - `checkout.session.completed`: Upgrades user to premium
  - `customer.subscription.deleted`: Downgrades user to free

**Models**:
- `StripeCustomer`: Links user_id to stripe_customer_id and stripe_subscription_id

**Environment Variables**:
- `STRIPE_SECRET_KEY`
- `STRIPE_PREMIUM_PRICE_ID` (monthly)
- `STRIPE_YEARLY_PRICE_ID` (annual)
- `STRIPE_WEBHOOK_SECRET`
- `FRONTEND_URL`

**Payment Router**: `app/routers/payments.py`
- `POST /payments/create-checkout`: Creates checkout session
- `POST /payments/create-portal`: Creates billing portal session
- `GET /payments/subscription`: Retrieves subscription details
- `POST /payments/webhook`: Stripe webhook endpoint
- `POST /payments/sync-subscription`: Manual sync for testing

### 5. Database Schema

**Core Tables**:
```
users
├── id (UUID, PK)
├── email (String, unique)
├── subscription_tier (String: free/premium/enterprise)
├── subscription_expires_at (DateTime, nullable)
└── ... (auth fields)

user_usage
├── id (UUID, PK)
├── user_id (UUID, FK → users.id, CASCADE)
├── period_start (Date)
├── period_end (Date)
├── full_assessments_used (Integer)
└── full_assessments_limit (Integer)

stripe_customers
├── id (UUID, PK)
├── user_id (UUID, FK → users.id, unique)
├── stripe_customer_id (String, unique)
└── stripe_subscription_id (String, nullable)

assessments
├── id (UUID, PK)
├── user_id (UUID, FK → users.id, nullable)
├── mode (Enum: quick/full)
├── status (Enum: in_progress/completed/voided/expired)
├── results_locked (Boolean, default=False)
└── ... (scores, responses, timestamps)
```

## Gaps & Missing Features

### 1. Webhook Handlers
**Missing**:
- `customer.subscription.updated`: Handle plan changes, renewals
- `invoice.payment_failed`: Handle failed payments
- `invoice.payment_succeeded`: Confirm successful payments
- `customer.subscription.trial_will_end`: Trial expiration warnings

### 2. Subscription Management
**Missing**:
- Subscription expiration enforcement
- Grace period handling
- Automatic downgrade on expiration
- Prorated upgrades/downgrades
- Trial period support

### 3. Usage Tracking
**Limitations**:
- No automatic period rollover
- No usage history/analytics
- No usage warnings (e.g., "2/3 assessments used")
- No usage reset job for new periods

### 4. Results Locking
**Current State**:
- Flag is set but not enforced
- Frontend must implement the actual blocking
- No server-side validation on results endpoint

### 5. Error Recovery
**Missing**:
- Webhook retry logic
- Failed payment recovery flow
- Subscription sync repair tools
- Usage counter correction mechanisms

## Data Flow Diagrams

### Assessment Start Flow (Full Mode)
```
User → POST /assessments/start
  ↓
Check pending assessment
  ↓
Premium gating check (industry/role)
  ↓
Get current user tier
  ↓
If premium: check_limit() → increment_usage()
If free: set results_locked=True
If enterprise: no limit
  ↓
Create Assessment record
  ↓
Return questions
```

### Stripe Checkout Flow
```
User → POST /payments/create-checkout
  ↓
StripeService.create_checkout_session()
  ↓
Get/create StripeCustomer
  ↓
Create Stripe checkout session
  ↓
Return checkout_url
  ↓
User completes payment on Stripe
  ↓
Stripe → POST /payments/webhook (checkout.session.completed)
  ↓
StripeService.handle_checkout_completed()
  ↓
Update user.subscription_tier = "premium"
Update stripe_customer.stripe_subscription_id
  ↓
Send upgrade email
```

### Usage Check Flow
```
UsageService.check_limit(user_id, tier, db)
  ↓
get_current_period() → (period_start, period_end)
  ↓
get_or_create_usage(user_id, tier, db)
  ↓
Query UserUsage WHERE user_id AND period_start
  ↓
If not found: create new record with limit from tier
  ↓
Return (can_access, used, limit)
  where can_access = (used < limit)
```

## Configuration

**Settings** (`app/config.py`):
- `deployment_mode`: "self_hosted" | "saas"
- `database_url`: PostgreSQL connection string
- `redis_url`: Redis connection string
- `secret_key`: JWT signing key
- `access_token_expire_minutes`: Token TTL (default: 60)

**Assessment Timers**:
- `quick_assessment_time_limit`: 900s (15 min)
- `full_kba_time_limit`: 900s (15 min)
- `full_ppa_time_limit`: 1800s (30 min)

## Dependencies

**External Services**:
- Stripe API (payments)
- Email service (upgrade notifications)
- Redis (leaderboards, caching)
- PostgreSQL (persistence)

**Python Packages** (key):
- fastapi
- sqlalchemy[asyncio]
- asyncpg
- stripe
- pydantic
- python-jose (JWT)
- passlib (password hashing)
