"""
Obscuras Campaign Manager - Utility Functions
Helper functions for email validation, encryption, and template rendering.
"""

from typing import Optional, Tuple

import dns.resolver
from email_validator import validate_email as ev_validate, EmailNotValidError
from utils.logging_config import get_logger

logger = get_logger("utils.email_validator")


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate an email address format.
    
    Args:
        email: The email address to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, normalized_email or error_message)
    """
    try:
        result = ev_validate(email, check_deliverability=False)
        logger.debug(f"E-Mail validiert: {email} → {result.normalized}")
        return True, result.normalized
    except EmailNotValidError as e:
        logger.warning(f"E-Mail ungültig: {email} - {e}")
        return False, str(e)


def check_mx_record(domain: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a domain has valid MX records.
    
    Args:
        domain: The domain to check
        
    Returns:
        Tuple[bool, Optional[str]]: (has_mx, first_mx_host or None)
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        if mx_records:
            # Return the highest priority MX record
            mx_host = str(sorted(mx_records, key=lambda x: x.preference)[0].exchange)
            logger.debug(f"MX-Record gefunden für {domain}: {mx_host}")
            return True, mx_host.rstrip('.')
        logger.warning(f"Keine MX-Records für {domain}")
        return False, None
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers) as e:
        logger.warning(f"DNS-Fehler für {domain}: {type(e).__name__}")
        return False, None
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei MX-Check für {domain}: {e}")
        return False, None


def validate_email_full(email: str) -> Tuple[bool, str, bool]:
    """
    Perform full email validation including MX record check.
    
    Args:
        email: The email address to validate
        
    Returns:
        Tuple[bool, str, bool]: (is_valid, message, has_mx)
    """
    # First validate format
    is_valid, result = validate_email(email)
    if not is_valid:
        return False, result, False
    
    # Extract domain
    domain = result.split('@')[1]
    
    # Check MX records
    has_mx, mx_host = check_mx_record(domain)
    if not has_mx:
        return True, f"Warnung: Keine MX-Records für {domain}", False
    
    return True, f"Valid (MX: {mx_host})", True
