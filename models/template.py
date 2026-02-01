"""
Obscuras Campaign Manager - Template Model
Stores reusable email templates.
"""

from datetime import datetime, timezone
from typing import Any
import json
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

from models.database import Base
from utils.logging_config import get_logger

logger = get_logger("models.template")


class Template(Base):
    """Template model for storing reusable email templates."""
    
    __tablename__ = "templates"
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FIELDS
    # ═══════════════════════════════════════════════════════════════
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Category for organization (e.g., "Ärzte", "Immobilien", "Kanzleien")
    category = Column(String(100), nullable=True, index=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TEMPLATE CONTENT
    # ═══════════════════════════════════════════════════════════════
    subject_template = Column(String(500), nullable=True)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TEMPLATE VARIABLES
    # ═══════════════════════════════════════════════════════════════
    # List of required variables (stored as JSON array)
    required_variables = Column(Text, nullable=True)  # ["PRAXISNAME", "DOMAIN", "PROBLEM"]
    
    # ═══════════════════════════════════════════════════════════════
    # METADATA
    # ═══════════════════════════════════════════════════════════════
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}', category='{self.category}')>"
    
    def get_required_variables(self) -> list[str]:
        """Get list of required template variables."""
        required_vars: str | None = self.required_variables  # type: ignore[assignment]
        if not required_vars:
            return []
        try:
            return json.loads(required_vars)
        except json.JSONDecodeError:
            return []
    
    def set_required_variables(self, variables: list[str]) -> None:
        """Set list of required template variables."""
        self.required_variables = json.dumps(variables)  # type: ignore[assignment]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "subject_template": self.subject_template,
            "required_variables": self.get_required_variables(),
            "is_active": self.is_active,
            "usage_count": self.usage_count,
        }
