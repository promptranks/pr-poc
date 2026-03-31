from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class PendingAssessment(Base):
    __tablename__ = "pending_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String(255), nullable=False, unique=True)
    industry = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    mode = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(hours=24))

    # Relationships
    user = relationship("User", back_populates="pending_assessments")
    assessment = relationship("Assessment")

    # Constraints
    __table_args__ = (
        CheckConstraint("mode IN ('quick', 'full')", name="check_mode"),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'abandoned')", name="check_status"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
            "industry": self.industry,
            "role": self.role,
            "mode": self.mode,
            "status": self.status,
            "assessment_id": str(self.assessment_id) if self.assessment_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
