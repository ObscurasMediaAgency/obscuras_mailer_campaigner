"""
Obscuras Campaign Manager - Utilities
Helper functions and shared utilities.
"""

from utils.email_validator import validate_email, check_mx_record
from utils.template_engine import render_template
from utils.crypto import encrypt_password, decrypt_password
from utils.logging_config import (
    setup_logging,
    get_logger,
    get_smtp_logger,
    log_email_sent,
    log_bounce,
    log_campaign_event,
    log_db_operation,
    log_user_action,
    log_function_call,
    log_exceptions,
)

__all__ = [
    # Email validation
    "validate_email",
    "check_mx_record",
    # Template rendering
    "render_template",
    # Encryption
    "encrypt_password",
    "decrypt_password",
    # Logging
    "setup_logging",
    "get_logger",
    "get_smtp_logger",
    "log_email_sent",
    "log_bounce",
    "log_campaign_event",
    "log_db_operation",
    "log_user_action",
    "log_function_call",
    "log_exceptions",
]
