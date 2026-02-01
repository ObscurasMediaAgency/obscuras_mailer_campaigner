"""
Obscuras Campaign Manager - Contact Model
Stores contact information for campaigns.
"""

from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
import json

from models.database import Base

if TYPE_CHECKING:
    from models.campaign import Campaign


class ContactStatus(enum.Enum):
    """Contact status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    BOUNCED = "bounced"
    ERROR = "error"
    BLACKLISTED = "blacklisted"
    UNSUBSCRIBED = "unsubscribed"


class Contact(Base):
    """Contact model for storing recipient data."""
    
    __tablename__ = "contacts"
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FIELDS
    # ═══════════════════════════════════════════════════════════════
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    
    # ═══════════════════════════════════════════════════════════════
    # PERSONALIZATION FIELDS
    # ═══════════════════════════════════════════════════════════════
    # These are common fields, but additional data is stored in custom_fields
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Custom fields stored as JSON string
    custom_fields: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: {"PRAXISNAME": "...", "PROBLEM": "..."}
    
    # ═══════════════════════════════════════════════════════════════
    # STATUS & TRACKING
    # ═══════════════════════════════════════════════════════════════
    status: Mapped[ContactStatus] = mapped_column(SQLEnum(ContactStatus), default=ContactStatus.PENDING)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    mx_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # ═══════════════════════════════════════════════════════════════
    # CAMPAIGN RELATIONSHIP
    # ═══════════════════════════════════════════════════════════════
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id"), nullable=False)
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="contacts")
    
    # ═══════════════════════════════════════════════════════════════
    # SEND TRACKING
    # ═══════════════════════════════════════════════════════════════
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Contact(id={self.id}, email='{self.email}', status={self.status.value})>"
    
    def get_custom_field(self, field_name: str) -> str | None:
        """Get a custom field value."""
        if not self.custom_fields:
            return None
        try:
            fields = json.loads(self.custom_fields)
            return fields.get(field_name)
        except json.JSONDecodeError:
            return None
    
    def set_custom_field(self, field_name: str, value: str) -> None:
        """Set a custom field value."""
        fields: dict[str, str] = {}
        if self.custom_fields:
            try:
                fields = json.loads(self.custom_fields)
            except json.JSONDecodeError:
                pass
        fields[field_name] = value
        self.custom_fields = json.dumps(fields, ensure_ascii=False)
    
    def get_all_fields(self) -> dict[str, Any]:
        """Get all fields including custom fields for template rendering."""
        result: dict[str, Any] = {
            "EMAIL": self.email,
            "COMPANY": self.company_name or "",
            "NAME": self.contact_name or "",
            "DOMAIN": self.domain or "",
        }
        
        if self.custom_fields:
            try:
                custom = json.loads(self.custom_fields)
                result.update(custom)
            except json.JSONDecodeError:
                pass
        
        return result
    
    def to_dict(self) -> dict[str, Any]:
        """Convert contact to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "domain": self.domain,
            "status": self.status.value,
            "is_valid": self.is_valid,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }
