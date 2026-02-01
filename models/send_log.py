"""
Obscuras Campaign Manager - Send Log Model
Stores email send history and results.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from models.database import Base

if TYPE_CHECKING:
    from models.campaign import Campaign


class SendResult(enum.Enum):
    """Send result enumeration."""
    SUCCESS = "success"
    BOUNCE = "bounce"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class BounceType(enum.Enum):
    """Bounce type classification."""
    NONE = "none"
    HARD = "hard"  # Permanent (mailbox doesn't exist)
    SOFT = "soft"  # Temporary (mailbox full, server down)


class SendLog(Base):
    """Send log model for tracking email delivery attempts."""
    
    __tablename__ = "send_logs"
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FIELDS
    # ═══════════════════════════════════════════════════════════════
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id"), nullable=False)
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="send_logs")
    
    contact_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # EMAIL DETAILS
    # ═══════════════════════════════════════════════════════════════
    recipient_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # RESULT
    # ═══════════════════════════════════════════════════════════════
    result: Mapped[SendResult] = mapped_column(SQLEnum(SendResult), nullable=False)
    bounce_type: Mapped[BounceType] = mapped_column(SQLEnum(BounceType), default=BounceType.NONE)
    
    # SMTP response
    smtp_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    smtp_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # METADATA
    # ═══════════════════════════════════════════════════════════════
    smtp_profile_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("smtp_profiles.id"), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    
    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f"<SendLog(id={self.id}, email='{self.recipient_email}', result={self.result.value})>"
    
    @classmethod
    def log_success(cls, campaign_id: int, contact_id: int, email: str, subject: str | None = None) -> "SendLog":
        """Create a success log entry."""
        return cls(
            campaign_id=campaign_id,
            contact_id=contact_id,
            recipient_email=email,
            subject=subject,
            result=SendResult.SUCCESS,
        )
    
    @classmethod
    def log_bounce(cls, campaign_id: int, email: str, smtp_code: str, smtp_message: str, is_hard: bool = True):
        """Create a bounce log entry."""
        return cls(
            campaign_id=campaign_id,
            recipient_email=email,
            result=SendResult.BOUNCE,
            bounce_type=BounceType.HARD if is_hard else BounceType.SOFT,
            smtp_code=smtp_code,
            smtp_message=smtp_message,
        )
    
    @classmethod
    def log_error(cls, campaign_id: int, email: str, error_message: str):
        """Create an error log entry."""
        return cls(
            campaign_id=campaign_id,
            recipient_email=email,
            result=SendResult.ERROR,
            error_message=error_message,
        )
    
    def to_dict(self) -> dict[str, object]:
        """Convert log entry to dictionary."""
        bounce = self.bounce_type
        sent = self.sent_at
        return {
            "id": self.id,
            "recipient_email": self.recipient_email,
            "result": self.result.value,
            "bounce_type": bounce.value if bounce else None,  # type: ignore[union-attr]
            "smtp_code": self.smtp_code,
            "error_message": self.error_message,
            "sent_at": sent.isoformat() if sent else None,  # type: ignore[union-attr]
        }
