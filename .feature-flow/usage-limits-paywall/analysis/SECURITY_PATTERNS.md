# Security Patterns: Authentication, Authorization & Data Protection

## Authentication System

### 1. JWT Token-Based Authentication

**Implementation**: `app/middleware/auth.py`

**Token Structure**:
```python
payload = {
    "sub": str(user_id),  # Subject: user UUID
    "email": user_email,
    # exp, iat added by JWT library
}
```

**Token Lifecycle**:
- Created by `AuthService.create_access_token()`
- Expires after `access_token_expire_minutes` (default: 60)
- Validated by `decode_access_token()`
- Stored client-side (not server-side sessions)

### 2. Authentication Middleware

**Required Authentication**:
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Raises 401 if not authenticated."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_access_token(credentials.credentials)
    user_id = UUID(payload.get("sub"))
    
    # Load user from database
    user = await db.execute(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

**Optional Authentication**:
```python
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Returns User if authenticated, None otherwise. Never raises."""
    if credentials is None:
        return None
    
    try:
        # Attempt to decode and load user
        # Return None on any error
    except Exception:
        return None
```

**Usage Pattern**:
```python
# Require auth
@router.post("/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_user)
):
    # current_user is guaranteed to exist

# Optional auth
@router.post("/assessments/start")
async def start_assessment(
    current_user: User | None = Depends(get_current_user_optional)
):
    # current_user may be None (anonymous access)
    if current_user:
        tier = current_user.subscription_tier
    else:
        tier = "free"
```

### 3. Password Security

**Hashing**: Uses `passlib` (referenced but not shown)
- Passwords never stored in plaintext
- Hashed before database storage
- Verified via `verify_password(plain, hashed)`

**Password Requirements**:
```python
if len(body.password) < 8:
    raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
```

## Authorization Patterns

### 1. Subscription Tier Validation

**Pattern**: Check tier before granting access

**Example 1: Premium Industry/Role Gating**
```python
def _check_premium_required(industry: str | None, role: str | None, mode: str) -> bool:
    """Check if industry/role combination requires premium subscription."""
    premium_industries = ["healthcare", "finance", "legal", "enterprise"]
    if industry and industry.lower() in premium_industries:
        return True
    
    premium_roles = ["architect", "director", "vp", "cto", "ciso"]
    if mode == "full" and role and role.lower() in premium_roles:
        return True
    
    return False

# In endpoint
requires_premium = _check_premium_required(body.industry, body.role, body.mode)
if requires_premium:
    user_tier = current_user.subscription_tier if current_user else "free"
    if user_tier not in ("premium", "enterprise"):
        raise HTTPException(
            status_code=402,
            detail="Premium subscription required for this industry/role combination"
        )
```

**Example 2: Usage Limit Enforcement**
```python
if body.mode == "full":
    if current_user:
        tier = current_user.subscription_tier
        if tier == "premium":
            can_start, used, limit = await UsageService.check_limit(
                str(current_user.id), tier, db
            )
            if not can_start:
                raise HTTPException(
                    status_code=403,
                    detail=f"Assessment limit reached ({used}/{limit}). Upgrade to Enterprise for unlimited access."
                )
            await UsageService.increment_usage(str(current_user.id), tier, db)
```

**HTTP Status Codes**:
- `401 Unauthorized`: Not authenticated
- `402 Payment Required`: Premium subscription required
- `403 Forbidden`: Usage limit exceeded
- `404 Not Found`: Resource doesn't exist
- `409 Conflict`: Resource already exists

### 2. Resource Ownership Validation

**Pattern**: Verify user owns resource before access

**Example: Assessment Ownership**
```python
# Assessment can be owned by user or anonymous
assessment = await db.execute(select(Assessment).where(Assessment.id == aid))

# When claiming, link to authenticated user
if current_user:
    assessment.user_id = current_user.id
```

**Example: Stripe Customer Ownership**
```python
# Only allow user to access their own Stripe data
result = await db.execute(
    select(StripeCustomer).where(StripeCustomer.user_id == current_user.id)
)
stripe_customer = result.scalar_one_or_none()
```

### 3. Assessment State Validation

**Pattern**: Validate assessment status before operations

```python
async def _load_assessment(db: AsyncSession, assessment_id: str) -> Assessment:
    """Load an in-progress, non-expired assessment or raise HTTPException."""
    assessment = await db.execute(select(Assessment).where(Assessment.id == aid))
    
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status == AssessmentStatus.expired:
        raise HTTPException(status_code=400, detail="Assessment has expired")
    if assessment.status == AssessmentStatus.voided:
        raise HTTPException(status_code=400, detail="Assessment has been voided")
    if assessment.status == "completed":
        raise HTTPException(status_code=400, detail="Assessment already completed")
    
    # Check timer
    if check_timer_expired(assessment):
        await expire_assessment(db, assessment)
        raise HTTPException(status_code=400, detail="Assessment has expired")
    
    return assessment
```

### 4. Idempotency Checks

**Pattern**: Prevent duplicate operations

```python
# Check if already submitted
if assessment.kba_score is not None:
    raise HTTPException(status_code=400, detail="KBA already submitted for this assessment")

# Check if already claimed
existing_badge = await db.execute(select(Badge).where(Badge.assessment_id == aid))
if existing_badge.scalar_one_or_none() is not None:
    raise HTTPException(status_code=409, detail="Assessment already claimed")
```

## Data Protection

### 1. Sensitive Data Handling

**Never Expose**:
- Password hashes
- JWT secret keys
- Stripe secret keys
- Webhook secrets

**Conditionally Expose**:
- Assessment correct answers (only after submission)
- PSV ground truth (only after submission)
- User email (only to owner)

**Example: Question Filtering**
```python
# Return questions WITHOUT correct_answer or explanation
questions_out = [
    QuestionOut(
        id=str(q.id),
        text=q.question_text,
        options=q.options,
        pillar=q.pillar,
        # correct_answer NOT included
        # explanation NOT included
    )
    for q in questions
]
```

**Example: PSV Sample Filtering**
```python
return PSVSampleResponse(
    sample_id=str(sample.id),
    title=sample.title,
    pillar=sample.pillar,
    difficulty=sample.difficulty,
    task_context=sample.task_context,
    prompt_text=sample.prompt_text,
    output_text=sample.output_text,
    # NOTE: ground_truth_level is NOT exposed
)
```

### 2. Database Security

**Foreign Key Constraints**:
```python
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
```

**Cascade Deletes**:
- `UserUsage` cascades on user deletion
- Prevents orphaned usage records

**Unique Constraints**:
```python
email = Column(String, unique=True, nullable=False, index=True)
stripe_customer_id = Column(String(255), unique=True, nullable=False)
```

**Indexes**:
```python
email = Column(String, unique=True, nullable=False, index=True)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
```

### 3. UUID Usage

**Pattern**: Use UUIDs for all primary keys

**Benefits**:
- Non-sequential (prevents enumeration attacks)
- Globally unique
- No information leakage

**Implementation**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**Validation**:
```python
try:
    aid = uuid.UUID(assessment_id)
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid assessment ID")
```

### 4. Input Validation

**Pydantic Models**:
```python
class StartAssessmentRequest(BaseModel):
    mode: str  # Validated in endpoint
    industry: str | None = None
    role: str | None = None
    industry_id: str | None = None
    role_id: str | None = None
    session_id: str | None = None

# In endpoint
if body.mode not in ("quick", "full"):
    raise HTTPException(status_code=400, detail="mode must be 'quick' or 'full'")
```

**Literal Types**:
```python
class CheckoutRequest(BaseModel):
    plan: Literal["premium_monthly", "premium_annual"]
```

**Range Validation**:
```python
if body.user_level < 1 or body.user_level > 5:
    raise HTTPException(400, "user_level must be between 1 and 5")
```

## Webhook Security

### 1. Stripe Webhook Signature Verification

**Implementation**: `app/routers/payments.py:136`

```python
@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    try:
        # Verify signature
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Process verified event
    if event["type"] == "checkout.session.completed":
        await StripeService.handle_checkout_completed(event["data"]["object"], db)
```

**Security Properties**:
- Prevents replay attacks
- Ensures events come from Stripe
- Validates payload integrity

### 2. Webhook Idempotency

**Pattern**: Handle duplicate webhook deliveries

```python
# Stripe may send same event multiple times
# Operations should be idempotent

# Example: Subscription update
user.subscription_tier = "premium"  # Idempotent assignment
```

## Anti-Cheat System

### 1. Violation Tracking

**Model**: `Assessment.violations`, `Assessment.violation_log`

**Implementation**:
```python
@router.post("/{assessment_id}/violation")
async def report_violation(
    assessment_id: str,
    body: ViolationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Report an anti-cheat violation. 3 violations = session voided."""
    assessment = await load_assessment(assessment_id, db)
    
    # Increment violations
    current_violations = (assessment.violations or 0) + 1
    assessment.violations = current_violations
    
    # Append to log
    log = list(assessment.violation_log or [])
    log.append({
        "type": body.violation_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    assessment.violation_log = log
    flag_modified(assessment, "violation_log")
    
    # Void if threshold exceeded
    voided = current_violations >= 3
    if voided:
        assessment.status = AssessmentStatus.voided
    
    await db.commit()
```

**Violation Types** (client-reported):
- `tab_switch`: User switched browser tabs
- `copy_paste`: User copied/pasted content
- Other client-detected cheating behaviors

### 2. Timer Enforcement

**Pattern**: Server-side timer validation

```python
def check_timer_expired(assessment: Assessment) -> bool:
    """Check if assessment has exceeded time limit."""
    return datetime.now(timezone.utc) > assessment.expires_at

async def expire_assessment(db: AsyncSession, assessment: Assessment):
    """Mark assessment as expired."""
    assessment.status = AssessmentStatus.expired
    await db.commit()

# In endpoints
if check_timer_expired(assessment):
    await expire_assessment(db, assessment)
    raise HTTPException(status_code=400, detail="Assessment has expired")
```

## Security Best Practices

### 1. Principle of Least Privilege
- Anonymous users: limited access, results locked
- Free users: basic access, results locked on full assessments
- Premium users: full access with limits
- Enterprise users: unlimited access

### 2. Defense in Depth
- Client-side validation (UX)
- Server-side validation (security)
- Database constraints (data integrity)
- Webhook signature verification (external security)

### 3. Fail Secure
```python
# Default to most restrictive
user_tier = current_user.subscription_tier if current_user else "free"

# Default to locked
results_locked = False
if tier == "free":
    results_locked = True
```

### 4. Audit Trail
- `created_at`, `updated_at` timestamps on all models
- `violation_log` for anti-cheat events
- Webhook event logging

### 5. Error Message Safety
```python
# Don't leak information
raise HTTPException(status_code=401, detail="Invalid email or password")
# NOT: "Email not found" or "Password incorrect"

# Be specific for legitimate errors
raise HTTPException(status_code=403, detail=f"Assessment limit reached ({used}/{limit})")
```

## Security Gaps & Recommendations

### Current Gaps

1. **No Rate Limiting**
   - Endpoints vulnerable to brute force
   - No protection against API abuse

2. **No CSRF Protection**
   - JWT-only auth (no cookies)
   - Acceptable for API-only backend

3. **No Request Signing**
   - Only Stripe webhooks verified
   - Client requests not signed

4. **Limited Audit Logging**
   - No comprehensive audit trail
   - No security event monitoring

5. **No IP Restrictions**
   - Webhooks accept from any IP
   - Should whitelist Stripe IPs

### Recommendations

1. **Add Rate Limiting**:
   ```python
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @router.post("/auth/login")
   @limiter.limit("5/minute")
   async def login(...):
   ```

2. **Add Webhook IP Whitelisting**:
   ```python
   STRIPE_IPS = ["54.187.174.169", ...]  # Stripe's webhook IPs
   
   if request.client.host not in STRIPE_IPS:
       raise HTTPException(403, "Forbidden")
   ```

3. **Add Security Headers**:
   ```python
   from fastapi.middleware.trustedhost import TrustedHostMiddleware
   
   app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.promptranks.org"])
   ```

4. **Add Audit Logging**:
   ```python
   async def log_security_event(event_type: str, user_id: UUID, details: dict):
       # Log to database or external service
   ```

5. **Add Request Validation Middleware**:
   ```python
   @app.middleware("http")
   async def validate_content_type(request: Request, call_next):
       if request.method in ["POST", "PUT", "PATCH"]:
           if "application/json" not in request.headers.get("content-type", ""):
               return JSONResponse(status_code=415, content={"detail": "Unsupported Media Type"})
       return await call_next(request)
   ```
