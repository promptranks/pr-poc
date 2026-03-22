from fastapi import APIRouter

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/start")
async def start_assessment():
    """Start a new assessment (quick or full)."""
    # TODO: Implement in Step 3
    return {"message": "not implemented"}


@router.post("/{assessment_id}/kba/submit")
async def submit_kba(assessment_id: str):
    """Submit KBA answers."""
    # TODO: Implement in Step 3
    return {"message": "not implemented"}


@router.post("/{assessment_id}/ppa/execute")
async def execute_ppa(assessment_id: str):
    """Execute a prompt in PPA sandbox."""
    # TODO: Implement in Step 4
    return {"message": "not implemented"}


@router.post("/{assessment_id}/psv/submit")
async def submit_psv(assessment_id: str):
    """Submit PSV portfolio entry."""
    # TODO: Implement in Step 8
    return {"message": "not implemented"}


@router.get("/{assessment_id}/results")
async def get_results(assessment_id: str):
    """Get assessment results and badge."""
    # TODO: Implement in Step 5
    return {"message": "not implemented"}
