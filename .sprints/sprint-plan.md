# PromptRanks Webapp v1 - Sprint Plan

**PRD:** Webapp-v1-PRD.md
**Codebase:** /Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps
**Status:** Initialized
**Created:** 2026-03-28

---

## Overview

Transform PromptRanks from open assessment tool to freemium SaaS platform with:
- OAuth + Magic Link authentication
- Tier-based usage limits (Free/Premium/Enterprise)
- Personal dashboard with analytics
- Stripe payment integration
- Industry/role targeting for premium users

---

## Existing Architecture

**Frontend:** React + TypeScript (Vite) at prk.promptranks.org
**Backend:** FastAPI + PostgreSQL + Redis at api.promptranks.org
**Current Flow:** Landing → Assessment (KBA/PPA/PSV) → Results → Badge

**Existing Models:**
- user.py - Basic auth with subscription_tier field
- assessment.py - Has industry_id/role_id but unused in UI
- taxonomy.py - Industries and roles exist
- question.py, badge.py, content_pack.py, psv_sample.py

---

## Sprint Breakdown

### Sprint 1: Auth Foundation
**Duration:** 5 days
**Goal:** OAuth + Magic Link authentication

**Database Changes:**
- oauth_accounts table
- magic_links table
- users.avatar_url, users.oauth_provider columns

**Backend Tasks:**
- Google OAuth endpoints
- GitHub OAuth endpoints
- Magic link generation/verification
- Email service integration

**Frontend Tasks:**
- AuthModal component
- Landing page auth links
- Auth context provider

---

### Sprint 2: Usage Tracking & Paywall
**Duration:** 5 days
**Goal:** Tier-based limits and results paywall

**Database Changes:**
- user_usage table
- assessments.results_locked column

**Backend Tasks:**
- Usage tracking service
- Check limit endpoint
- Usage reset logic

**Frontend Tasks:**
- PaywallModal component
- Results page lock check
- Usage badge in header

---

### Sprint 3: Dashboard & History
**Duration:** 5 days
**Goal:** Personal dashboard with assessment history

**Backend Tasks:**
- Dashboard data endpoint
- Assessment list endpoint
- Assessment details endpoint

**Frontend Tasks:**
- Dashboard page
- AssessmentHistoryTable component
- Navigation updates

---

### Sprint 4: Analytics & Recommendations
**Duration:** 5 days
**Goal:** Premium analytics features

**Database Changes:**
- learning_resources table

**Backend Tasks:**
- Analytics calculation service
- Recommendations algorithm
- Learning resources seeding

**Frontend Tasks:**
- AnalyticsCharts component
- Score trends visualization
- Recommendations section

---

### Sprint 5: Stripe Integration
**Duration:** 5 days
**Goal:** Payment processing

**Database Changes:**
- stripe_customers table

**Backend Tasks:**
- Stripe checkout flow
- Webhook handlers
- Portal session creation

**Frontend Tasks:**
- UpgradeModal component
- Pricing page
- Subscription management UI

---

### Sprint 6: Industry/Role & Polish
**Duration:** 5 days
**Goal:** Complete feature set and polish

**Backend Tasks:**
- Email templates
- Email sending service
- Analytics tracking

**Frontend Tasks:**
- Industry/role selectors
- Email notifications
- Mobile responsive
- E2E testing

---

## Success Metrics

**Launch (Month 1):**
- 1,000 users
- 10% conversion rate
- 50 paying subscribers
- $950 MRR

**Growth (Month 3):**
- 5,000 users
- 15% conversion rate
- 300 subscribers
- $5,700 MRR
