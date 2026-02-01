"""
Obscuras Campaign Manager - Data Models
SQLAlchemy models for campaigns, contacts, and settings.
"""

from models.database import init_database, get_session
from models.campaign import Campaign
from models.contact import Contact
from models.smtp_profile import SmtpProfile
from models.send_log import SendLog

__all__ = [
    "init_database",
    "get_session",
    "Campaign",
    "Contact",
    "SmtpProfile",
    "SendLog",
]
