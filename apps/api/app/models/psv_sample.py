import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.user import Base

class PsvSample(Base):
    __tablename__ = "psv_samples"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    pillar = Column(String(1), nullable=False, index=True)
    difficulty = Column(Integer, nullable=False)
    task_context = Column(Text, nullable=False)
    prompt_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    ground_truth_level = Column(Integer, nullable=False)
    ground_truth_rationale = Column(Text, nullable=True)
    content_tier = Column(String, nullable=False, default="core")
    content_pack_id = Column(UUID(as_uuid=True), ForeignKey("content_packs.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
