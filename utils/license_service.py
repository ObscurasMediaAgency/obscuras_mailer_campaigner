"""
Obscuras Campaign Manager - License Service
Centralized license management and validation.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Any, cast
import secrets
import hashlib

from models.database import get_session_simple
from models.license import License, LicenseType
from models.campaign import Campaign
from utils.logging_config import get_logger

logger = get_logger("utils.license_service")


class LicenseService:
    """Service for managing licenses and enforcing limits."""
    
    # Singleton instance
    _instance: Optional["LicenseService"] = None
    
    # Cached license data (not ORM object)
    _license_data: dict[str, Any] | None = None
    
    def __new__(cls) -> "LicenseService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if self._license_data is None:
            self._load_or_create_license()
    
    def _load_or_create_license(self) -> None:
        """Load existing license or create trial license."""
        session = get_session_simple()
        try:
            license_obj = session.query(License).first()
            
            if not license_obj:
                # Create new trial license
                license_obj = License(
                    license_type=LicenseType.TRIAL,
                    trial_start=datetime.now(timezone.utc),
                    trial_days=14,
                    max_campaigns_trial=3,
                    max_emails_per_day_trial=300
                )
                session.add(license_obj)
                session.commit()
                logger.info("Neue Trial-Lizenz erstellt")
            
            # Cache license data as dict (not ORM object)
            self._license_data = {
                "id": license_obj.id,
                "license_type": license_obj.license_type,
                "trial_start": license_obj.trial_start,
                "trial_days": license_obj.trial_days,
                "license_key": license_obj.license_key,
                "license_valid_until": license_obj.license_valid_until,
                "stripe_customer_id": license_obj.stripe_customer_id,
                "stripe_subscription_id": license_obj.stripe_subscription_id,
                "max_campaigns_trial": license_obj.max_campaigns_trial,
                "max_emails_per_day_trial": license_obj.max_emails_per_day_trial,
                "emails_sent_today": license_obj.emails_sent_today,
                "last_email_date": license_obj.last_email_date,
            }
            
        finally:
            session.close()
    
    def refresh(self) -> None:
        """Refresh license data from database."""
        self._load_or_create_license()
    
    # ═══════════════════════════════════════════════════════════════
    # LICENSE STATUS
    # ═══════════════════════════════════════════════════════════════
    
    @property
    def _data(self) -> dict[str, Any]:
        """Get cached license data, loading if needed."""
        if self._license_data is None:
            self._load_or_create_license()
        return self._license_data  # type: ignore
    
    @property
    def is_valid(self) -> bool:
        """Check if license is valid."""
        license_type = self._data.get("license_type")
        now = datetime.now(timezone.utc)
        
        if license_type == LicenseType.PRO:
            valid_until_raw = self._data.get("license_valid_until")
            if valid_until_raw:
                valid_until = cast(datetime, valid_until_raw)
                # Handle naive datetime from database
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                return bool(valid_until > now)
            return False
        
        # Trial - check if not expired
        trial_start_raw = self._data.get("trial_start")
        trial_days = int(self._data.get("trial_days", 14))
        
        if trial_start_raw:
            trial_start = cast(datetime, trial_start_raw)
            # Handle naive datetime from database
            if trial_start.tzinfo is None:
                trial_start = trial_start.replace(tzinfo=timezone.utc)
            
            trial_end = trial_start + timedelta(days=trial_days)
            return bool(now < trial_end)
        
        return False
    
    @property
    def is_pro(self) -> bool:
        """Check if this is a pro license."""
        return bool(
            self._data.get("license_type") == LicenseType.PRO 
            and self.is_valid
        )
    
    @property
    def is_trial(self) -> bool:
        """Check if this is a trial license."""
        return bool(
            self._data.get("license_type") == LicenseType.TRIAL 
            and self.is_valid
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if license has expired."""
        return not self.is_valid
    
    @property
    def trial_days_remaining(self) -> int:
        """Get remaining trial days."""
        if self._data.get("license_type") != LicenseType.TRIAL:
            return 0
        
        trial_start_raw = self._data.get("trial_start")
        trial_days = int(self._data.get("trial_days", 14))
        
        if not trial_start_raw:
            return 0
        
        trial_start = cast(datetime, trial_start_raw)
        # Handle naive datetime from database
        if trial_start.tzinfo is None:
            trial_start = trial_start.replace(tzinfo=timezone.utc)
        
        trial_end = trial_start + timedelta(days=trial_days)
        remaining = (trial_end - datetime.now(timezone.utc)).days
        return max(0, remaining)
    
    @property
    def license_type(self) -> str:
        """Get license type string."""
        if self.is_pro:
            return "Pro"
        elif self.is_trial:
            return "Trial"
        else:
            return "Abgelaufen"
    
    # ═══════════════════════════════════════════════════════════════
    # LIMIT CHECKS
    # ═══════════════════════════════════════════════════════════════
    
    def can_create_campaign(self) -> tuple[bool, str]:
        """
        Check if user can create a new campaign.
        Returns (allowed, message).
        """
        if not self.is_valid:
            return False, "Ihre Testversion ist abgelaufen. Bitte upgraden Sie auf Pro."
        
        if self.is_pro:
            return True, ""
        
        # Count existing campaigns
        session = get_session_simple()
        try:
            campaign_count = session.query(Campaign).count()
            max_campaigns = self._data.get("max_campaigns_trial", 3)
            
            if campaign_count >= max_campaigns:
                return False, f"Trial-Limit erreicht: Max. {max_campaigns} Kampagnen. Upgraden Sie auf Pro für unbegrenzte Kampagnen."
            
            remaining = max_campaigns - campaign_count
            return True, f"Noch {remaining} von {max_campaigns} Kampagnen verfügbar"
        finally:
            session.close()
    
    def can_send_email(self) -> tuple[bool, str]:
        """
        Check if user can send an email.
        Returns (allowed, message).
        """
        if not self.is_valid:
            return False, "Ihre Testversion ist abgelaufen. Bitte upgraden Sie auf Pro."
        
        if self.is_pro:
            return True, ""
        
        remaining = self.get_remaining_emails_today()
        
        if remaining <= 0:
            max_emails = self._data.get("max_emails_per_day_trial", 300)
            return False, f"Tageslimit erreicht: Max. {max_emails} E-Mails/Tag. Upgraden Sie auf Pro für unbegrenzte E-Mails."
        
        return True, f"Noch {remaining} E-Mails heute verfügbar"
    
    def get_remaining_emails_today(self) -> int:
        """Get remaining emails for today."""
        # Refresh from DB to get current count
        session = get_session_simple()
        try:
            license_obj = session.query(License).first()
            if license_obj:
                return license_obj.get_remaining_emails_today()
            return 0
        finally:
            session.close()
    
    def record_email_sent(self) -> None:
        """Record that an email was sent."""
        session = get_session_simple()
        try:
            license_obj = session.query(License).first()
            if license_obj:
                license_obj.record_email_sent()
                session.commit()
        finally:
            session.close()
    
    def get_campaign_count(self) -> int:
        """Get current campaign count."""
        session = get_session_simple()
        try:
            return session.query(Campaign).count()
        finally:
            session.close()
    
    def get_max_campaigns(self) -> int:
        """Get max campaigns allowed."""
        if self.is_pro:
            return -1  # Unlimited
        return self._data.get("max_campaigns_trial", 3)
    
    def get_max_emails_per_day(self) -> int:
        """Get max emails per day."""
        if self.is_pro:
            return -1  # Unlimited
        return self._data.get("max_emails_per_day_trial", 300)
    
    # ═══════════════════════════════════════════════════════════════
    # LICENSE ACTIVATION
    # ═══════════════════════════════════════════════════════════════
    
    def activate_license(
        self,
        license_key: str,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None
    ) -> tuple[bool, str]:
        """
        Activate a pro license.
        Returns (success, message).
        """
        session = get_session_simple()
        try:
            license_obj = session.query(License).first()
            if not license_obj:
                return False, "Keine Lizenz gefunden"
            
            license_obj.activate_pro_license(
                license_key=license_key,
                valid_for_days=365,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id
            )
            session.commit()
            
            # Refresh local cache
            self.refresh()
            
            logger.info(f"Lizenz aktiviert: {license_key[:8]}...")
            return True, "Pro-Lizenz erfolgreich aktiviert! Vielen Dank für Ihren Kauf."
            
        except Exception as e:
            session.rollback()
            logger.error(f"Fehler bei Lizenzaktivierung: {e}")
            return False, f"Fehler bei der Aktivierung: {e}"
        finally:
            session.close()
    
    @staticmethod
    def generate_license_key() -> str:
        """Generate a unique license key."""
        random_bytes = secrets.token_bytes(16)
        key_hash = hashlib.sha256(random_bytes).hexdigest()[:32].upper()
        # Format: XXXX-XXXX-XXXX-XXXX
        return f"{key_hash[:4]}-{key_hash[4:8]}-{key_hash[8:12]}-{key_hash[12:16]}"
    
    # ═══════════════════════════════════════════════════════════════
    # STATUS INFO
    # ═══════════════════════════════════════════════════════════════
    
    def get_status_info(self) -> dict[str, Any]:
        """Get comprehensive license status information."""
        campaign_count = self.get_campaign_count()
        max_campaigns = self.get_max_campaigns()
        
        # Get fresh email count from DB
        emails_sent_today = 0
        session = get_session_simple()
        try:
            license_obj = session.query(License).first()
            if license_obj:
                emails_sent_today = license_obj.emails_sent_today
        finally:
            session.close()
        
        return {
            "type": self.license_type,
            "is_valid": self.is_valid,
            "is_pro": self.is_pro,
            "is_trial": self.is_trial,
            "is_expired": self.is_expired,
            "trial_days_remaining": self.trial_days_remaining,
            "campaigns_used": campaign_count,
            "max_campaigns": max_campaigns,
            "campaigns_remaining": max_campaigns - campaign_count if max_campaigns > 0 else -1,
            "emails_sent_today": emails_sent_today,
            "emails_remaining_today": self.get_remaining_emails_today(),
            "max_emails_per_day": self.get_max_emails_per_day(),
            "license_valid_until": self._data.get("license_valid_until"),
        }


# Global instance
_license_service: Optional[LicenseService] = None


def get_license_service() -> LicenseService:
    """Get the global license service instance."""
    global _license_service
    if _license_service is None:
        _license_service = LicenseService()
    return _license_service
