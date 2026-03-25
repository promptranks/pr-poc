# Sprint 4 Handoff: Auth + Badge Claim

**Created**: 2026-03-25
**Status**: Ready to start
**Objective**: Users register at claim time, badge generated with SVG and verification URL.

## Required Reading

1. **PRD**: `PRD.md` — Section 3.3 (Claim), 3.4 (Badge Page), 3.5 (Verification), 4 (API — auth, claim, verify), 6 (Sprint 4)
2. **CLAUDE.md**: `CLAUDE.md` — Bcrypt rules, matrix theme
3. **Iteration Plan**: `.sprint/iteration-plan.md` — Sprint 4 details
4. **Sprint 3 Report**: `.sprint/sprint-3-completion-report.md`

## Context: What Already Exists

### Backend (apps/api/)
- `app/routers/assessment.py` — Full assessment flow: start, KBA submit, PPA tasks/execute/submit-best, PSV submit, violations, results
- `app/routers/auth.py` — Stub endpoints (register, login)
- `app/routers/badges.py` — Stub endpoint (verify)
- `app/services/scoring.py` — Final score, level assignment, pillar aggregation
- `app/services/psv_engine.py` — PSV judging
- `app/services/llm_client.py` — LiteLLM multi-provider wrapper
- `app/models/user.py` — User model (email, name, password_hash)
- `app/models/badge.py` — Badge model (level, level_name, final_score, pillar_scores, badge_svg, verification_url)
- `app/models/assessment.py` — Assessment with final_score, level, status=completed
- `tests/` — 74 tests (KBA, PPA, Scoring)

### Frontend (apps/web/)
- `src/pages/Results.tsx` — Shows final score, level, radar chart. Needs claim form addition.
- `src/pages/Assessment.tsx` — Full flow: KBA → PPA → Results
- `src/components/RadarChart.tsx` — SVG radar chart

### Key Security Rules
- **Bcrypt for passwords** (not Passlib), 72-byte limit validation
- **SHA256 for tokens** (JWT refresh tokens, session tokens)
- **python-jose** already in requirements for JWT

## Task List

| ID | Task | Target Files | Priority |
|----|------|-------------|----------|
| S4-T1 | Auth register endpoint | `apps/api/app/routers/auth.py`, `apps/api/app/services/auth_service.py` | CRITICAL |
| S4-T2 | Auth login endpoint + JWT | `apps/api/app/routers/auth.py`, `apps/api/app/services/auth_service.py` | CRITICAL |
| S4-T3 | JWT middleware | `apps/api/app/middleware/auth.py` | HIGH |
| S4-T4 | Claim endpoint | `apps/api/app/routers/assessment.py` | CRITICAL |
| S4-T5 | Badge SVG generation | `apps/api/app/services/badge_service.py` | HIGH |
| S4-T6 | Badge verify endpoint | `apps/api/app/routers/badges.py` | HIGH |
| S4-T7 | Frontend claim form on Results page | `apps/web/src/pages/Results.tsx` | HIGH |
| S4-T8 | Frontend Badge page | `apps/web/src/pages/Badge.tsx` | HIGH |
| S4-T9 | Frontend Verify page | `apps/web/src/pages/Verify.tsx` | MEDIUM |
| S4-T10 | Unit tests | `apps/api/tests/test_auth.py`, `apps/api/tests/test_badge.py` | CRITICAL |

## Key Constraints
- Auth-last: assessment works without login, register happens at claim time
- Bcrypt for passwords (direct bcrypt, NOT Passlib)
- JWT tokens signed with SECRET_KEY
- Badge SVG must contain: level, score, radar chart, date, mode label
- Verification endpoint is public (no auth required)
- Duplicate claim returns 409
- Existing user can login and claim

## Acceptance Criteria
- [ ] Complete assessment → click Claim → register → badge issued
- [ ] Badge SVG contains: level, score, radar chart, date, mode label
- [ ] `GET /badges/verify/{id}` returns badge data (public)
- [ ] Already registered user can login and claim
- [ ] Can't claim same assessment twice (409)
- [ ] Passwords hashed with bcrypt
- [ ] JWT tokens work for protected endpoints
- [ ] All unit tests pass
- [ ] CI green
