# Existing Services: Patterns & Interactions

## Service Layer Architecture

The codebase follows a service-oriented architecture where business logic is extracted into service classes/modules, keeping routers thin and focused on HTTP concerns.

## Core Services

### 1. UsageService (`app/services/usage_service.py`)

**Pattern**: Static methods (stateless utility class)

**Responsibilities**:
- Tier limit management
- Billing period calculation
- Usage record lifecycle (get/create)
- Usage validation and increment

**Methods**:
```python
@staticmethod
def get_tier_limit(tier: str) -> int:
    """Returns assessment limit for subscription tier."""
    limits = {"free": 0, "premium": 3, "enterprise": 999}
    return limits.get(tier, 0)

@staticmethod
def get_current_period() -> Tuple[date, date]:
    """Returns (period_start, period_end) for current month."""
    # Returns 1st and last day of current month

@staticmethod
async def get_or_create_usage(user_id: str, tier: str, db: AsyncSession) -> UserUsage:
    """Fetches or creates usage record for current period."""
    # Queries by user_id + period_start
    # Creates if not found with tier limit

@staticmethod
async def check_limit(user_id: str, tier: str, db: AsyncSession) -> Tuple[bool, int, int]:
    """Returns (can_access, used, limit)."""
    # can_access = used < limit

@staticmethod
async def increment_usage(user_id: str, tier: str, db: AsyncSession) -> None:
    """Increments usage counter and updates timestamp."""
    # Increments full_assessments_used
    # Updates updated_at
```

**Usage Pattern**:
```python
# In assessment router
tier = current_user.subscription_tier
can_start, used, limit = await UsageService.check_limit(str(current_user.id), tier, db)
if not can_start:
    raise HTTPException(403, f"Limit reached ({used}/{limit})")
await UsageService.increment_usage(str(current_user.id), tier, db)
```

**Interactions**:
- Called by: `assessment.py` router (start_assessment endpoint)
- Depends on: `UserUsage` model, database session
- No external service calls

### 2. StripeService (`app/services/stripe_service.py`)

**Pattern**: Static methods (stateless utility class)

**Responsibilities**:
- Stripe checkout session creation
- Stripe billing portal session creation
- Webhook event processing
- Customer/subscription management

**Methods**:
```python
@staticmethod
async def create_checkout_session(user_id: UUID, plan: str, db: AsyncSession) -> str:
    """Creates Stripe checkout session, returns checkout URL."""
    # Validates plan (premium_monthly/premium_annual)
    # Gets/creates StripeCustomer
    # Creates Stripe checkout session with metadata
    # Returns session.url

@staticmethod
async def create_portal_session(user_id: UUID, db: AsyncSession) -> str:
    """Creates Stripe billing portal session, returns portal URL."""
    # Retrieves StripeCustomer
    # Creates portal session
    # Returns session.url

@staticmethod
async def handle_checkout_completed(session_data: dict, db: AsyncSession):
    """Webhook handler: upgrades user to premium."""
    # Extracts user_id from metadata
    # Updates user.subscription_tier = "premium"
    # Updates stripe_customer.stripe_subscription_id
    # Sends upgrade email

@staticmethod
async def handle_subscription_deleted(subscription_data: dict, db: AsyncSession):
    """Webhook handler: downgrades user to free."""
    # Finds StripeCustomer by subscription_id
    # Updates user.subscription_tier = "free"
    # Clears stripe_customer.stripe_subscription_id
```

**Helper Function**:
```python
async def _resolve(value):
    """Resolves awaitable or returns value directly."""
    return await value if inspect.isawaitable(value) else value
```

**Usage Pattern**:
```python
# In payments router
checkout_url = await StripeService.create_checkout_session(
    current_user.id, 
    request.plan, 
    db
)
return {"checkout_url": checkout_url}

# In webhook endpoint
if event["type"] == "checkout.session.completed":
    await StripeService.handle_checkout_completed(event["data"]["object"], db)
```

**Interactions**:
- Called by: `payments.py` router
- Depends on: `User`, `StripeCustomer` models, Stripe API, EmailService
- External calls: Stripe API (Customer.create, checkout.Session.create, etc.)

**Error Handling**:
- Raises `ValueError` for missing config/invalid plans
- Stripe errors propagate to caller
- Extensive logging for webhook events

### 3. AuthService (`app/services/auth_service.py`)

**Pattern**: Functions (not shown in files but referenced)

**Responsibilities**:
- JWT token creation/validation
- User authentication
- Password hashing/verification

**Referenced Methods**:
```python
def create_access_token(user_id: UUID, email: str) -> str:
    """Creates JWT access token."""

def decode_access_token(token: str) -> dict:
    """Decodes and validates JWT token."""

async def create_user(db: AsyncSession, email: str, name: str, password: str) -> User:
    """Creates new user with hashed password."""

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Retrieves user by email."""

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies password against hash."""
```

**Usage Pattern**:
```python
# In auth middleware
payload = decode_access_token(credentials.credentials)
user_id = UUID(payload.get("sub"))

# In claim endpoint
token = create_access_token(user.id, user.email)
```

### 4. EmailService (`app/services/email_service.py`)

**Pattern**: Static methods (referenced but not shown)

**Responsibilities**:
- Transactional email sending
- Email template rendering

**Referenced Methods**:
```python
@staticmethod
def send_upgrade_email(email: str, name: str):
    """Sends upgrade confirmation email."""
```

**Usage Pattern**:
```python
# In StripeService webhook handler
EmailService.send_upgrade_email(user.email, user.name)
```

### 5. BadgeService (`app/services/badge_service.py`)

**Pattern**: Functions (referenced but not shown)

**Responsibilities**:
- Badge generation
- SVG rendering
- Verification URL creation

**Referenced Methods**:
```python
async def create_badge(db: AsyncSession, user: User, assessment: Assessment) -> Badge:
    """Creates badge record with SVG and verification URL."""
```

**Usage Pattern**:
```python
# In claim endpoint
badge = await create_badge(db, user, assessment)
return ClaimResponse(
    badge_id=str(badge.id),
    badge_svg=badge.badge_svg,
    verification_url=badge.verification_url,
    ...
)
```

## Service Interaction Patterns

### 1. Dependency Injection via FastAPI

All services receive dependencies through function parameters:
```python
async def endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await SomeService.method(user_id, db)
```

### 2. Database Session Management

- Sessions injected via `Depends(get_db)`
- Services receive session as parameter
- Caller responsible for commit/rollback
- Services may commit internally (e.g., UsageService.get_or_create_usage)

### 3. Error Propagation

Services use two error patterns:
1. **Raise exceptions**: Let caller handle (most common)
2. **Return None/False**: For optional operations

Example:
```python
# Service raises ValueError
try:
    url = await StripeService.create_checkout_session(...)
except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc))
```

### 4. Async Throughout

All service methods are async:
- Database operations use `await`
- External API calls use `await`
- No blocking I/O

### 5. Type Hints

All services use comprehensive type hints:
```python
async def check_limit(
    user_id: str, 
    tier: str, 
    db: AsyncSession
) -> Tuple[bool, int, int]:
```

## Service Communication Flow

### Assessment Start with Usage Check
```
Router (assessment.py)
  ↓
UsageService.check_limit()
  ↓ (if allowed)
UsageService.increment_usage()
  ↓
Create Assessment
  ↓
Return response
```

### Stripe Checkout to Upgrade
```
Router (payments.py)
  ↓
StripeService.create_checkout_session()
  ↓
Stripe API
  ↓
User completes payment
  ↓
Stripe Webhook → Router (payments.py)
  ↓
StripeService.handle_checkout_completed()
  ↓
Update User model
  ↓
EmailService.send_upgrade_email()
```

### Assessment Claim with Badge
```
Router (assessment.py)
  ↓
AuthService.get_user_by_email() / create_user()
  ↓
Link assessment to user
  ↓
BadgeService.create_badge()
  ↓
LeaderboardService.update_score()
  ↓
AuthService.create_access_token()
  ↓
Return badge + token
```

## Service Design Principles

### 1. Single Responsibility
Each service handles one domain:
- UsageService: usage tracking only
- StripeService: payment processing only
- AuthService: authentication only

### 2. Stateless
All services use static methods or pure functions:
- No instance state
- All data passed as parameters
- Idempotent operations where possible

### 3. Testability
Services designed for easy mocking:
- Clear interfaces
- Dependency injection
- No global state
- External calls isolated

Example test:
```python
@pytest.mark.asyncio
async def test_premium_user_under_limit(db_session, test_user):
    test_user.subscription_tier = "premium"
    await db_session.commit()
    
    can_start, used, limit = await UsageService.check_limit(
        str(test_user.id), 
        "premium", 
        db_session
    )
    
    assert can_start is True
    assert used == 0
    assert limit == 3
```

### 4. Separation of Concerns
- **Routers**: HTTP concerns (request/response, status codes)
- **Services**: Business logic (validation, calculations, orchestration)
- **Models**: Data structure and persistence

### 5. Explicit Dependencies
Services declare all dependencies:
```python
async def method(
    user_id: str,      # Required data
    tier: str,         # Required data
    db: AsyncSession   # Required service
) -> ReturnType:
```

## Common Patterns

### Pattern 1: Get or Create
```python
async def get_or_create_usage(...) -> UserUsage:
    result = await db.execute(select(UserUsage).where(...))
    usage = result.scalar_one_or_none()
    
    if not usage:
        usage = UserUsage(...)
        db.add(usage)
        await db.commit()
        await db.refresh(usage)
    
    return usage
```

### Pattern 2: Check and Increment
```python
# Check first
can_start, used, limit = await UsageService.check_limit(...)
if not can_start:
    raise HTTPException(403, ...)

# Then increment
await UsageService.increment_usage(...)
```

### Pattern 3: Webhook Processing
```python
async def handle_webhook_event(event_data: dict, db: AsyncSession):
    # Extract data
    user_id = UUID(event_data["metadata"]["user_id"])
    
    # Load models
    user = await db.execute(select(User).where(...))
    
    # Update state
    user.subscription_tier = "premium"
    
    # Commit
    await db.commit()
    
    # Side effects (email, etc.)
    EmailService.send_email(...)
```

### Pattern 4: External API Wrapper
```python
async def create_checkout_session(...) -> str:
    # Validate inputs
    if plan not in ["premium_monthly", "premium_annual"]:
        raise ValueError("Invalid plan")
    
    # Prepare data
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    
    # Call external API
    session = stripe.checkout.Session.create(...)
    
    # Return simplified result
    return session.url
```

## Service Extension Points

To add new features, follow these patterns:

### Adding Usage Tracking for New Resource
1. Add field to `UserUsage` model
2. Add method to `UsageService`:
   ```python
   @staticmethod
   async def check_resource_limit(user_id: str, tier: str, db: AsyncSession):
       # Similar to check_limit
   ```
3. Call from router before resource creation

### Adding Stripe Webhook Handler
1. Add method to `StripeService`:
   ```python
   @staticmethod
   async def handle_new_event(event_data: dict, db: AsyncSession):
       # Process event
   ```
2. Add case to webhook router:
   ```python
   elif event["type"] == "new.event.type":
       await StripeService.handle_new_event(event["data"]["object"], db)
   ```

### Adding New Service
1. Create `app/services/new_service.py`
2. Use static methods or pure functions
3. Accept `db: AsyncSession` as parameter
4. Use type hints
5. Raise exceptions for errors
6. Add tests in `tests/test_new_service.py`
