"""
Obscuras Campaign Manager - License Model
Manages trial period and license validation.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from models.database import Base
from utils.logging_config import get_logger

logger = get_logger("models.license")


class LicenseType:
    """License type constants."""
    TRIAL = "trial"
    PRO = "pro"
    EXPIRED = "expired"


class License(Base):
    """License model for managing trial and paid licenses."""
    
    __tablename__ = "license"
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FIELDS
    # ═══════════════════════════════════════════════════════════════
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # License type: trial, pro, expired
    license_type: Mapped[str] = mapped_column(String(50), default=LicenseType.TRIAL)
    
    # Trial period
    trial_start: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc)
    )
    trial_days: Mapped[int] = mapped_column(Integer, default=14)
    
    # Pro license (after payment)
    license_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    license_valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # STRIPE INTEGRATION
    # ═══════════════════════════════════════════════════════════════
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # LIMITS (Trial)
    # ═══════════════════════════════════════════════════════════════
    max_campaigns_trial: Mapped[int] = mapped_column(Integer, default=3)
    max_emails_per_day_trial: Mapped[int] = mapped_column(Integer, default=300)
    
    # ═══════════════════════════════════════════════════════════════
    # USAGE TRACKING
    # ═══════════════════════════════════════════════════════════════
    emails_sent_today: Mapped[int] = mapped_column(Integer, default=0)
    last_email_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    def __repr__(self) -> str:
        return f"<License(type={self.license_type}, valid_until={self.license_valid_until})>"
    
    # ═══════════════════════════════════════════════════════════════
    # TRIAL METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _ensure_aware(self, dt: datetime | None) -> datetime | None:
        """Ensure datetime is timezone-aware (UTC)."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @property
    def trial_end_date(self) -> datetime:
        """Calculate trial end date."""
        trial_start = self._ensure_aware(self.trial_start) or datetime.now(timezone.utc)
        return trial_start + timedelta(days=self.trial_days)
    
    @property
    def trial_days_remaining(self) -> int:
        """Calculate remaining trial days."""
        if self.license_type == LicenseType.PRO:
            return -1  # Pro license, no trial
        
        now = datetime.now(timezone.utc)
        remaining = (self.trial_end_date - now).days
        return max(0, remaining)
    
    @property
    def is_trial_expired(self) -> bool:
        """Check if trial has expired."""
        return self.trial_days_remaining <= 0 and self.license_type == LicenseType.TRIAL
    
    # ═══════════════════════════════════════════════════════════════
    # LICENSE VALIDATION
    # ═══════════════════════════════════════════════════════════════
    
    @property
    def is_valid(self) -> bool:
        """Check if license is currently valid (trial or pro)."""
        if self.license_type == LicenseType.PRO:
            if self.license_valid_until:
                valid_until = self._ensure_aware(self.license_valid_until)
                return datetime.now(timezone.utc) < valid_until # pyright: ignore[reportOperatorIssue]
            return True  # No expiry set
        
        return not self.is_trial_expired
    
    @property
    def is_pro(self) -> bool:
        """Check if this is a pro license."""
        return self.license_type == LicenseType.PRO and self.is_valid
    
    # ═══════════════════════════════════════════════════════════════
    # LIMIT CHECKS
    # ═══════════════════════════════════════════════════════════════
    
    def can_create_campaign(self, current_campaign_count: int) -> bool:
        """Check if user can create a new campaign."""
        if self.is_pro:
            return True
        
        if not self.is_valid:
            return False
        
        return current_campaign_count < self.max_campaigns_trial
    
    def can_send_email(self) -> bool:
        """Check if user can send an email today."""
        if self.is_pro:
            return True
        
        if not self.is_valid:
            return False
        
        # Reset counter if new day
        self._reset_daily_counter_if_needed()
        
        return self.emails_sent_today < self.max_emails_per_day_trial
    
    def get_remaining_emails_today(self) -> int:
        """Get remaining emails for today."""
        if self.is_pro:
            return -1  # Unlimited
        
        self._reset_daily_counter_if_needed()
        return max(0, self.max_emails_per_day_trial - self.emails_sent_today)
    
    def record_email_sent(self) -> None:
        """Record an email was sent."""
        self._reset_daily_counter_if_needed()
        self.emails_sent_today += 1
        self.last_email_date = datetime.now(timezone.utc)
    
    def _reset_daily_counter_if_needed(self) -> None:
        """Reset daily email counter if it's a new day."""
        now = datetime.now(timezone.utc)
        if self.last_email_date:
            last_date = self._ensure_aware(self.last_email_date)
            if last_date and last_date.date() < now.date():
                self.emails_sent_today = 0
    
    # ═══════════════════════════════════════════════════════════════
    # PRO LICENSE ACTIVATION
    # ═══════════════════════════════════════════════════════════════
    
    def activate_pro_license(
        self, 
        license_key: str, 
        valid_for_days: int = 365,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None
    ) -> None:
        """Activate a pro license."""
        self.license_type = LicenseType.PRO
        self.license_key = license_key
        self.license_valid_until = datetime.now(timezone.utc) + timedelta(days=valid_for_days)
        
        if stripe_customer_id:
            self.stripe_customer_id = stripe_customer_id
        if stripe_subscription_id:
            self.stripe_subscription_id = stripe_subscription_id
        
        logger.info(f"Pro-Lizenz aktiviert bis {self.license_valid_until}")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "license_type": self.license_type,
            "is_valid": self.is_valid,
            "is_pro": self.is_pro,
            "trial_days_remaining": self.trial_days_remaining,
            "trial_end_date": self.trial_end_date.isoformat() if self.trial_end_date else None,
            "license_valid_until": self.license_valid_until.isoformat() if self.license_valid_until else None,
            "emails_sent_today": self.emails_sent_today,
            "remaining_emails_today": self.get_remaining_emails_today(),
            "max_campaigns_trial": self.max_campaigns_trial,
            "max_emails_per_day_trial": self.max_emails_per_day_trial,
        }
