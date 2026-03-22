from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register():
    """Register a new user."""
    # TODO: Implement in Step 2
    return {"message": "not implemented"}


@router.post("/login")
async def login():
    """Login and receive JWT token."""
    # TODO: Implement in Step 2
    return {"message": "not implemented"}
