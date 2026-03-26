"""PSV Engine: Peer Sample Validation — user evaluates pre-scored samples."""
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.psv_sample import PsvSample


async def select_psv_sample(db: AsyncSession) -> PsvSample | None:
    """Select a random active PSV sample."""
    result = await db.execute(
        select(PsvSample).where(PsvSample.is_active.is_(True))
    )
    samples = result.scalars().all()
    if not samples:
        return None
    return random.choice(samples)


def compute_psv_score(user_level: int, ground_truth_level: int) -> float:
    """Compute PSV score based on calibration accuracy.
    delta=0 → 100, delta=1 → 75, delta=2 → 50, delta=3 → 25, delta=4 → 0
    """
    delta = abs(user_level - ground_truth_level)
    return max(0.0, 100.0 - delta * 25.0)
