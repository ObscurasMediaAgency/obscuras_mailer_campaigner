"""
Obscuras Campaign Manager - Stripe Service
Handles payment processing and subscription management.
"""

import os
import webbrowser
from typing import Optional, Any

import stripe

from utils.logging_config import get_logger
from utils.license_service import get_license_service, LicenseService

logger = get_logger("utils.stripe_service")


class StripeService:
    """Service for Stripe payment integration."""
    
    # Product info
    PRODUCT_NAME = "Obscuras Campaign Manager Pro"
    PRODUCT_PRICE_EUR = 129.00
    LICENSE_DURATION_DAYS = 365
    
    # Singleton
    _instance: Optional["StripeService"] = None
    
    def __new__(cls) -> "StripeService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        self._api_key: str | None = None
        self._publishable_key: str | None = None
        self._price_id: str | None = None
        self._is_configured = False
        self._load_config()
    
    def _load_config(self) -> None:
        """Load Stripe configuration from environment or config file."""
        # Try environment variables first
        self._api_key = os.environ.get("STRIPE_SECRET_KEY")
        self._publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
        self._price_id = os.environ.get("STRIPE_PRICE_ID")
        
        # Try config file if env vars not set
        if not self._api_key:
            try:
                import yaml
                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "config/stripe.yaml"
                )
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        if config:
                            self._api_key = config.get("secret_key")
                            self._publishable_key = config.get("publishable_key")
                            self._price_id = config.get("price_id")
            except Exception as e:
                logger.debug(f"Keine Stripe-Konfiguration gefunden: {e}")
        
        if self._api_key:
            stripe.api_key = self._api_key
            self._is_configured = True
            logger.info("Stripe konfiguriert")
        else:
            logger.warning("Stripe nicht konfiguriert - Zahlungen deaktiviert")
    
    @property
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return self._is_configured and bool(self._api_key)
    
    def configure(
        self, 
        secret_key: str, 
        publishable_key: str, 
        price_id: str | None = None
    ) -> None:
        """Configure Stripe with API keys."""
        self._api_key = secret_key
        self._publishable_key = publishable_key
        self._price_id = price_id
        
        stripe.api_key = secret_key
        self._is_configured = True
        
        # Save to config file
        self._save_config()
        logger.info("Stripe erfolgreich konfiguriert")
    
    def _save_config(self) -> None:
        """Save Stripe configuration to file."""
        import yaml
        
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config/stripe.yaml"
        )
        
        config = {
            "secret_key": self._api_key,
            "publishable_key": self._publishable_key,
            "price_id": self._price_id,
        }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
    
    # ═══════════════════════════════════════════════════════════════
    # CHECKOUT
    # ═══════════════════════════════════════════════════════════════
    
    def create_checkout_session(
        self,
        customer_email: str | None = None,
        success_url: str = "https://obscuras-media-agency.de/payment/success",
        cancel_url: str = "https://obscuras-media-agency.de/payment/cancel"
    ) -> tuple[bool, str]:
        """
        Create a Stripe Checkout session.
        Returns (success, checkout_url_or_error).
        """
        if not self.is_configured:
            return False, "Stripe ist nicht konfiguriert. Bitte API-Keys hinterlegen."
        
        try:
            # Create checkout session
            checkout_params: dict[str, Any] = {
                "payment_method_types": ["card"],
                "mode": "payment",
                "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
                "cancel_url": cancel_url,
                "line_items": [{
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": self.PRODUCT_NAME,
                            "description": f"Jahreslizenz - {self.LICENSE_DURATION_DAYS} Tage gültig",
                        },
                        "unit_amount": int(self.PRODUCT_PRICE_EUR * 100),  # In Cents
                    },
                    "quantity": 1,
                }],
                "metadata": {
                    "product": "campaign_manager_pro",
                    "license_days": str(self.LICENSE_DURATION_DAYS),
                },
            }
            
            if customer_email:
                checkout_params["customer_email"] = customer_email
            
            # Use price_id if configured (for recurring subscriptions)
            if self._price_id:
                checkout_params["mode"] = "subscription"  # Switch to subscription mode
                checkout_params["line_items"] = [{
                    "price": self._price_id,
                    "quantity": 1,
                }]
            
            session = stripe.checkout.Session.create(**checkout_params)  # type: ignore[arg-type]
            
            logger.info(f"Checkout-Session erstellt: {session.id}")
            return True, str(session.url)
            
        except stripe.StripeError as e:
            logger.error(f"Stripe-Fehler: {e}")
            return False, f"Zahlungsfehler: {e.user_message if hasattr(e, 'user_message') else str(e)}"
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Checkout-Session: {e}")
            return False, f"Fehler: {e}"
    
    def open_checkout(self, customer_email: str | None = None) -> tuple[bool, str]:
        """
        Create checkout session and open in browser.
        Returns (success, message).
        """
        success, result = self.create_checkout_session(customer_email=customer_email)
        
        if success:
            webbrowser.open(result)
            return True, "Zahlungsseite wurde im Browser geöffnet."
        else:
            return False, result
    
    # ═══════════════════════════════════════════════════════════════
    # PAYMENT VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def verify_payment(self, session_id: str) -> tuple[bool, str]:
        """
        Verify a payment session and activate license.
        Returns (success, message).
        """
        if not self.is_configured:
            return False, "Stripe ist nicht konfiguriert"
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == "paid":
                # Activate license
                license_service = get_license_service()
                license_key = LicenseService.generate_license_key()
                
                success, message = license_service.activate_license(
                    license_key=license_key,
                    stripe_customer_id=str(session.customer) if session.customer else None,
                    stripe_subscription_id=str(session.subscription) if session.subscription else None
                )
                
                if success:
                    return True, f"Zahlung erfolgreich! Ihre Lizenz wurde aktiviert.\n\nLizenzschlüssel: {license_key}"
                else:
                    return False, f"Zahlung erfolgreich, aber Lizenzaktivierung fehlgeschlagen: {message}"
            else:
                return False, f"Zahlung nicht abgeschlossen. Status: {session.payment_status}"
                
        except stripe.StripeError as e:
            logger.error(f"Stripe-Fehler bei Verifizierung: {e}")
            return False, f"Fehler bei der Verifizierung: {e}"
    
    # ═══════════════════════════════════════════════════════════════
    # MANUAL LICENSE ACTIVATION
    # ═══════════════════════════════════════════════════════════════
    
    def activate_with_key(self, license_key: str) -> tuple[bool, str]:
        """
        Manually activate a license with a key.
        Returns (success, message).
        """
        # For now, accept any 16-char key format (XXXX-XXXX-XXXX-XXXX)
        # In production, validate against a server
        key_clean = license_key.replace("-", "").replace(" ", "").upper()
        
        if len(key_clean) != 16 or not key_clean.isalnum():
            return False, "Ungültiges Lizenzschlüssel-Format. Erwartet: XXXX-XXXX-XXXX-XXXX"
        
        license_service = get_license_service()
        return license_service.activate_license(license_key=license_key)


# Global instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get the global Stripe service instance."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service
