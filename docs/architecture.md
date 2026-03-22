# Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────┐
│                        Client                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  React SPA (Vite + TypeScript)                      │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │ │
│  │  │ Landing  │ │Assessment│ │ Results  │           │ │
│  │  │ (mode    │ │ (locked  │ │ (badge + │           │ │
│  │  │ select)  │ │ page)    │ │ claim)   │           │ │
│  │  └──────────┘ └──────────┘ └──────────┘           │ │
│  │       │            │  ▲          │                  │ │
│  │       │  TabLock    │  │ Timer    │                  │ │
│  └───────┼────────────┼──┼──────────┼──────────────────┘ │
└──────────┼────────────┼──┼──────────┼────────────────────┘
           │            │  │          │
           ▼            ▼  │          ▼
┌──────────────────────────────────────────────────────────┐
│                     FastAPI Backend                        │
│                                                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │
│  │ Assessment │  │ KBA Engine │  │ PPA Engine          │ │
│  │ Router     │──│            │  │ ┌────────────────┐  │ │
│  │            │  │ Question   │  │ │ LLM Executor   │  │ │
│  │ /start     │  │ Selection  │  │ │ (Claude Sonnet)│  │ │
│  │ /kba/submit│  │ Scoring    │  │ ├────────────────┤  │ │
│  │ /ppa/exec  │  └────────────┘  │ │ LLM Judge      │  │ │
│  │ /psv/submit│                   │ │ (Claude Opus)  │  │ │
│  │ /results   │  ┌────────────┐  │ └────────────────┘  │ │
│  │ /claim     │  │ Badge      │  └────────────────────┘ │
│  └────────────┘  │ Service    │                          │
│                   │ SVG gen   │  ┌────────────────────┐ │
│  ┌────────────┐  │ Verify    │  │ Anti-Cheat         │ │
│  │ Auth       │  └────────────┘  │ Middleware          │ │
│  │ Router     │                   │ Session validation │ │
│  │ /register  │  ┌────────────┐  │ Timer enforcement  │ │
│  │ /login     │  │ Scoring    │  │ Violation tracking │ │
│  └────────────┘  │ Service    │  └────────────────────┘ │
│                   └────────────┘                          │
└──────────┬───────────────────────────────┬───────────────┘
           │                               │
           ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│  PostgreSQL 16   │            │    Redis 7       │
│                  │            │                  │
│  users           │            │  Sessions        │
│  questions       │            │  Rate limits     │
│  tasks           │            │  Assessment      │
│  assessments     │            │  state cache     │
│  badges          │            │                  │
└──────────────────┘            └──────────────────┘
```

## User Flow (Auth-Last)

```
1. User arrives at landing page
2. Selects Quick (15 min) or Full (~60 min)
3. Selects industry + role (optional)
4. Assessment starts — page locks (no tab switching)
   a. KBA: answer questions
   b. PPA: write prompts, execute, see results
   c. PSV: submit portfolio (full only)
5. Results page: score, level, PECAM radar chart
6. To claim badge: register with email + password
7. Badge issued with verification URL
8. Share on LinkedIn / social media
```

Key design: **No registration required to take the assessment.** Users only register when they want to claim and share their badge. This minimizes friction and maximizes completion rates.

## Data Flow

### KBA
```
Client submits answers → API scores against DB → Returns pillar breakdown
```
No LLM calls. Pure database lookup.

### PPA
```
Client submits prompt
  → API sends to Claude Sonnet (executor) with task input_data
  → Output returned to client
  → Client can refine and resubmit (up to max_attempts)
  → Best attempt sent to Claude Opus (judge)
  → Judge returns 5-dimension scores as structured JSON
```

### Badge
```
Assessment completed → Scoring service calculates final score
  → Level assigned → SVG badge generated server-side
  → Badge stored in DB with verification UUID
  → Public /verify endpoint serves badge data
```

## Security Model

| Layer | Protection |
|-------|-----------|
| Transport | HTTPS (Cloudflare) |
| Auth | JWT tokens (bcrypt passwords, SHA256 token hashing) |
| Assessment | Tab-lock, timer, violation tracking, session binding |
| LLM | Token budget per request, sandboxed execution |
| API | Rate limiting (Redis), CORS, input validation |
| Data | Parameterized queries (SQLAlchemy), no raw SQL |

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Frontend | React 18 + TypeScript + Vite | Type safety, fast builds, large ecosystem |
| Backend | FastAPI (Python 3.12) | Async, great typing, natural fit for LLM work |
| Database | PostgreSQL 16 | Reliable, JSONB for flexible schemas |
| Cache | Redis 7 | Sessions, rate limiting, assessment state |
| LLM | Claude API (Anthropic SDK) | Best reasoning for judge tasks |
| Badge | Server-side SVG | No external dependency, fully self-hosted |
| Deploy | Docker Compose | Simple self-hosting, single command |
| CI | GitHub Actions | Standard for open source |
