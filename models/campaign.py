"""
Obscuras Campaign Manager - Campaign Model
Stores campaign configuration and metadata.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from models.database import Base

if TYPE_CHECKING:
    from models.contact import Contact
    from models.smtp_profile import SmtpProfile
    from models.send_log import SendLog
from utils.logging_config import get_logger

logger = get_logger("models.campaign")


class CampaignStatus(enum.Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Campaign(Base):
    """Campaign model for storing email campaign data."""
    
    __tablename__ = "campaigns"
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FIELDS
    # ═══════════════════════════════════════════════════════════════
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # Folder name
    
    # ═══════════════════════════════════════════════════════════════
    # EMAIL CONTENT
    # ═══════════════════════════════════════════════════════════════
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    template_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Content blocks (stored as JSON in YAML format)
    greeting: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intro: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    highlight: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of paragraphs
    cta_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cta_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # STATUS & SCHEDULING
    # ═══════════════════════════════════════════════════════════════
    status: Mapped[CampaignStatus] = mapped_column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    
    # Schedule settings
    schedule_days: Mapped[str] = mapped_column(String(50), default="1-5")  # 1=Mo, 5=Fr
    schedule_hours: Mapped[str] = mapped_column(String(50), default="9-17")
    schedule_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    schedule_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # SMTP CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    smtp_profile_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("smtp_profiles.id"), nullable=True)
    smtp_profile: Mapped[Optional["SmtpProfile"]] = relationship("SmtpProfile", back_populates="campaigns")
    
    # ═══════════════════════════════════════════════════════════════
    # RATE LIMITING
    # ═══════════════════════════════════════════════════════════════
    delay_seconds: Mapped[int] = mapped_column(Integer, default=80)
    max_per_hour: Mapped[int] = mapped_column(Integer, default=50)
    max_per_day: Mapped[int] = mapped_column(Integer, default=200)
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════
    total_contacts: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    bounce_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="campaign", cascade="all, delete-orphan")
    send_logs: Mapped[List["SendLog"]] = relationship("SendLog", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status={self.status.value})>"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        sent: int = self.sent_count or 0  # type: ignore[assignment]
        bounce: int = self.bounce_count or 0  # type: ignore[assignment]
        error: int = self.error_count or 0  # type: ignore[assignment]
        if sent == 0:
            return 0.0
        return float((sent - bounce - error) / sent) * 100
    
    @property
    def progress(self) -> float:
        """Calculate campaign progress percentage."""
        total: int = self.total_contacts or 0  # type: ignore[assignment]
        sent: int = self.sent_count or 0  # type: ignore[assignment]
        if total == 0:
            return 0.0
        return float(sent / total) * 100
    
    def to_dict(self) -> dict[str, object]:
        """Convert campaign to dictionary."""
        status_val = self.status
        created = self.created_at
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "subject": self.subject,
            "status": status_val.value if status_val else None,  # type: ignore[union-attr]
            "total_contacts": self.total_contacts,
            "sent_count": self.sent_count,
            "bounce_count": self.bounce_count,
            "progress": self.progress,
            "success_rate": self.success_rate,
            "created_at": created.isoformat() if created else None,  # type: ignore[union-attr]
        }
