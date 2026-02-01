"""
Obscuras Campaign Manager - Blacklist Model
Stores blacklisted email addresses and domains.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
import enum

from models.database import Base
from utils.logging_config import get_logger

logger = get_logger("models.blacklist")


class BlacklistReason(enum.Enum):
    """Reason for blacklisting."""
    HARD_BOUNCE = "hard_bounce"
    UNSUBSCRIBE = "unsubscribe"
    COMPLAINT = "complaint"
    MANUAL = "manual"
    INVALID = "invalid"


class BlacklistType(enum.Enum):
    """Type of blacklist entry."""
    EMAIL = "email"
    DOMAIN = "domain"


class BlacklistEntry(Base):
    """Blacklist model for storing blocked email addresses and domains."""
    
    __tablename__ = "blacklist"
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FIELDS
    # ═══════════════════════════════════════════════════════════════
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # The blocked value (email address or domain)
    value = Column(String(320), nullable=False, unique=True, index=True)
    entry_type = Column(SQLEnum(BlacklistType), default=BlacklistType.EMAIL)
    
    # ═══════════════════════════════════════════════════════════════
    # REASON & SOURCE
    # ═══════════════════════════════════════════════════════════════
    reason = Column(SQLEnum(BlacklistReason), nullable=False)
    source_campaign_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Original SMTP error (if bounce)
    smtp_code = Column(String(10), nullable=True)
    smtp_message = Column(Text, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<BlacklistEntry(id={self.id}, value='{self.value}', reason={self.reason.value})>"
    
    @classmethod
    def from_bounce(cls, email: str, smtp_code: str, smtp_message: str, campaign_id: Optional[int] = None):
        """Create a blacklist entry from a bounce."""
        return cls(
            value=email.lower(),
            entry_type=BlacklistType.EMAIL,
            reason=BlacklistReason.HARD_BOUNCE,
            source_campaign_id=campaign_id,
            smtp_code=smtp_code,
            smtp_message=smtp_message,
        )
    
    @classmethod
    def from_unsubscribe(cls, email: str, notes: Optional[str] = None):
        """Create a blacklist entry from an unsubscribe request."""
        return cls(
            value=email.lower(),
            entry_type=BlacklistType.EMAIL,
            reason=BlacklistReason.UNSUBSCRIBE,
            notes=notes,
        )
    
    @classmethod
    def block_domain(cls, domain: str, notes: Optional[str] = None):
        """Block an entire domain."""
        return cls(
            value=domain.lower(),
            entry_type=BlacklistType.DOMAIN,
            reason=BlacklistReason.MANUAL,
            notes=notes,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dictionary."""
        created_at_value: Optional[datetime] = self.created_at  # type: ignore[assignment]
        return {
            "id": self.id,
            "value": self.value,
            "entry_type": self.entry_type.value,
            "reason": self.reason.value,
            "notes": self.notes,
            "created_at": created_at_value.isoformat() if created_at_value else None,
        }
