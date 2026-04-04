# Code Conventions: Style, Naming, Error Handling & Testing

## Code Style

### 1. Python Style Guide

**Base**: PEP 8 compliant

**Key Conventions**:
- 4 spaces for indentation (no tabs)
- Max line length: ~100-120 characters (flexible)
- Double quotes for strings
- Type hints on all function signatures
- Docstrings for public functions

**Example**:
```python
async def get_or_create_usage(user_id: str, tier: str, db: AsyncSession) -> UserUsage:
    """Fetches or creates usage record for current period."""
    period_start, period_end = UsageService.get_current_period()
    limit = UsageService.get_tier_limit(tier)
    # ...
```

### 2. Import Organization

**Order**:
1. Standard library imports
2. Third-party imports
3. Local application imports

**Example**:
```python
# Standard library
import uuid
from datetime import datetime, timezone
from typing import Tuple

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Local
from app.database import get_db
from app.models.user import User
from app.services.usage_service import UsageService
```

### 3. Async/Await Consistency

**Pattern**: All I/O operations are async

```python
# Database operations
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

# Service calls
await UsageService.increment_usage(user_id, tier, db)

# External APIs
session = stripe.checkout.Session.create(...)  # Stripe SDK is sync
```

## Naming Conventions

### 1. Variables & Functions

**Pattern**: `snake_case`

```python
user_id = uuid.uuid4()
subscription_tier = "premium"
period_start = date.today()

async def get_current_user():
    pass

async def check_limit():
    pass
```

### 2. Classes & Models

**Pattern**: `PascalCase`

```python
class User(Base):
    pass

class UsageService:
    pass

class StartAssessmentRequest(BaseModel):
    pass
```

### 3. Constants

**Pattern**: `UPPER_SNAKE_CASE`

```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
LEVEL_NAMES = {1: "Novice", 2: "Intermediate", ...}
```

### 4. Enums

**Pattern**: `PascalCase` for class, `snake_case` for values

```python
class AssessmentMode(str, enum.Enum):
    quick = "quick"
    full = "full"

class AssessmentStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    voided = "voided"
    expired = "expired"
```

### 5. Private/Helper Functions

**Pattern**: Leading underscore for module-level helpers

```python
def _check_premium_required(industry: str | None, role: str | None, mode: str) -> bool:
    """Helper function not exposed in API."""
    pass

async def _load_assessment(db: AsyncSession, assessment_id: str) -> Assessment:
    """Internal helper for loading and validating assessments."""
    pass

def _build_results_response(assessment: Assessment) -> ResultsResponse:
    """Internal helper for building response objects."""
    pass
```

### 6. Database Models

**Table Names**: `snake_case`, plural
```python
__tablename__ = "users"
__tablename__ = "user_usage"
__tablename__ = "stripe_customers"
__tablename__ = "assessments"
```

**Column Names**: `snake_case`
```python
subscription_tier = Column(String, default="free")
full_assessments_used = Column(Integer, default=0)
stripe_customer_id = Column(String(255), unique=True)
```

### 7. API Endpoints

**Pattern**: `kebab-case` for multi-word paths

```python
@router.post("/create-checkout")
@router.post("/create-portal")
@router.post("/sync-subscription")
@router.post("/submit-best")
```

### 8. Request/Response Models

**Pattern**: Descriptive suffixes

```python
class StartAssessmentRequest(BaseModel):
    pass

class StartAssessmentResponse(BaseModel):
    pass

class SubmitKBARequest(BaseModel):
    pass

class SubmitKBAResponse(BaseModel):
    pass
```

## Error Handling

### 1. HTTPException Pattern

**Standard Usage**:
```python
from fastapi import HTTPException

# 400 Bad Request - Invalid input
if body.mode not in ("quick", "full"):
    raise HTTPException(status_code=400, detail="mode must be 'quick' or 'full'")

# 401 Unauthorized - Not authenticated
if credentials is None:
    raise HTTPException(status_code=401, detail="Not authenticated")

# 402 Payment Required - Premium required
if requires_premium and user_tier not in ("premium", "enterprise"):
    raise HTTPException(
        status_code=402,
        detail="Premium subscription required for this industry/role combination"
    )

# 403 Forbidden - Authenticated but not allowed
if not can_start:
    raise HTTPException(
        status_code=403,
        detail=f"Assessment limit reached ({used}/{limit}). Upgrade to Enterprise for unlimited access."
    )

# 404 Not Found - Resource doesn't exist
if assessment is None:
    raise HTTPException(status_code=404, detail="Assessment not found")

# 409 Conflict - Resource already exists
if existing_badge.scalar_one_or_none() is not None:
    raise HTTPException(status_code=409, detail="Assessment already claimed")

# 500 Internal Server Error - Unexpected error
if not questions:
    raise HTTPException(status_code=500, detail="No questions available. Run the seed script first.")

# 502 Bad Gateway - External service error
except Exception as e:
    raise HTTPException(status_code=502, detail=f"LLM execution failed: {str(e)}")
```

### 2. Service Layer Errors

**Pattern**: Raise ValueError for business logic errors

```python
# In service
if plan not in ["premium_monthly", "premium_annual"]:
    raise ValueError("Unsupported subscription plan.")

if not secret_key:
    raise ValueError("Stripe secret key is missing. Set STRIPE_SECRET_KEY in .env.")

# In router
try:
    checkout_url = await StripeService.create_checkout_session(current_user.id, request.plan, db)
except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc))
```

### 3. External API Errors

**Pattern**: Catch specific exceptions, re-raise as HTTPException

```python
try:
    checkout_url = await StripeService.create_checkout_session(...)
except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc))
except stripe.error.StripeError as exc:
    message = getattr(exc, "user_message", None) or "Stripe checkout is not configured correctly yet."
    raise HTTPException(status_code=502, detail=message)
```

### 4. Database Errors

**Pattern**: Let SQLAlchemy errors propagate (FastAPI handles them)

```python
# No try/catch needed for normal operations
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one()  # Raises if not found

# Use scalar_one_or_none() when None is valid
user = result.scalar_one_or_none()
if user is None:
    raise HTTPException(status_code=404, detail="User not found")
```

### 5. Validation Errors

**Pattern**: Validate early, fail fast

```python
# UUID validation
try:
    aid = uuid.UUID(assessment_id)
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid assessment ID")

# Range validation
if body.user_level < 1 or body.user_level > 5:
    raise HTTPException(400, "user_level must be between 1 and 5")

# Enum validation
if body.mode not in ("quick", "full"):
    raise HTTPException(status_code=400, detail="mode must be 'quick' or 'full'")
```

### 6. Logging Pattern

**Usage**: Log important events, especially in webhooks

```python
import logging
logger = logging.getLogger(__name__)

# Info level for normal operations
logger.info(f"Webhook: checkout.session.completed for user {user_id}, subscription {subscription_id}")
logger.info(f"Webhook: Successfully updated user {user.email} to premium tier")

# Error level for failures
logger.error(f"Webhook: Invalid payload - {str(e)}")
logger.error(f"Sync: Stripe error - {str(e)}")
```

## Testing Patterns

### 1. Test File Organization

**Structure**:
```
tests/
├── conftest.py              # Shared fixtures
├── test_auth.py             # Auth tests
├── test_usage.py            # Usage service tests
├── test_payments.py         # Payment tests
├── test_kba.py              # KBA tests
└── ...
```

### 2. Fixture Patterns

**Shared Fixtures** (`conftest.py`):
```python
@pytest_asyncio.fixture
async def db_session(engine):
    """Create a test database session."""
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a basic persisted user for tests that need one."""
    user = User(
        id=uuid.uuid4(),
        email="fixture-user@test.com",
        name="Fixture User",
        password_hash="hashed",
        subscription_tier="free",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

### 3. Test Naming

**Pattern**: `test_<feature>_<scenario>`

```python
@pytest.mark.asyncio
async def test_get_tier_limit():
    pass

@pytest.mark.asyncio
async def test_free_user_full_assessment_locked(db_session, test_user):
    pass

@pytest.mark.asyncio
async def test_premium_user_under_limit(db_session, test_user):
    pass

@pytest.mark.asyncio
async def test_premium_user_at_limit(db_session, test_user):
    pass
```

### 4. Async Test Pattern

**Decorator**: Always use `@pytest.mark.asyncio`

```python
@pytest.mark.asyncio
async def test_premium_user_increment_usage(db_session, test_user):
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()
    
    await UsageService.increment_usage(str(test_user.id), "premium", db_session)
    
    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)
    assert used == 1
    assert limit == 3
```

### 5. Mocking Pattern

**External Services**: Mock with `unittest.mock`

```python
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.asyncio
async def test_create_checkout_session():
    user_id = uuid4()
    mock_db = AsyncMock()
    
    with patch.dict(os.environ, {
        'STRIPE_SECRET_KEY': 'sk_test_123',
        'STRIPE_PREMIUM_PRICE_ID': 'price_test_123',
    }), \
         patch('stripe.Customer.create') as mock_customer, \
         patch('stripe.checkout.Session.create') as mock_session:
        
        mock_customer.return_value = Mock(id="cus_test123")
        mock_session.return_value = Mock(url="https://checkout.stripe.com/test")
        
        url = await StripeService.create_checkout_session(user_id, "premium_monthly", mock_db)
        
        assert url == "https://checkout.stripe.com/test"
        mock_customer.assert_called_once()
```

### 6. Database Testing

**Pattern**: Use SQLite in-memory for tests

```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def engine():
    """Create a test database engine."""
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield eng
    
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await eng.dispose()
```

### 7. Assertion Patterns

**Clear Assertions**:
```python
# Boolean checks
assert can_start is True
assert assessment.results_locked is True

# Equality checks
assert used == 0
assert limit == 3
assert user.subscription_tier == "premium"

# None checks
assert user is not None
assert stripe_customer.stripe_subscription_id is None
```

## API Response Patterns

### 1. Success Responses

**Pattern**: Return Pydantic models or dicts

```python
# Pydantic model response
return StartAssessmentResponse(
    assessment_id=str(assessment.id),
    mode=body.mode,
    expires_at=expires_at.isoformat(),
    questions=questions_out,
)

# Dict response
return {
    "checkout_url": checkout_url
}

# Simple success
return {"success": True}
```

### 2. Error Responses

**Pattern**: HTTPException with detail

```python
raise HTTPException(
    status_code=403,
    detail=f"Assessment limit reached ({used}/{limit}). Upgrade to Enterprise for unlimited access."
)
```

**FastAPI Auto-Formats**:
```json
{
  "detail": "Assessment limit reached (3/3). Upgrade to Enterprise for unlimited access."
}
```

### 3. Response Models

**Pattern**: Use Pydantic with `model_config`

```python
class QuestionOut(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    text: str
    options: list[str]
    pillar: str
```

### 4. Datetime Serialization

**Pattern**: Convert to ISO format strings

```python
expires_at=expires_at.isoformat()
completed_at=assessment.completed_at.isoformat()
```

## Database Patterns

### 1. Query Pattern

**Standard Query**:
```python
result = await db.execute(
    select(User).where(User.id == user_id)
)
user = result.scalar_one_or_none()
```

**Multiple Results**:
```python
result = await db.execute(
    select(Question).where(Question.id.in_(question_ids))
)
questions = result.scalars().all()
```

### 2. Create Pattern

**Standard Create**:
```python
assessment = Assessment(
    id=uuid.uuid4(),
    user_id=current_user.id,
    mode=AssessmentMode(body.mode),
    status=AssessmentStatus.in_progress,
    # ...
)
db.add(assessment)
await db.commit()
await db.refresh(assessment)
```

### 3. Update Pattern

**Standard Update**:
```python
user.subscription_tier = "premium"
user.updated_at = datetime.now(timezone.utc)
await db.commit()
```

**JSON Column Update**:
```python
assessment.ppa_responses = updated_ppa
flag_modified(assessment, "ppa_responses")
await db.commit()
```

### 4. Delete Pattern

**Standard Delete**:
```python
await db.delete(pending)
await db.commit()
```

## Configuration Patterns

### 1. Environment Variables

**Pattern**: Use Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://..."
    secret_key: str = "dev-secret-change-in-production"
    stripe_secret_key: str = ""
    
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
```

### 2. Feature Flags

**Pattern**: Use settings for feature toggles

```python
deployment_mode: Literal["self_hosted", "saas"] = "self_hosted"
```

## Documentation Patterns

### 1. Docstrings

**Pattern**: Brief description, no parameter docs (type hints suffice)

```python
async def get_or_create_usage(user_id: str, tier: str, db: AsyncSession) -> UserUsage:
    """Fetches or creates usage record for current period."""
    pass
```

### 2. Endpoint Documentation

**Pattern**: FastAPI auto-generates from docstrings

```python
@router.post("/start", response_model=StartAssessmentResponse)
async def start_assessment(...):
    """Start a new assessment (quick or full). Checks for pending assessment and premium requirements."""
    pass
```

### 3. Comments

**Pattern**: Explain why, not what

```python
# Premium gating - single decision point
requires_premium = _check_premium_required(body.industry, body.role, body.mode)

# Check usage limits for full assessments
if body.mode == "full":
    # ...
```

## File Organization

### 1. Module Structure

```
app/
├── main.py                  # FastAPI app initialization
├── config.py                # Settings
├── database.py              # Database setup
├── models/                  # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   ├── assessment.py
│   ├── user_usage.py
│   └── stripe_customer.py
├── routers/                 # API endpoints
│   ├── __init__.py
│   ├── assessment.py
│   └── payments.py
├── services/                # Business logic
│   ├── __init__.py
│   ├── usage_service.py
│   ├── stripe_service.py
│   └── auth_service.py
└── middleware/              # Middleware
    ├── __init__.py
    └── auth.py
```

### 2. Import Patterns

**Absolute Imports**:
```python
from app.models.user import User
from app.services.usage_service import UsageService
from app.database import get_db
```

**No Relative Imports** (except within same package):
```python
# Good
from app.models.user import User

# Avoid
from ..models.user import User
```
