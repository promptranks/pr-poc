# API Reference

Base URL: `http://localhost:8000`

## Health

### `GET /health`
Returns API status.

**Response:**
```json
{"status": "ok", "version": "0.1.0"}
```

---

## Authentication

### `POST /auth/register`
Register a new user. Called when user claims their badge after assessment.

**Body:**
```json
{
  "email": "user@example.com",
  "name": "Jane Doe",
  "password": "min8chars"
}
```

**Response:** `201` with user object (no password).

### `POST /auth/login`
Login and receive JWT token.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "min8chars"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Assessments

### `POST /assessments/start`
Start a new assessment session. No auth required — users assess first, register later.

**Body:**
```json
{
  "mode": "quick",
  "industry": "technology",
  "role": "backend-developer"
}
```

**Response:**
```json
{
  "assessment_id": "uuid",
  "mode": "quick",
  "kba_questions": [...],
  "expires_at": "2026-03-22T16:00:00Z"
}
```

### `POST /assessments/{id}/kba/submit`
Submit KBA answers.

**Body:**
```json
{
  "answers": [
    {"question_id": "P-001", "selected": 1},
    {"question_id": "E-002", "selected": 0}
  ]
}
```

**Response:**
```json
{
  "kba_score": 80.0,
  "correct": 8,
  "total": 10,
  "pillar_breakdown": {"P": 100, "E": 50, "C": 100, "M": 50, "A": 100}
}
```

### `POST /assessments/{id}/ppa/execute`
Execute a prompt in the PPA sandbox.

**Body:**
```json
{
  "task_id": "TASK-QUICK-001",
  "prompt": "Extract all action items from the meeting transcript as JSON...",
  "attempt": 1
}
```

**Response:**
```json
{
  "llm_output": "...",
  "judge_scores": {
    "accuracy": {"score": 85, "rationale": "..."},
    "completeness": {"score": 90, "rationale": "..."},
    "prompt_efficiency": {"score": 70, "rationale": "..."},
    "output_quality": {"score": 95, "rationale": "..."},
    "creativity": {"score": 60, "rationale": "..."},
    "task_score": 82.5
  },
  "attempts_remaining": 1
}
```

### `POST /assessments/{id}/psv/submit`
Submit portfolio entry (full assessment only).

**Body:**
```json
{
  "prompt": "My best prompt...",
  "output": "The output it produced...",
  "context": "What task this was for"
}
```

**Response:**
```json
{
  "psv_score": 75.0,
  "judge_scores": {...}
}
```

### `GET /assessments/{id}/results`
Get final results. Returns score, level, and badge.

**Response:**
```json
{
  "mode": "quick",
  "kba_score": 80.0,
  "ppa_score": 82.5,
  "psv_score": null,
  "final_score": 81.5,
  "level": 3,
  "level_name": "Proficient",
  "label": "Estimated",
  "pillar_scores": {"P": 85, "E": 78, "C": 90, "M": 65, "A": 72},
  "badge_id": "uuid",
  "claim_url": "/claim/uuid"
}
```

### `POST /assessments/{id}/claim`
Claim badge by registering or logging in. Links assessment to user account.

**Body:**
```json
{
  "email": "user@example.com",
  "name": "Jane Doe",
  "password": "min8chars"
}
```

**Response:**
```json
{
  "badge_id": "uuid",
  "verification_url": "https://promptranks.org/verify/uuid",
  "badge_svg": "..."
}
```

---

## Badges

### `GET /badges/verify/{badge_id}`
Public badge verification. No auth required.

**Response:**
```json
{
  "valid": true,
  "level": 3,
  "level_name": "Proficient",
  "mode": "quick",
  "label": "Estimated",
  "final_score": 81.5,
  "pillar_scores": {"P": 85, "E": 78, "C": 90, "M": 65, "A": 72},
  "issued_at": "2026-03-22T00:00:00Z",
  "badge_svg": "..."
}
```

---

## Anti-Cheat

### `POST /assessments/{id}/violation`
Report a client-side violation (tab switch, focus loss).

**Body:**
```json
{
  "type": "tab_switch",
  "timestamp": "2026-03-22T15:30:00Z"
}
```

**Response:**
```json
{
  "violations": 2,
  "warning": "Please stay on the assessment page. 3 violations will void your session.",
  "voided": false
}
```
