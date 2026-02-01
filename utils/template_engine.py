"""
Obscuras Campaign Manager - Template Engine
Jinja2-based template rendering for emails.
"""

import re
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateNotFound
from utils.logging_config import get_logger

logger = get_logger("utils.template_engine")


# ═══════════════════════════════════════════════════════════════════
# TEMPLATE PATHS
# ═══════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"


# ═══════════════════════════════════════════════════════════════════
# CUSTOM LOADER FOR DATABASE TEMPLATES
# ═══════════════════════════════════════════════════════════════════

class StringLoader(BaseLoader):
    """Load templates from strings (for database-stored templates)."""
    
    def __init__(self, templates: Dict[str, str]):
        self.templates = templates
    
    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str, Callable[[], bool]]:
        if template in self.templates:
            source = self.templates[template]
            return source, template, lambda: True
        raise TemplateNotFound(template)


# ═══════════════════════════════════════════════════════════════════
# TEMPLATE ENGINE
# ═══════════════════════════════════════════════════════════════════

class TemplateEngine:
    """Template engine for rendering email content."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template engine.
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR
        
        # File-based environment
        self.file_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
        )
        
        # String-based environment (for dynamic templates)
        self.string_env = Environment(autoescape=True)
    
    def render_file_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template from file.
        
        Args:
            template_name: Name of the template file
            context: Dictionary of variables to replace
            
        Returns:
            str: Rendered template
        """
        template = self.file_env.get_template(template_name)
        return template.render(**context)
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template from string.
        
        Args:
            template_string: Template content as string
            context: Dictionary of variables to replace
            
        Returns:
            str: Rendered template
        """
        # Convert {{VAR}} syntax to Jinja2 {{ VAR }} if needed
        template_string = self._normalize_placeholders(template_string)
        template = self.string_env.from_string(template_string)
        return template.render(**context)
    
    def _normalize_placeholders(self, content: str) -> str:
        """
        Normalize placeholder syntax.
        Converts {{VAR}} to {{ VAR }} for Jinja2 compatibility.
        """
        # Already Jinja2 format - just ensure spacing
        return re.sub(r'\{\{\s*(\w+)\s*\}\}', r'{{ \1 }}', content)
    
    @staticmethod
    def extract_variables(template_string: str) -> List[str]:
        """
        Extract all variable names from a template.
        
        Args:
            template_string: Template content
            
        Returns:
            List[str]: List of variable names found
        """
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        matches = re.findall(pattern, template_string)
        return list(set(matches))


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

_engine: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    """Get singleton template engine instance."""
    global _engine
    if _engine is None:
        _engine = TemplateEngine()
    return _engine


def render_template(template: str, context: Dict[str, Any], is_file: bool = False) -> str:
    """
    Render a template with the given context.
    
    Args:
        template: Template string or filename
        context: Dictionary of variables
        is_file: If True, treat template as filename
        
    Returns:
        str: Rendered content
    """
    engine = get_template_engine()
    try:
        if is_file:
            logger.debug(f"Rendere Template-Datei: {template}")
            return engine.render_file_template(template, context)
        logger.debug(f"Rendere Template-String ({len(template)} Zeichen)")
        return engine.render_string(template, context)
    except Exception as e:
        logger.error(f"Template-Rendering fehlgeschlagen: {e}")
        raise


def render_email(
    html_template: str,
    text_template: str,
    contact_data: Dict[str, Any],
    campaign_data: Dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Render both HTML and text versions of an email.
    
    Args:
        html_template: HTML template string
        text_template: Plain text template string
        contact_data: Contact-specific variables
        campaign_data: Campaign-wide variables
        
    Returns:
        Tuple[str, str]: (rendered_html, rendered_text)
    """
    # Merge contexts
    context: Dict[str, Any] = {}
    if campaign_data:
        context.update(campaign_data)
    context.update(contact_data)
    
    engine = get_template_engine()
    html = engine.render_string(html_template, context)
    text = engine.render_string(text_template, context)
    
    return html, text
