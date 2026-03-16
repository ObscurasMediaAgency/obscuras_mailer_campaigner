"""
Obscuras Campaign Manager - Template Engine
Jinja2-based template rendering for emails.

Features:
- File and string-based templates
- Custom user templates (templates/custom/)
- Newsletter import with placeholder detection
- Theme configuration support
"""

import re
import os
from typing import Dict, Any, List, Optional, Callable, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateNotFound
from utils.logging_config import get_logger

logger = get_logger("utils.template_engine")


# ═══════════════════════════════════════════════════════════════════
# TEMPLATE PATHS
# ═══════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
CUSTOM_TEMPLATES_DIR = TEMPLATES_DIR / "custom"


# ═══════════════════════════════════════════════════════════════════
# TEMPLATE INFO
# ═══════════════════════════════════════════════════════════════════

def _empty_str_list() -> List[str]:
    return []


def _empty_str_dict() -> Dict[str, str]:
    return {}


@dataclass
class TemplateInfo:
    """Information about a template."""
    name: str
    path: Path
    display_name: str
    is_custom: bool
    description: str = ""
    variables: List[str] = field(default_factory=_empty_str_list)
    
    @property
    def filename(self) -> str:
        return self.path.name


# ═══════════════════════════════════════════════════════════════════
# DEFAULT THEME
# ═══════════════════════════════════════════════════════════════════

DEFAULT_THEME: Dict[str, str] = {
    "THEME_PRIMARY_COLOR": "#3b82f6",
    "THEME_SECONDARY_COLOR": "#8b5cf6",
    "THEME_BG_COLOR": "#f4f4f5",
    "THEME_CARD_BG": "#ffffff",
    "THEME_TEXT_COLOR": "#52525b",
    "THEME_HEADING_COLOR": "#18181b",
    "THEME_MUTED_COLOR": "#71717a",
    "THEME_BORDER_COLOR": "#e4e4e7",
    "THEME_HIGHLIGHT_BG": "#fafafa",
}

DARK_THEME: Dict[str, str] = {
    "THEME_PRIMARY_COLOR": "#6366f1",
    "THEME_SECONDARY_COLOR": "#a855f7",
    "THEME_BG_COLOR": "#0a0a0f",
    "THEME_CARD_BG": "#18181b",
    "THEME_TEXT_COLOR": "#a1a1aa",
    "THEME_HEADING_COLOR": "#fafafa",
    "THEME_MUTED_COLOR": "#71717a",
    "THEME_BORDER_COLOR": "#27272a",
    "THEME_HIGHLIGHT_BG": "#1e1b4b",
    "THEME_ACCENT_COLOR": "linear-gradient(90deg,#6366f1,#a855f7)",
}


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
    
    # Built-in template descriptions (supports .html and .jinja2 extensions)
    BUILTIN_TEMPLATES: Dict[str, str] = {
        "base.html": "Original Obscuras Template (Dark)",
        "base_generic.jinja2": "Generisch (Hell, anpassbar)",
        "base_dark.jinja2": "Modern Dark Theme",
        "base_minimal.jinja2": "Minimalistisch (Klassisch)",
    }
    
    # Supported template extensions
    TEMPLATE_EXTENSIONS = (".html", ".jinja2", ".j2")
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template engine.
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.custom_dir = self.templates_dir / "custom"
        
        # Ensure custom directory exists
        self.custom_dir.mkdir(parents=True, exist_ok=True)
        
        # File-based environment with multiple search paths
        search_paths = [str(self.templates_dir)]
        if self.custom_dir.exists():
            search_paths.insert(0, str(self.custom_dir))  # Custom first
        
        self.file_env = Environment(
            loader=FileSystemLoader(search_paths),
            autoescape=True,
        )
        
        # String-based environment (for dynamic templates)
        self.string_env = Environment(autoescape=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TEMPLATE DISCOVERY
    # ═══════════════════════════════════════════════════════════════
    
    def list_templates(self, include_builtin: bool = True) -> List[TemplateInfo]:
        """
        List all available templates.
        
        Args:
            include_builtin: Include built-in templates
            
        Returns:
            List of TemplateInfo objects
        """
        templates: List[TemplateInfo] = []
        
        # Built-in templates
        if include_builtin:
            for name, description in self.BUILTIN_TEMPLATES.items():
                path = self.templates_dir / name
                if path.exists():
                    display = name.replace("base_", "").replace(".html", "").replace(".jinja2", "").replace(".j2", "").title()
                    if name == "base.html":
                        display = "Obscuras Original"
                    templates.append(TemplateInfo(
                        name=name,
                        path=path,
                        display_name=display,
                        is_custom=False,
                        description=description,
                        variables=self._extract_variables_from_file(path),
                    ))
        
        # Custom templates (all supported extensions)
        if self.custom_dir.exists():
            custom_files: List[Path] = []
            for ext in self.TEMPLATE_EXTENSIONS:
                custom_files.extend(self.custom_dir.glob(f"*{ext}"))
            
            for file in sorted(set(custom_files), key=lambda p: p.name):
                templates.append(TemplateInfo(
                    name=f"custom/{file.name}",
                    path=file,
                    display_name=f"✨ {file.stem}",
                    is_custom=True,
                    description="Benutzerdefiniertes Template",
                    variables=self._extract_variables_from_file(file),
                ))
        
        return templates
    
    def get_template_info(self, template_name: str) -> Optional[TemplateInfo]:
        """Get info about a specific template."""
        for tpl in self.list_templates():
            if tpl.name == template_name or tpl.path.name == template_name:
                return tpl
        return None
    
    def _extract_variables_from_file(self, path: Path) -> List[str]:
        """Extract variables from a template file."""
        try:
            content = path.read_text(encoding="utf-8")
            return self.extract_variables(content)
        except Exception:
            return []
    
    # ═══════════════════════════════════════════════════════════════
    # RENDERING
    # ═══════════════════════════════════════════════════════════════
    
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


# ═══════════════════════════════════════════════════════════════════
# NEWSLETTER IMPORT
# ═══════════════════════════════════════════════════════════════════

# Common placeholder patterns from various newsletter tools
PLACEHOLDER_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    # Mailchimp merge tags
    "mailchimp": [
        (r'\*\|FNAME\|\*', '{{VORNAME}}'),
        (r'\*\|LNAME\|\*', '{{NACHNAME}}'),
        (r'\*\|EMAIL\|\*', '{{EMAIL}}'),
        (r'\*\|COMPANY\|\*', '{{FIRMA}}'),
        (r'\*\|MC:SUBJECT\|\*', '{{EMAIL_SUBJECT}}'),
        (r'\*\|UNSUB\|\*', '{{UNSUBSCRIBE_URL}}'),
        (r'\*\|([A-Z_]+)\|\*', r'{{\1}}'),  # Generic merge tags
    ],
    # Sendinblue / Brevo
    "sendinblue": [
        (r'\{\{contact\.FIRSTNAME\}\}', '{{VORNAME}}'),
        (r'\{\{contact\.LASTNAME\}\}', '{{NACHNAME}}'),
        (r'\{\{contact\.EMAIL\}\}', '{{EMAIL}}'),
        (r'\{\{contact\.COMPANY\}\}', '{{FIRMA}}'),
        (r'\{\{contact\.([A-Z_]+)\}\}', r'{{\1}}'),
    ],
    # HubSpot
    "hubspot": [
        (r'\{\{contact\.firstname\}\}', '{{VORNAME}}'),
        (r'\{\{contact\.lastname\}\}', '{{NACHNAME}}'),
        (r'\{\{contact\.email\}\}', '{{EMAIL}}'),
        (r'\{\{contact\.company\}\}', '{{FIRMA}}'),
        (r'\{\{unsubscribe_link\}\}', '{{UNSUBSCRIBE_URL}}'),
    ],
    # CleverReach
    "cleverreach": [
        (r'\{FIRSTNAME\}', '{{VORNAME}}'),
        (r'\{LASTNAME\}', '{{NACHNAME}}'),
        (r'\{EMAIL\}', '{{EMAIL}}'),
        (r'\{COMPANY\}', '{{FIRMA}}'),
        (r'\{UNSUBSCRIBE\}', '{{UNSUBSCRIBE_URL}}'),
        (r'\{([A-Z_]+)\}', r'{{\1}}'),
    ],
    # Generic patterns
    "generic": [
        (r'%FIRSTNAME%', '{{VORNAME}}'),
        (r'%LASTNAME%', '{{NACHNAME}}'),
        (r'%EMAIL%', '{{EMAIL}}'),
        (r'%COMPANY%', '{{FIRMA}}'),
        (r'%UNSUBSCRIBE%', '{{UNSUBSCRIBE_URL}}'),
        (r'%([A-Z_]+)%', r'{{\1}}'),
        # German variants
        (r'\[VORNAME\]', '{{VORNAME}}'),
        (r'\[NACHNAME\]', '{{NACHNAME}}'),
        (r'\[ANREDE\]', '{{ANREDE}}'),
        (r'\[FIRMA\]', '{{FIRMA}}'),
    ],
}


@dataclass
class ImportResult:
    """Result of a newsletter import."""
    success: bool
    template_path: Optional[Path] = None
    html_content: str = ""
    source_format: str = "unknown"
    original_placeholders: List[str] = field(default_factory=_empty_str_list)
    converted_placeholders: Dict[str, str] = field(default_factory=_empty_str_dict)
    warnings: List[str] = field(default_factory=_empty_str_list)
    error: Optional[str] = None


def detect_placeholder_format(html_content: str) -> str:
    """
    Detect which newsletter tool format is used.
    
    Returns:
        Format name ('mailchimp', 'sendinblue', 'hubspot', 'cleverreach', 'generic', 'unknown')
    """
    # Check for specific patterns
    if re.search(r'\*\|[A-Z_]+\|\*', html_content):
        return "mailchimp"
    if re.search(r'\{\{contact\.[a-z]+\}\}', html_content):
        return "sendinblue"
    if re.search(r'\{\{contact\.[a-z]+\}\}.*\{\{unsubscribe_link\}\}', html_content, re.DOTALL):
        return "hubspot"
    if re.search(r'\{[A-Z_]+\}', html_content):
        return "cleverreach"
    if re.search(r'%[A-Z_]+%', html_content):
        return "generic"
    if re.search(r'\[[A-ZÄÖÜ_]+\]', html_content):
        return "generic"
    
    return "unknown"


def convert_placeholders(
    html_content: str, 
    source_format: Optional[str] = None
) -> Tuple[str, List[str], List[str]]:
    """
    Convert external placeholder formats to Mailer Campaigner format.
    
    Args:
        html_content: HTML content with placeholders
        source_format: Source format (auto-detect if None)
        
    Returns:
        Tuple of (converted_html, original_placeholders, new_placeholders)
    """
    if source_format is None:
        source_format = detect_placeholder_format(html_content)
    
    original_placeholders: List[str] = []
    new_placeholders: List[str] = []
    result = html_content
    
    # Get patterns for the detected format (and always include generic)
    formats_to_try = [source_format, "generic"] if source_format != "generic" else ["generic"]
    
    for fmt in formats_to_try:
        patterns = PLACEHOLDER_PATTERNS.get(fmt, [])
        for pattern, replacement in patterns:
            # Find all matches before replacing
            matches = re.findall(pattern, result)
            if matches:
                for match in matches:
                    if isinstance(match, str):
                        original_placeholders.append(match)
                
                # Apply replacement
                result = re.sub(pattern, replacement, result)
    
    # Extract final placeholders
    new_placeholders = TemplateEngine.extract_variables(result)
    
    return result, list(set(original_placeholders)), new_placeholders


def import_newsletter(
    source: str | Path,
    template_name: Optional[str] = None,
    source_format: Optional[str] = None,
) -> ImportResult:
    """
    Import a newsletter HTML file as a custom template.
    
    Args:
        source: Path to HTML file or HTML content string
        template_name: Name for the new template (auto-generated if None)
        source_format: Source placeholder format (auto-detect if None)
        
    Returns:
        ImportResult with status and details
    """
    warnings: List[str] = []
    html_content: str = ""
    
    # Read content
    source_path: Optional[Path] = None
    if isinstance(source, Path):
        source_path = source
    elif os.path.isfile(source):
        source_path = Path(source)
    
    if source_path is not None:
        try:
            html_content = source_path.read_text(encoding="utf-8")
            if template_name is None:
                template_name = source_path.stem
        except Exception as e:
            return ImportResult(success=False, error=f"Datei konnte nicht gelesen werden: {e}")
    else:
        html_content = str(source)
        if template_name is None:
            template_name = f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Validate HTML
    if "<html" not in html_content.lower() and "<body" not in html_content.lower():
        warnings.append("Kein vollständiges HTML-Dokument erkannt. Wird trotzdem importiert.")
    
    # Detect and convert placeholders
    detected_format = source_format or detect_placeholder_format(html_content)
    if detected_format == "unknown":
        warnings.append("Placeholder-Format nicht erkannt. Bitte manuell prüfen.")
    else:
        logger.info(f"Erkanntes Newsletter-Format: {detected_format}")
    
    converted_html, originals, new_vars = convert_placeholders(html_content, detected_format)
    
    # Build mapping of original to new placeholders
    placeholder_map: Dict[str, str] = {}
    for i, orig in enumerate(originals):
        if i < len(new_vars):
            placeholder_map[orig] = new_vars[i]
    
    # Ensure custom directory exists
    CUSTOM_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    safe_name = re.sub(r'[^\w\-]', '_', template_name)
    target_path = CUSTOM_TEMPLATES_DIR / f"{safe_name}.html"
    
    # Handle existing files
    counter = 1
    while target_path.exists():
        target_path = CUSTOM_TEMPLATES_DIR / f"{safe_name}_{counter}.html"
        counter += 1
    
    # Write template
    try:
        target_path.write_text(converted_html, encoding="utf-8")
        logger.info(f"Newsletter importiert: {target_path}")
    except Exception as e:
        return ImportResult(success=False, error=f"Speichern fehlgeschlagen: {e}")
    
    # Check for missing standard variables
    standard_vars = {"EMAIL_SUBJECT", "SENDER_NAME", "COMPANY_NAME", "CONTENT_BODY"}
    missing = standard_vars - set(new_vars)
    if missing:
        warnings.append(f"Fehlende Standard-Variablen: {', '.join(missing)}")
    
    return ImportResult(
        success=True,
        template_path=target_path,
        html_content=converted_html,
        source_format=detected_format,
        original_placeholders=originals,
        converted_placeholders=placeholder_map,
        warnings=warnings,
    )


def html_to_plaintext(html: str) -> str:
    """
    Convert HTML to plain text for email fallback.
    
    Args:
        html: HTML content
        
    Returns:
        Plain text version
    """
    text = html
    
    # Remove style and script blocks
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert common elements
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</tr>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</h[1-6]>', '\n\n', text, flags=re.IGNORECASE)
    
    # Convert links
    text = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', r'\2 (\1)', text, flags=re.IGNORECASE)
    
    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    text = text.strip()
    
    # Decode HTML entities
    import html as html_module
    text = html_module.unescape(text)
    
    return text


# ═══════════════════════════════════════════════════════════════════
# THEME HELPERS
# ═══════════════════════════════════════════════════════════════════

def get_theme(theme_name: str = "default") -> Dict[str, str]:
    """
    Get theme variables by name.
    
    Args:
        theme_name: 'default', 'dark', or custom theme name
        
    Returns:
        Dictionary of theme variables
    """
    if theme_name == "dark":
        return DARK_THEME.copy()
    return DEFAULT_THEME.copy()


def create_context(
    contact: Dict[str, Any],
    campaign: Optional[Dict[str, Any]] = None,
    company: Optional[Dict[str, Any]] = None,
    theme: str = "default",
) -> Dict[str, Any]:
    """
    Create a full rendering context with all variables.
    
    Args:
        contact: Contact data (EMAIL, VORNAME, NACHNAME, etc.)
        campaign: Campaign data (subject, content, etc.)
        company: Company data (name, url, sender info)
        theme: Theme name
        
    Returns:
        Complete context dictionary
    """
    context: Dict[str, Any] = {}
    
    # Add theme
    context.update(get_theme(theme))
    
    # Add year
    context["YEAR"] = str(datetime.now().year)
    
    # Add company info
    if company:
        context["COMPANY_NAME"] = company.get("name", "")
        context["COMPANY_URL"] = company.get("url", "")
        context["COMPANY_DOMAIN"] = company.get("domain", "")
        context["COMPANY_ADDRESS"] = company.get("address", "")
        context["LOGO_URL"] = company.get("logo_url", "")
        context["SENDER_NAME"] = company.get("sender_name", "")
        context["SENDER_TITLE"] = company.get("sender_title", "")
    
    # Add campaign info
    if campaign:
        context["EMAIL_SUBJECT"] = campaign.get("subject", "")
        context["CONTENT_GREETING"] = campaign.get("greeting", "")
        context["CONTENT_INTRO"] = campaign.get("intro", "")
        context["CONTENT_BODY"] = campaign.get("body", "")
        context["CONTENT_HIGHLIGHT"] = campaign.get("highlight", "")
        context["CONTENT_CTA_TEXT"] = campaign.get("cta_text", "")
        context["CONTENT_CTA_URL"] = campaign.get("cta_url", "")
        context["UNSUBSCRIBE_URL"] = campaign.get("unsubscribe_url", "")
    
    # Add contact info (override any matching keys)
    if contact:
        for key, value in contact.items():
            context[key.upper()] = value
    
    return context


# ═══════════════════════════════════════════════════════════════════
# STANDALONE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

# Global engine instance for convenience functions
_engine: Optional[TemplateEngine] = None


def _get_engine() -> TemplateEngine:
    """Get or create global template engine instance."""
    global _engine
    if _engine is None:
        _engine = TemplateEngine()
    return _engine


def list_templates(include_builtin: bool = True) -> List[TemplateInfo]:
    """
    List all available templates (convenience function).
    
    Args:
        include_builtin: Include built-in templates
        
    Returns:
        List of TemplateInfo objects
    """
    return _get_engine().list_templates(include_builtin=include_builtin)


def get_template_info(template_name: str) -> Optional[TemplateInfo]:
    """
    Get info about a specific template (convenience function).
    
    Args:
        template_name: Name of the template
        
    Returns:
        TemplateInfo or None
    """
    return _get_engine().get_template_info(template_name)


def render_file_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render a template by name (convenience function).
    
    Args:
        template_name: Name of the template file
        context: Dictionary of variables
        
    Returns:
        Rendered template string
    """
    return _get_engine().render_file_template(template_name, context)


def render_string_template(template_string: str, context: Dict[str, Any]) -> str:
    """
    Render a template from string (convenience function).
    
    Args:
        template_string: Template content
        context: Dictionary of variables
        
    Returns:
        Rendered template string
    """
    return _get_engine().render_string(template_string, context)
