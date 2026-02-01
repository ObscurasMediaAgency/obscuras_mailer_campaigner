"""
Obscuras Campaign Manager - Cryptography Utilities
Secure password encryption and decryption.
"""

import base64
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from utils.logging_config import get_logger

logger = get_logger("utils.crypto")


# ═══════════════════════════════════════════════════════════════════
# KEY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

KEY_FILE = Path(__file__).parent.parent / "data" / ".secret_key"


def _get_or_create_key() -> bytes:
    """Get existing key or create a new one."""
    if KEY_FILE.exists():
        logger.debug("Vorhandener Schlüssel geladen")
        return KEY_FILE.read_bytes()
    
    # Create data directory if needed
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate new key
    key = Fernet.generate_key()
    
    # Save key with restricted permissions
    KEY_FILE.write_bytes(key)
    KEY_FILE.chmod(0o600)  # Read/write only for owner
    
    logger.info(f"Neuer Verschlüsselungsschlüssel erstellt: {KEY_FILE}")
    return key


def _get_fernet() -> Fernet:
    """Get Fernet instance with the secret key."""
    key = _get_or_create_key()
    return Fernet(key)


# ═══════════════════════════════════════════════════════════════════
# ENCRYPTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def encrypt_password(password: str) -> str:
    """
    Encrypt a password for storage.
    
    Args:
        password: The plaintext password
        
    Returns:
        str: The encrypted password (base64 encoded)
    """
    if not password:
        return ""
    
    fernet = _get_fernet()
    encrypted = fernet.encrypt(password.encode('utf-8'))
    logger.debug("Passwort verschlüsselt")
    return encrypted.decode('utf-8')


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt a stored password.
    
    Args:
        encrypted_password: The encrypted password (base64 encoded)
        
    Returns:
        str: The plaintext password
    """
    if not encrypted_password:
        return ""
    
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_password.encode('utf-8'))
        logger.debug("Passwort entschlüsselt")
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Fehler beim Entschlüsseln des Passworts: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════════
# DERIVED KEY FUNCTIONS (for future use)
# ═══════════════════════════════════════════════════════════════════

def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Derive a cryptographic key from a password.
    
    Args:
        password: The password to derive from
        salt: Optional salt (generated if not provided)
        
    Returns:
        Tuple[bytes, bytes]: (derived_key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return key, salt
