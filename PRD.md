# PromptRanks PoC — Product Requirements Document (PRD)

**Version**: 1.0
**Date**: 2026-03-22
**Author**: Adam CHIN
**Status**: Draft

---

## 1. Product Overview

PromptRanks is an open-source platform that assesses AI prompting skill using the PECAM framework. Users take an assessment, receive a score and level (L1–L5), and earn a shareable badge.

**Core principle: Assess first, register later.** No account needed to start. Users only register when they want to claim their badge.

---

## 2. User Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        LANDING PAGE                              │
│  "Measure your AI prompting skill"                               │
│  [Quick Assessment - 15 min]  [Full Assessment - ~60 min]        │
│  Optional: select industry + role                                │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
        ┌──────▼──────┐           ┌───────▼───────┐
        │   QUICK     │           │    FULL       │
        │  ASSESSMENT │           │  ASSESSMENT   │
        │  (locked)   │           │  (locked)     │
        │             │           │               │
        │ KBA: 10 Q   │           │ KBA: 20 Q    │
        │ (5 min)     │           │ (15 min)     │
        │      │      │           │      │       │
        │ PPA: 1 task │           │ PPA: 3-5     │
        │ (8 min)     │           │ tasks (30min)│
        │             │           │      │       │
        │             │           │ PSV: portfolio│
        │             │           │ (15 min)     │
        └──────┬──────┘           └───────┬──────┘
               │                          │
        ┌──────▼──────────────────────────▼──────┐
        │            RESULTS PAGE                 │
        │  Score: 78/100  Level: L3 Proficient    │
        │  PECAM Radar Chart                      │
        │  Per-pillar breakdown                   │
        │                                         │
        │  ┌─────────────────────────────────┐   │
        │  │ Want to keep your badge?         │   │
        │  │ [Register with email to claim]   │   │
        │  └─────────────────────────────────┘   │
        │                                         │
        │  (Quick only) "Upgrade to Full →"       │
        └──────────────┬─────────────────────────┘
                       │
                ┌──────▼──────┐
                │  CLAIM PAGE │
                │  Email +    │
                │  Password   │
                │  → Badge    │
                │  issued     │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │ BADGE PAGE  │
                │ Share on    │
                │ LinkedIn    │
                │ Copy URL    │
                │ Download    │
                │ SVG         │
                └─────────────┘
```

---

## 3. Screens & Pages

### 3.1 Landing Page (`/`)

**Purpose:** Entry point. Choose assessment mode.

**Elements:**
- Hero: "Measure your AI prompting skill in 15 minutes"
- Two CTA buttons: "Quick Assessment (15 min)" / "Full Assessment (~60 min)"
- Optional dropdowns: Industry, Role (pre-populated lists)
- Brief explanation of PECAM framework (5 pillar icons)
- "How it works" section (3 steps: Assess → Score → Share)
- Footer: GitHub link, methodology link, "Open Source" badge

**Actions:**
- Click Quick → `POST /assessments/start {mode: "quick"}` → redirect to `/assessment/{id}`
- Click Full → `POST /assessments/start {mode: "full"}` → redirect to `/assessment/{id}`

### 3.2 Assessment Page (`/assessment/{id}`)

**Purpose:** Locked assessment environment. No navigation allowed.

**Global elements:**
- Timer (countdown, top-right)
- Progress indicator (KBA → PPA → PSV)
- Tab-lock warning overlay (shown on focus loss)
- No navbar, no links, no back button

#### 3.2.1 KBA Phase

**Elements:**
- Question card: question text, 4 option buttons (MCQ)
- Question counter: "3 / 10"
- Pillar indicator badge (P, E, C, M, A)
- "Next" button (enabled after selection)
- No "Back" button (can't change previous answers)

**Behavior:**
- Questions served one at a time
- Selection highlights the chosen option
- Click "Next" → submits answer, loads next question
- After last question → auto-transition to PPA phase
- Timer continues across phases

#### 3.2.2 PPA Phase

**Elements:**
- Task brief panel (left/top): title, instructions, input data
- Prompt editor (center): textarea with monospace font, line numbers
- "Execute" button
- Output panel (right/bottom): LLM response display
- Attempt counter: "Attempt 1 of 2"
- "Submit Best Attempt" button (after at least 1 execution)

**Behavior:**
- User reads brief, writes prompt in editor
- Click "Execute" → `POST /assessments/{id}/ppa/execute` → shows LLM output
- User can edit prompt and re-execute (up to max_attempts)
- Click "Submit Best Attempt" → moves to next task (or PSV/results)
- Each execution shows the raw output, NOT the judge scores (scores revealed at end)

#### 3.2.3 PSV Phase (Full only)

**Elements:**
- Text area: "Paste your best prompt"
- Text area: "Paste the output it produced"
- Text area: "Brief context (what was the task?)"
- "Submit Portfolio" button

**Behavior:**
- User submits one prompt-output pair
- `POST /assessments/{id}/psv/submit`
- Transition to results

### 3.3 Results Page (`/results/{id}`)

**Purpose:** Show assessment outcome and motivate badge claim.

**Elements:**
- Score display: large number (e.g., "78")
- Level badge: "L3 Proficient" (with color)
- Label: "Estimated" (quick) or "Certified" (full)
- PECAM radar chart (5 axes)
- Per-pillar score breakdown table
- Score formula explanation: "KBA: 80 × 0.40 + PPA: 76 × 0.60 = 78"
- KBA detail: correct/total per pillar
- PPA detail: per-task scores with 5-dimension breakdown

**Quick-specific:**
- Faded/incomplete radar chart (pillars not fully tested)
- "Your weakest area: Meta-Cognition — test it in the Full Assessment"
- CTA: "Take Full Assessment for your Certified badge →"

**Claim section:**
- "Register to claim your badge and share it"
- Email input + password input + "Claim Badge" button
- Or "Login" link if already registered

### 3.4 Badge Page (`/badge/{badge_id}`)

**Purpose:** Display and share the earned badge.

**Elements:**
- SVG badge (large, centered)
- Level, score, date, mode
- PECAM radar chart
- Verification URL (copyable)
- Share buttons: "Add to LinkedIn", "Copy Link", "Download SVG", "Tweet"
- QR code to verification URL

### 3.5 Verification Page (`/verify/{badge_id}`)

**Purpose:** Public page for anyone to verify a badge. No auth required.

**Elements:**
- Badge SVG
- "This badge is valid" / "Badge not found"
- Level, score, date, issuer (PromptRanks)
- PECAM radar chart
- Link back to promptranks.org

---

## 4. API Endpoints

### No Auth Required

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| POST | `/assessments/start` | Start assessment (returns questions + session) |
| POST | `/assessments/{id}/kba/submit` | Submit KBA answers |
| POST | `/assessments/{id}/ppa/execute` | Execute prompt in sandbox |
| POST | `/assessments/{id}/psv/submit` | Submit portfolio (full only) |
| GET | `/assessments/{id}/results` | Get results |
| POST | `/assessments/{id}/violation` | Report anti-cheat violation |
| GET | `/badges/verify/{badge_id}` | Public badge verification |

### Auth Required

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login |
| POST | `/assessments/{id}/claim` | Claim badge (register + link) |
| GET | `/users/me` | Get user profile |
| GET | `/users/me/badges` | List user's badges |

---

## 5. Data Models

### User
```
id: UUID (PK)
email: string (unique)
name: string
password_hash: string (bcrypt)
is_active: boolean
created_at: timestamp
```

### Assessment
```
id: UUID (PK)
user_id: UUID (FK, nullable — set on claim)
mode: "quick" | "full"
status: "in_progress" | "completed" | "voided" | "expired"
industry: string (optional)
role: string (optional)
kba_score: float
kba_responses: JSON
ppa_score: float
ppa_responses: JSON
psv_score: float (full only)
psv_submission: JSON (full only)
final_score: float
level: 1-5
pillar_scores: JSON {P, E, C, M, A}
violations: int
violation_log: JSON
started_at: timestamp
completed_at: timestamp
expires_at: timestamp
```

### Badge
```
id: UUID (PK)
user_id: UUID (FK)
assessment_id: UUID (FK, unique)
mode: "quick" | "full"
level: 1-5
level_name: string
final_score: float
pillar_scores: JSON
badge_svg: text
verification_url: string
issued_at: timestamp
```

---

## 6. Sprint Plan

Based on sprint-flow methodology. Each sprint is 2-4 hours of AI work, produces testable output.

### Sprint 0: Foundation (already done)
- Project skeleton, Docker Compose, CI, docs, content YAML
- **Deliverable**: `docker compose up` works, CI green
- **Status**: COMPLETE

### Sprint 1: Assessment Session + KBA Engine
**Goal**: User can start an assessment and complete KBA questions.

**Tasks:**
1. Database connection (async SQLAlchemy + PostgreSQL)
2. Assessment session creation (`POST /assessments/start`)
   - Generate session ID, set timer, select questions
   - Quick: 10 questions (2 per pillar, 1 easy + 1 medium)
   - Full: 20 questions (4 per pillar, mixed difficulty)
3. KBA question serving (return questions without correct answers)
4. KBA answer submission + scoring (`POST /assessments/{id}/kba/submit`)
5. Per-pillar score breakdown
6. Seed script inserts questions into DB
7. Frontend: Assessment page with KBA question cards, timer, progress

**Acceptance criteria:**
- Start quick assessment → receive 10 questions (2 per pillar)
- Submit answers → receive KBA score + pillar breakdown
- Timer counts down from 15 min (quick) / 15 min KBA phase (full)
- Questions don't include correct answers in response
- Seed script loads all 30 questions into DB

**Tests:**
- `test_start_assessment` — creates session, returns questions
- `test_kba_scoring` — correct score calculation
- `test_kba_pillar_balance` — 2 questions per pillar in quick mode
- `test_timer_expiry` — expired session returns error

### Sprint 2: PPA Engine (LLM Execution + Judging)
**Goal**: User can write prompts, execute them, and get judged.

**Tasks:**
1. LLM client service (Anthropic SDK wrapper)
2. PPA task serving (load from DB, return brief + input_data)
3. Prompt execution endpoint (`POST /assessments/{id}/ppa/execute`)
   - Send user prompt + task input to Claude Sonnet
   - Return LLM output to user
4. LLM judge service
   - Send output + rubric to Claude Opus
   - Parse structured JSON scores (5 dimensions)
5. Attempt tracking (max 2 for quick, max 3 for full)
6. Best attempt selection and scoring
7. Frontend: PPA page with editor, execute button, output panel

**Acceptance criteria:**
- Execute prompt → see LLM output within 10 seconds
- Submit best attempt → judge returns 5-dimension scores
- Attempt counter enforced (can't exceed max)
- Judge output is valid JSON with all 5 dimensions
- Score is deterministic within ±5 points across runs

**Tests:**
- `test_ppa_execute` — prompt execution returns output
- `test_ppa_judge` — judge returns valid structured scores
- `test_ppa_attempts` — max attempts enforced
- `test_ppa_judge_consistency` — 3 runs, variance < 10 points

### Sprint 3: Scoring + Results + Anti-Cheat
**Goal**: Complete assessment flow with final score, level, and results page.

**Tasks:**
1. Scoring service
   - Quick: KBA×0.40 + PPA×0.60
   - Full: KBA×0.30 + PPA×0.60 + PSV×0.10
2. Level assignment (L1–L5 thresholds)
3. PECAM pillar score aggregation
4. Results endpoint (`GET /assessments/{id}/results`)
5. Anti-cheat middleware
   - Violation reporting endpoint
   - Tab-lock detection (frontend)
   - Timer enforcement (backend rejects late submissions)
   - 3 violations → void session
6. PSV portfolio submission (full mode)
   - LLM judge scores portfolio entry
7. Frontend: Results page with score, level, radar chart, pillar breakdown

**Acceptance criteria:**
- Complete quick assessment → see final score + level
- Score formula matches: KBA×0.40 + PPA×0.60
- PECAM radar chart shows per-pillar scores
- Tab switch triggers warning, 3 violations voids session
- Expired timer rejects further submissions
- Full mode: PSV submission scored and included in final score

**Tests:**
- `test_scoring_quick` — formula verification
- `test_scoring_full` — formula with PSV
- `test_level_assignment` — boundary cases (49→L1, 50→L2, etc.)
- `test_anti_cheat_violation` — 3 violations void session
- `test_timer_enforcement` — late submission rejected

### Sprint 4: Auth + Badge Claim
**Goal**: Users can register, claim their badge, and get a verification URL.

**Tasks:**
1. User registration (email + password, bcrypt)
2. Login (JWT tokens)
3. Claim endpoint (`POST /assessments/{id}/claim`)
   - Creates user (or links existing)
   - Links assessment to user
   - Generates badge
4. Badge service
   - SVG generation with level, score, PECAM radar chart
   - Verification URL generation
5. Badge verification endpoint (`GET /badges/verify/{badge_id}`)
6. Frontend: Claim form on results page, badge display page

**Acceptance criteria:**
- Complete assessment → click "Claim" → register → badge issued
- Badge SVG contains: level, score, radar chart, date
- Verification URL returns badge data (public, no auth)
- Already registered user can login and claim
- Badge page has share buttons (copy URL, download SVG)

**Tests:**
- `test_register` — creates user with bcrypt password
- `test_login` — returns valid JWT
- `test_claim_badge` — links assessment to user, generates badge
- `test_verify_badge` — public endpoint returns badge data
- `test_duplicate_claim` — can't claim same assessment twice

### Sprint 5: Polish + Release v0.1.0
**Goal**: Production-ready PoC with documentation and first release.

**Tasks:**
1. Landing page polish (responsive, animations)
2. Assessment UX polish (transitions, loading states, error handling)
3. Results page polish (animated score reveal, radar chart animation)
4. Quick → Full conversion CTA
5. Error handling (network errors, LLM failures, timeout recovery)
6. Rate limiting (Redis-based)
7. Update README with screenshots
8. Update CHANGELOG
9. Tag v0.1.0, create GitHub Release
10. Create 5 "good first issues" for community

**Acceptance criteria:**
- Full Quick Assessment flow works end-to-end in under 15 min
- Full Assessment flow works end-to-end in under 60 min
- All pages responsive (mobile + desktop)
- Error states handled gracefully
- CI green, all tests pass
- README has screenshots and clear quickstart
- GitHub Release published with changelog

---

## 7. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Assessment start to first question | < 2 seconds |
| PPA prompt execution | < 15 seconds |
| LLM judge scoring | < 10 seconds |
| Badge generation | < 3 seconds |
| Concurrent assessments | 10+ simultaneous |
| Self-hosting | Single `docker compose up` |
| Browser support | Chrome, Firefox, Safari, Edge (latest) |
| Mobile | Responsive (assessment works on tablet, not phone) |

---

## 8. Out of Scope (v0.1.0)

- OAuth / SSO login
- Premium modules
- Leaderboard
- Peer calibration (PSV Phase 2)
- Multi-language support
- Adaptive difficulty
- Admin dashboard
- Analytics / tracking
- Email notifications
- Payment processing

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Quick Assessment completion rate | > 80% of starts |
| Full Assessment completion rate | > 60% of starts |
| Quick → Full conversion | > 20% |
| Badge claim rate | > 50% of completions |
| LLM judge consistency | < 10 point variance |
| Self-host success rate | > 90% (docker compose up works) |
