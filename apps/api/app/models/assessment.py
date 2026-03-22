import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.models.user import Base


class AssessmentMode(str, enum.Enum):
    quick = "quick"
    full = "full"


class AssessmentStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    voided = "voided"
    expired = "expired"


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    mode = Column(Enum(AssessmentMode), nullable=False)
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.in_progress)
    industry = Column(String, nullable=True)
    role = Column(String, nullable=True)

    # KBA
    kba_score = Column(Float, nullable=True)
    kba_responses = Column(JSON, nullable=True)

    # PPA
    ppa_score = Column(Float, nullable=True)
    ppa_responses = Column(JSON, nullable=True)

    # PSV (full only)
    psv_score = Column(Float, nullable=True)
    psv_submission = Column(JSON, nullable=True)

    # Final
    final_score = Column(Float, nullable=True)
    level = Column(Integer, nullable=True)  # 1-5
    pillar_scores = Column(JSON, nullable=True)  # {"P": 85, "E": 78, ...}

    # Anti-cheat
    violations = Column(Integer, default=0)
    violation_log = Column(JSON, nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
