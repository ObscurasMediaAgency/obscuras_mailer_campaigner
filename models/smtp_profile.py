"""
Obscuras Campaign Manager - SMTP Profile Model
Stores SMTP server configurations.
"""

from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from models.database import Base

if TYPE_CHECKING:
    from models.campaign import Campaign


class SmtpProfile(Base):
    """SMTP Profile model for storing email server configurations."""
    
    __tablename__ = "smtp_profiles"
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FIELDS
    # ═══════════════════════════════════════════════════════════════
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)  # "Hauptkonto", "Backup"
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # ═══════════════════════════════════════════════════════════════
    # SMTP SERVER SETTINGS
    # ═══════════════════════════════════════════════════════════════
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=465)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=True)
    use_tls: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # ═══════════════════════════════════════════════════════════════
    # AUTHENTICATION
    # ═══════════════════════════════════════════════════════════════
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    # Password is stored encrypted or in keyring
    password_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    use_keyring: Mapped[bool] = mapped_column(Boolean, default=True)  # Use OS keyring for password
    
    # ═══════════════════════════════════════════════════════════════
    # SENDER INFORMATION
    # ═══════════════════════════════════════════════════════════════
    from_name: Mapped[str] = mapped_column(String(255), nullable=False)
    from_email: Mapped[str] = mapped_column(String(320), nullable=False)
    reply_to: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # RATE LIMITS
    # ═══════════════════════════════════════════════════════════════
    max_per_hour: Mapped[int] = mapped_column(Integer, default=50)
    max_per_day: Mapped[int] = mapped_column(Integer, default=500)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=80)
    
    # ═══════════════════════════════════════════════════════════════
    # TRACKING
    # ═══════════════════════════════════════════════════════════════
    total_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_bounced: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════
    campaigns: Mapped[List["Campaign"]] = relationship("Campaign", back_populates="smtp_profile")
    
    def __repr__(self):
        return f"<SmtpProfile(id={self.id}, name='{self.name}', host='{self.host}')>"
    
    def get_password(self) -> str:
        """Get the SMTP password from keyring or encrypted storage."""
        if self.use_keyring:
            import keyring
            password = keyring.get_password("obscuras_campaign_manager", self.username)
            return password or ""
        else:
            from utils.crypto import decrypt_password
            return decrypt_password(self.password_encrypted) if self.password_encrypted else ""
    
    def set_password(self, password: str) -> None:
        """Set the SMTP password in keyring or encrypted storage."""
        if self.use_keyring:
            import keyring
            keyring.set_password("obscuras_campaign_manager", self.username, password)
        else:
            from utils.crypto import encrypt_password
            self.password_encrypted = encrypt_password(password)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert profile to dictionary (without password)."""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "from_name": self.from_name,
            "from_email": self.from_email,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "max_per_hour": self.max_per_hour,
        }
