# Sprint 4 Handoff: Stripe Integration

**Created**: 2026-03-29
**Status**: Ready to start
**Objective**: Implement payment processing and subscription management

## Required Reading

Before starting, read these documents:
1. **PRD**: `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/Webapp-v1-PRD.md` — Focus on: Section 4 (Payment Integration)
2. **Iteration Plan**: `.sprint/iteration-plan.md`
3. **Sprint 3 Report**: `.sprint/sprint-3-completion-report.md` — Premium features now available
4. **Design Decisions**: `.sprint/design-decisions.md`

## Design Context

**From design-decisions.md:**
- PostgreSQL with async SQLAlchemy
- UUID primary keys
- React + TypeScript frontend
- Stripe for payment processing

**Sprint Contracts:**
- **Input from Sprint 3**: Dashboard page, premium feature gates, analytics section
- **Output for Sprint 5**: Stripe checkout flow, subscription management, webhook handlers

## Task List

| ID | Task | Target Files | Priority |
|----|------|-------------|----------|
| S4-T1 | Create stripe_customers table | `apps/api/migrations/007_stripe_customers.sql` | CRITICAL |
| S4-T2 | Stripe service | `apps/api/app/services/stripe_service.py` | CRITICAL |
| S4-T3 | Payment endpoints | `apps/api/app/routers/payments.py` | CRITICAL |
| S4-T4 | Webhook handler | `apps/api/app/routers/payments.py` | CRITICAL |
| S4-T5 | Pricing page | `apps/web/src/pages/Pricing.tsx` | HIGH |
| S4-T6 | Upgrade modal | `apps/web/src/components/UpgradeModal.tsx` | HIGH |
| S4-T7 | Subscription card | `apps/web/src/components/SubscriptionCard.tsx` | HIGH |
| S4-T8 | Update dashboard | `apps/web/src/pages/Dashboard.tsx` | HIGH |
| S4-T9 | Unit tests | `apps/api/tests/test_payments.py` | CRITICAL |

## Detailed Instructions

### S4-T1: Stripe Customers Table

Create migration with stripe_customer_id and stripe_subscription_id columns.

### S4-T2: Stripe Service

Create service with methods:
- create_checkout_session(user_id, plan)
- create_portal_session(customer_id)
- handle_checkout_completed(session)
- handle_subscription_updated(subscription)
- handle_subscription_deleted(subscription)

### S4-T3: Payment Endpoints

- POST /payments/create-checkout
- POST /payments/create-portal
- GET /payments/subscription

### S4-T4: Webhook Handler

- POST /payments/webhook
- Verify Stripe signature
- Handle events: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted

### S4-T5-T8: Frontend Components

Create pricing page, upgrade modal, subscription management card, and integrate into dashboard.

### S4-T9: Unit Tests

Test scenarios:
- Checkout session creation
- Webhook signature verification
- Subscription activation
- Subscription cancellation
- Portal session creation

## Key Constraints

- Use Stripe test mode for development
- Verify webhook signatures
- Update user subscription_tier on successful payment
- Handle failed payments gracefully
- Redirect to dashboard after successful checkout

## Required Test Scenarios

1. Create checkout session for premium plan
2. Webhook activates subscription on payment
3. Subscription cancellation downgrades to free
4. Portal session created for existing customer
5. Invalid webhook signature rejected

## After Completion

1. Update `.sprint/iteration-plan.md` — Mark Sprint 4 as Completed
2. Create `.sprint/sprint-4-completion-report.md`
3. Create `.sprint/handoff-sprint-5.md` for Industry/Role & Polish
