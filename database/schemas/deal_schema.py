import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Numeric, DateTime, Enum, Index, func
from sqlalchemy.dialects.postgresql import UUID

from database.schemas.base import Base


class DealStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class DealSchema(Base):
    __tablename__ = "deals"
    __table_args__ = (Index("ix_deals_status_created_at", "status", "created_at"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount_from = Column(Numeric(18, 2), nullable=False)
    currency_from = Column(String(3), nullable=False)
    amount_to = Column(Numeric(18, 2), nullable=False)
    currency_to = Column(String(3), nullable=False)
    rate = Column(Numeric(18, 8), nullable=False)
    status = Column(Enum(DealStatus), default=DealStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
