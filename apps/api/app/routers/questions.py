from fastapi import APIRouter

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/")
async def list_questions():
    """List questions (admin only)."""
    # TODO: Implement in Step 3
    return {"message": "not implemented"}
