from fastapi import APIRouter

router = APIRouter(prefix="/badges", tags=["badges"])


@router.get("/verify/{badge_id}")
async def verify_badge(badge_id: str):
    """Public badge verification endpoint."""
    # TODO: Implement in Step 5
    return {"message": "not implemented"}
