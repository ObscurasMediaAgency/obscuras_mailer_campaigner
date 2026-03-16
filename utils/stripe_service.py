"""
Obscuras Campaign Manager - License Server Client
Kommuniziert mit der PHP-API für Zahlungen und Lizenzvalidierung.

Die Stripe-Keys liegen sicher auf dem Server - diese App enthält keine sensiblen Daten.
"""

import hashlib
import os
import platform
import urllib.request
import urllib.error
import json
import webbrowser
from typing import Optional, Any
from datetime import datetime

import yaml

from utils.logging_config import get_logger
from utils.license_service import get_license_service

logger = get_logger("utils.stripe_service")


class StripeService:
    """
    Client für die License Server API.
    
    Kommuniziert mit https://mailer-campaigner.de/api für:
    - Checkout-Session erstellen (Zahlung einleiten)
    - Lizenzschlüssel verifizieren (nach Kauf per E-Mail erhalten)
    - Lizenz aktivieren
    """
    
    # Singleton
    _instance: Optional["StripeService"] = None
    
    def __new__(cls) -> "StripeService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._api_url: str = ""
        self._endpoints: dict[str, str] = {}
        self._product: dict[str, Any] = {}
        self._checkout_urls: dict[str, str] = {}
        self._payment_link: str = ""
        self._timeout: int = 30
        self._is_configured = False
        
        self._load_config()
        self._initialized = True
    
    def _load_config(self) -> None:
        """Load license server configuration from config file."""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config/license_server.yaml"
        )
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                if config:
                    self._api_url = config.get("api_url", "").rstrip("/")
                    self._endpoints = config.get("endpoints", {})
                    self._product = config.get("product", {})
                    self._checkout_urls = config.get("checkout_urls", {})
                    self._payment_link = config.get("payment_link", "")
                    self._timeout = config.get("timeout", 30)
                    
                    # Konfiguriert wenn API-URL oder direkter Payment-Link vorhanden
                    if self._api_url or self._payment_link:
                        self._is_configured = True
                        if self._api_url:
                            logger.info(f"License Server konfiguriert: {self._api_url}")
                        if self._payment_link:
                            logger.info("Direkter Payment-Link konfiguriert")
                    else:
                        logger.warning("License Server URL nicht konfiguriert")
            else:
                logger.warning(f"License Server Konfiguration nicht gefunden: {config_path}")
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der License Server Konfiguration: {e}")
    
    @property
    def is_configured(self) -> bool:
        """Check if the license server or payment link is configured."""
        return self._is_configured and (bool(self._api_url) or bool(self._payment_link))
    
    @property
    def has_payment_link(self) -> bool:
        """Check if a direct payment link is available."""
        return bool(self._payment_link)
    
    @property
    def product_name(self) -> str:
        """Get product name from config."""
        return str(self._product.get("name", "Obscuras Campaign Manager Pro"))
    
    @property
    def product_price(self) -> float:
        """Get product price from config."""
        price = self._product.get("price_eur", 129.00)
        # Handle comma as decimal separator (German format)
        if isinstance(price, str):
            price = float(price.replace(",", "."))
        return float(price)
    
    @property
    def license_duration_days(self) -> int:
        """Get license duration from config."""
        return int(self._product.get("license_duration_days", 365))
    
    # ═══════════════════════════════════════════════════════════════
    # API COMMUNICATION
    # ═══════════════════════════════════════════════════════════════
    
    def _api_request(
        self, 
        endpoint: str, 
        data: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        """
        Make a POST request to the license server API.
        
        Returns:
            (success, response_data)
        """
        if not self.is_configured:
            return False, {"error": "License Server nicht konfiguriert"}
        
        url = f"{self._api_url}{endpoint}"
        
        try:
            # Prepare request
            json_data = json.dumps(data).encode('utf-8')
            request = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'ObscurasCampaignManager/1.0',
                },
                method='POST'
            )
            
            # Make request
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                return True, response_data
                
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode('utf-8'))
                error_msg = error_body.get('error', str(e))
            except Exception:
                error_msg = str(e)
            logger.error(f"API HTTP-Fehler ({url}): {e.code} - {error_msg}")
            return False, {"error": error_msg, "code": e.code}
            
        except urllib.error.URLError as e:
            logger.error(f"API Verbindungsfehler ({url}): {e}")
            return False, {"error": f"Verbindung zum Server fehlgeschlagen: {e.reason}"}
            
        except json.JSONDecodeError as e:
            logger.error(f"API JSON-Fehler: {e}")
            return False, {"error": "Ungültige Server-Antwort"}
            
        except Exception as e:
            logger.error(f"API Fehler: {e}")
            return False, {"error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════
    # CHECKOUT
    # ═══════════════════════════════════════════════════════════════
    
    def create_checkout_session(
        self,
        customer_email: str | None = None
    ) -> tuple[bool, str]:
        """
        Create a checkout session via the license server or use direct payment link.
        
        Order of preference:
        1. API-based checkout (dynamic, with customer email)
        2. Direct Stripe Payment Link (fallback)
        
        Returns:
            (success, checkout_url_or_error)
        """
        if not self.is_configured:
            return False, "License Server nicht konfiguriert. Bitte config/license_server.yaml prüfen."
        
        # Versuche zuerst die API, falls konfiguriert
        if self._api_url:
            endpoint = self._endpoints.get("checkout", "/checkout.php")
            
            data: dict[str, Any] = {}
            if customer_email:
                data["email"] = customer_email
            
            success, response = self._api_request(endpoint, data)
            
            if success and response.get("success"):
                # checkout_url kann direkt oder unter "data" liegen
                checkout_url = response.get("checkout_url", "")
                if not checkout_url:
                    data_obj = response.get("data", {})
                    if isinstance(data_obj, dict):
                        checkout_url = data_obj.get("checkout_url", "")
                
                if checkout_url:
                    logger.info(f"Checkout-Session erstellt für {customer_email or 'unbekannt'}")
                    return True, checkout_url
            
            # API fehlgeschlagen - loggen und Fallback versuchen
            error = response.get("error", "Server nicht erreichbar")
            logger.warning(f"API-Checkout fehlgeschlagen: {error}")
        
        # Fallback: Direkter Payment Link
        if self._payment_link:
            logger.info("Verwende direkten Payment-Link als Fallback")
            return True, self._payment_link
        
        # Kein Fallback verfügbar
        return False, (
            "Checkout nicht verfügbar.\n\n"
            "Der Lizenz-Server ist nicht erreichbar und kein alternativer Payment-Link konfiguriert.\n\n"
            "Bitte kontaktieren Sie support@obscuras-media-agency.de für eine Lizenz."
        )
    
    def open_checkout(self, customer_email: str | None = None) -> tuple[bool, str]:
        """
        Create checkout session and open in browser.
        
        Returns:
            (success, message)
        """
        success, result = self.create_checkout_session(customer_email=customer_email)
        
        if success:
            webbrowser.open(result)
            return True, (
                "Zahlungsseite wurde im Browser geöffnet.\n\n"
                "Nach erfolgreicher Zahlung erhältst du deinen Lizenzschlüssel per E-Mail."
            )
        else:
            return False, result
    
    # ═══════════════════════════════════════════════════════════════
    # LICENSE VERIFICATION & ACTIVATION
    # ═══════════════════════════════════════════════════════════════
    
    def _get_machine_id(self) -> str:
        """Generate a unique machine identifier for license binding."""
        components = [
            platform.node(),           # Hostname
            platform.machine(),        # CPU architecture
            platform.system(),         # OS name
        ]
        
        # Try to get more unique identifiers
        try:
            import uuid
            # Get MAC address
            mac = uuid.getnode()
            components.append(str(mac))
        except Exception:
            pass
        
        combined = "|".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def verify_license_key(self, license_key: str) -> tuple[bool, dict[str, Any]]:
        """
        Verify a license key with the server.
        
        Returns:
            (valid, license_data_or_error)
        """
        if not self.is_configured:
            return False, {"error": "License Server nicht konfiguriert"}
        
        # Format validation
        key_clean = license_key.replace("-", "").replace(" ", "").upper()
        if len(key_clean) != 16 or not key_clean.isalnum():
            return False, {"error": "Ungültiges Lizenzschlüssel-Format. Erwartet: XXXX-XXXX-XXXX-XXXX"}
        
        # Format key properly
        formatted_key = "-".join([key_clean[i:i+4] for i in range(0, 16, 4)])
        
        endpoint = self._endpoints.get("verify", "/verify.php")
        data = {"license_key": formatted_key}
        
        success, response = self._api_request(endpoint, data)
        
        if success and response.get("valid"):
            return True, response
        else:
            error = response.get("error", "Lizenzschlüssel ungültig")
            return False, {"error": error}
    
    def activate_with_key(self, license_key: str) -> tuple[bool, str]:
        """
        Verify and activate a license with a key.
        
        Steps:
        1. Verify key with server
        2. If valid, activate locally and optionally register machine
        
        Returns:
            (success, message)
        """
        # First verify with server
        valid, result = self.verify_license_key(license_key)
        
        if not valid:
            error = result.get("error", "Lizenzschlüssel ungültig")
            return False, error
        
        # Key is valid - activate locally
        license_service = get_license_service()
        
        # Extract expiry date from server response
        expires_str = result.get("expires", "")
        
        # Format key properly
        key_clean = license_key.replace("-", "").replace(" ", "").upper()
        formatted_key = "-".join([key_clean[i:i+4] for i in range(0, 16, 4)])
        
        # Activate in local database
        success, message = license_service.activate_license(
            license_key=formatted_key
        )
        
        if success:
            # Optionally: Register activation with server
            self._register_activation(formatted_key)
            
            expires_display = expires_str
            if expires_str:
                try:
                    # Parse and format date
                    expires_dt = datetime.fromisoformat(expires_str.replace(" ", "T").split("T")[0])
                    expires_display = expires_dt.strftime("%d.%m.%Y")
                except Exception:
                    pass
            
            return True, (
                f"✅ Lizenz erfolgreich aktiviert!\n\n"
                f"Produkt: {self.product_name}\n"
                f"Gültig bis: {expires_display}"
            )
        else:
            return False, message
    
    def _register_activation(self, license_key: str) -> None:
        """
        Register the activation with the server (optional).
        This helps track which machines have activated the license.
        """
        endpoint = self._endpoints.get("activate", "/activate.php")
        machine_id = self._get_machine_id()
        
        data = {
            "license_key": license_key,
            "machine_id": machine_id,
        }
        
        try:
            success, response = self._api_request(endpoint, data)
            if success:
                logger.info(f"Aktivierung registriert für Machine-ID: {machine_id[:8]}...")
            else:
                # Non-critical - don't fail if registration doesn't work
                logger.debug(f"Aktivierungs-Registrierung optional: {response.get('error', 'unbekannt')}")
        except Exception as e:
            logger.debug(f"Aktivierungs-Registrierung fehlgeschlagen (ignoriert): {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # LEGACY COMPATIBILITY
    # ═══════════════════════════════════════════════════════════════
    
    def verify_payment(self, session_id: str) -> tuple[bool, str]:
        """
        Legacy method - no longer used.
        
        Payment verification is now handled server-side via Stripe webhooks.
        The license key is sent to the customer via email.
        """
        return False, (
            "Diese Funktion wird nicht mehr verwendet.\n\n"
            "Nach erfolgreicher Zahlung erhältst du deinen Lizenzschlüssel per E-Mail.\n"
            "Gib den Schlüssel unter 'Einstellungen → Lizenz → Mit Schlüssel aktivieren' ein."
        )
    
    def configure(self, *args: Any, **kwargs: Any) -> None:
        """
        Legacy method - configuration is now read-only from license_server.yaml.
        
        Stripe keys are stored securely on the server, not in the app.
        """
        logger.warning(
            "configure() wird nicht mehr verwendet. "
            "Die Konfiguration erfolgt über config/license_server.yaml"
        )


# Global instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get the global Stripe service instance."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service
