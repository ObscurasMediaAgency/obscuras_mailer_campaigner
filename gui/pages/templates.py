"""
Obscuras Campaign Manager - Templates Page
Email template management with HTML editor and preview.
"""

import os
from typing import Any, cast

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QComboBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QSplitter, QTabWidget,
    QPlainTextEdit, QGroupBox, QCheckBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.template import Template

# Optional: WebEngine for live preview
_has_webengine = False
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    _has_webengine = True
except ImportError:
    QWebEngineView = None  # type: ignore[misc, assignment]


def load_company_settings() -> dict[str, Any]:
    """Load company settings from YAML."""
    import yaml
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config/company.yaml"
    )
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                result: Any = yaml.safe_load(f)
                if isinstance(result, dict):
                    return cast(dict[str, Any], result)
                return {}
        except Exception:
            pass
    return {}


class TemplateEditorDialog(QDialog):
    """Dialog for creating/editing email templates."""
    
    def __init__(self, template: Template | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("Neues Template" if not template else "Template bearbeiten")
        self.setMinimumSize(900, 700)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # ═══════════════════════════════════════════════════════════
        # BASIC INFO
        # ═══════════════════════════════════════════════════════════
        info_layout = QHBoxLayout()
        
        name_layout = QVBoxLayout()
        name_label = QLabel("Template-Name:")
        name_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        name_layout.addWidget(name_label)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("z.B. Arztpraxen - Modernisierung")
        name_layout.addWidget(self.name_edit)
        info_layout.addLayout(name_layout, stretch=2)
        
        category_layout = QVBoxLayout()
        category_label = QLabel("Kategorie:")
        category_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        category_layout.addWidget(category_label)
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Allgemein", "Ärzte", "Kanzleien", "Immobilien", "Andere"])
        self.category_combo.setEditable(True)
        category_layout.addWidget(self.category_combo)
        info_layout.addLayout(category_layout, stretch=1)
        
        layout.addLayout(info_layout)
        
        # ═══════════════════════════════════════════════════════════
        # SUBJECT LINE
        # ═══════════════════════════════════════════════════════════
        subject_label = QLabel("Betreffzeile:")
        subject_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        layout.addWidget(subject_label)
        
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("Betreff mit {{VARIABLEN}}")
        layout.addWidget(self.subject_edit)
        
        # ═══════════════════════════════════════════════════════════
        # EDITOR WITH PREVIEW
        # ═══════════════════════════════════════════════════════════
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Editor tabs
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_tabs = QTabWidget()
        
        # HTML Tab
        html_tab = QWidget()
        html_layout = QVBoxLayout(html_tab)
        html_layout.setContentsMargins(0, 0, 0, 0)
        
        self.html_editor = QPlainTextEdit()
        self.html_editor.setPlaceholderText("HTML-Inhalt hier einfügen...")
        self.html_editor.setFont(QFont("Consolas", 11))
        self.html_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0a0a0f;
                color: #fafafa;
                border: 1px solid #27272a;
                border-radius: 8px;
            }
        """)
        html_layout.addWidget(self.html_editor)
        
        editor_tabs.addTab(html_tab, "HTML")
        
        # Plain Text Tab
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_editor = QPlainTextEdit()
        self.text_editor.setPlaceholderText("Plaintext-Version hier...")
        self.text_editor.setFont(QFont("Consolas", 11))
        text_layout.addWidget(self.text_editor)
        
        editor_tabs.addTab(text_tab, "Plaintext")
        
        # Header/Footer Tab
        header_footer_tab = QWidget()
        hf_layout = QVBoxLayout(header_footer_tab)
        hf_layout.setContentsMargins(8, 8, 8, 8)
        hf_layout.setSpacing(16)
        
        # Info label
        info_label = QLabel("⚙️ Header und Footer werden aus den Firmeneinstellungen geladen.")
        info_label.setStyleSheet("color: #71717a; font-size: 12px;")
        info_label.setWordWrap(True)
        hf_layout.addWidget(info_label)
        
        # Header options
        header_group = QGroupBox("E-Mail Header")
        header_form = QFormLayout(header_group)
        header_form.setContentsMargins(12, 16, 12, 12)
        header_form.setSpacing(12)
        
        self.show_logo = QCheckBox("Logo anzeigen")
        self.show_logo.setChecked(True)
        header_form.addRow(self.show_logo)
        
        self.show_company_name = QCheckBox("Firmennamen anzeigen")
        self.show_company_name.setChecked(True)
        header_form.addRow(self.show_company_name)
        
        self.show_tagline = QCheckBox("Tagline/Slogan anzeigen")
        self.show_tagline.setChecked(False)
        header_form.addRow(self.show_tagline)
        
        self.header_bg_color = QLineEdit()
        self.header_bg_color.setPlaceholderText("#1a1a2e (leer = Standard)")
        self.header_bg_color.setMaximumWidth(200)
        header_form.addRow("Hintergrundfarbe:", self.header_bg_color)
        
        hf_layout.addWidget(header_group)
        
        # Footer options
        footer_group = QGroupBox("E-Mail Footer")
        footer_form = QFormLayout(footer_group)
        footer_form.setContentsMargins(12, 16, 12, 12)
        footer_form.setSpacing(12)
        
        self.show_footer = QCheckBox("Footer anzeigen")
        self.show_footer.setChecked(True)
        footer_form.addRow(self.show_footer)
        
        self.show_address = QCheckBox("Adresse im Footer")
        self.show_address.setChecked(True)
        footer_form.addRow(self.show_address)
        
        self.show_contact = QCheckBox("Kontaktdaten im Footer")
        self.show_contact.setChecked(True)
        footer_form.addRow(self.show_contact)
        
        self.show_social = QCheckBox("Social Media Links")
        self.show_social.setChecked(False)
        footer_form.addRow(self.show_social)
        
        self.show_legal = QCheckBox("Rechtliche Hinweise (Impressum)")
        self.show_legal.setChecked(True)
        footer_form.addRow(self.show_legal)
        
        self.show_unsubscribe = QCheckBox("Abmelde-Hinweis")
        self.show_unsubscribe.setChecked(True)
        footer_form.addRow(self.show_unsubscribe)
        
        hf_layout.addWidget(footer_group)
        
        # Open company settings button
        open_settings_btn = QPushButton("⚙️ Firmeneinstellungen bearbeiten")
        open_settings_btn.clicked.connect(self._open_company_settings)
        hf_layout.addWidget(open_settings_btn)
        
        hf_layout.addStretch()
        
        editor_tabs.addTab(header_footer_tab, "Header/Footer")
        
        editor_layout.addWidget(editor_tabs)
        splitter.addWidget(editor_widget)
        
        # Right: Preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_header = QWidget()
        preview_header_layout = QHBoxLayout(preview_header)
        preview_header_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("Vorschau")
        preview_label.setStyleSheet("color: #a1a1aa; font-weight: 500;")
        preview_header_layout.addWidget(preview_label)
        
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self._update_preview)
        preview_header_layout.addWidget(refresh_btn)
        
        preview_layout.addWidget(preview_header)
        
        if _has_webengine and QWebEngineView is not None:
            self.preview: QTextEdit | Any = QWebEngineView()
            self.preview.setHtml("<html><body style='background:#18181b;color:#fafafa;padding:20px;'><p>Vorschau wird geladen...</p></body></html>")
        else:
            self.preview = QTextEdit()
            self.preview.setReadOnly(True)
            self.preview.setPlaceholderText("HTML-Vorschau (WebEngine nicht verfügbar)")
        
        preview_layout.addWidget(self.preview)
        splitter.addWidget(preview_widget)
        
        splitter.setSizes([500, 400])
        layout.addWidget(splitter)
        
        # ═══════════════════════════════════════════════════════════
        # VARIABLES INFO
        # ═══════════════════════════════════════════════════════════
        vars_group = QGroupBox("Verfügbare Variablen")
        vars_layout = QHBoxLayout(vars_group)
        
        variables = ["{{EMAIL}}", "{{FIRMA}}", "{{DOMAIN}}", "{{PRAXISNAME}}", "{{PROBLEM}}", "{{YEAR}}"]
        for var in variables:
            var_btn = QPushButton(var)
            var_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27272a;
                    border: 1px solid #3f3f46;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: monospace;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3f3f46;
                }
            """)
            var_btn.clicked.connect(lambda _checked: self._insert_variable(var))  # type: ignore[arg-type]
            vars_layout.addWidget(var_btn)
        
        vars_layout.addStretch()
        layout.addWidget(vars_group)
        
        # ═══════════════════════════════════════════════════════════
        # BUTTONS
        # ═══════════════════════════════════════════════════════════
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Connect preview update
        self.html_editor.textChanged.connect(self._update_preview)
    
    def _insert_variable(self, variable: str):
        """Insert variable at cursor position."""
        self.html_editor.insertPlainText(variable)
        self.html_editor.setFocus()
    
    def _open_company_settings(self):
        """Open company settings dialog."""
        QMessageBox.information(
            self,
            "Firmeneinstellungen",
            "Bitte öffnen Sie die Firmeneinstellungen über das Menü:\n\n"
            "Einstellungen → Firma"
        )
    
    def _generate_header_html(self, company: dict[str, Any]) -> str:
        """Generate HTML header from company settings."""
        branding: dict[str, Any] = company.get('branding', {})
        primary_color: str = str(branding.get('primary_color', '#6366f1'))
        header_bg = self.header_bg_color.text() or '#1a1a2e'
        
        parts: list[str] = []
        parts.append(f'''
        <div style="background-color: {header_bg}; padding: 24px; text-align: center; border-radius: 8px 8px 0 0;">
        ''')
        
        if self.show_logo.isChecked() and branding.get('logo_path'):
            # Logo as inline or placeholder
            parts.append(f'''
            <img src="cid:logo" alt="{branding.get('company_name', 'Logo')}" style="max-height: 60px; margin-bottom: 12px;">
            ''')
        
        if self.show_company_name.isChecked() and branding.get('company_name'):
            parts.append(f'''
            <h1 style="color: #ffffff; font-size: 24px; margin: 0; font-weight: 700;">{branding.get('company_name')}</h1>
            ''')
        
        if self.show_tagline.isChecked() and branding.get('tagline'):
            parts.append(f'''
            <p style="color: {primary_color}; font-size: 14px; margin: 8px 0 0 0;">{branding.get('tagline')}</p>
            ''')
        
        parts.append('</div>')
        
        return ''.join(parts) if len(parts) > 2 else ''
    
    def _generate_footer_html(self, company: dict[str, Any]) -> str:
        """Generate HTML footer from company settings."""
        if not self.show_footer.isChecked():
            return ''
        
        branding: dict[str, Any] = company.get('branding', {})
        contact: dict[str, Any] = company.get('contact', {})
        social: dict[str, Any] = company.get('social', {})
        legal: dict[str, Any] = company.get('legal', {})
        footer_data: dict[str, Any] = company.get('footer', {})
        primary_color: str = str(branding.get('primary_color', '#6366f1'))
        
        parts: list[str] = []
        parts.append('''
        <div style="background-color: #18181b; padding: 24px; margin-top: 24px; border-radius: 0 0 8px 8px; border-top: 1px solid #27272a;">
        ''')
        
        if self.show_contact.isChecked():
            contact_parts: list[str] = []
            if contact.get('email'):
                contact_parts.append(f'✉️ <a href="mailto:{contact["email"]}" style="color: {primary_color};">{contact["email"]}</a>')
            if contact.get('phone'):
                contact_parts.append(f'📞 {contact["phone"]}')
            if contact.get('website'):
                contact_parts.append(f'🌐 <a href="{contact["website"]}" style="color: {primary_color};">{contact["website"]}</a>')
            
            if contact_parts:
                parts.append(f'''
                <p style="color: #a1a1aa; font-size: 13px; margin: 0 0 12px 0; text-align: center;">
                    {' | '.join(contact_parts)}
                </p>
                ''')
        
        if self.show_address.isChecked() and contact.get('address'):
            address = contact['address'].replace('\n', '<br>')
            parts.append(f'''
            <p style="color: #71717a; font-size: 12px; margin: 0 0 12px 0; text-align: center;">
                {address}
            </p>
            ''')
        
        if self.show_social.isChecked():
            social_parts: list[str] = []
            if social.get('linkedin'):
                social_parts.append(f'<a href="{social["linkedin"]}" style="color: {primary_color}; margin: 0 8px;">LinkedIn</a>')
            if social.get('xing'):
                social_parts.append(f'<a href="{social["xing"]}" style="color: {primary_color}; margin: 0 8px;">XING</a>')
            if social.get('facebook'):
                social_parts.append(f'<a href="{social["facebook"]}" style="color: {primary_color}; margin: 0 8px;">Facebook</a>')
            if social.get('instagram'):
                social_parts.append(f'<a href="{social["instagram"]}" style="color: {primary_color}; margin: 0 8px;">Instagram</a>')
            
            if social_parts:
                parts.append(f'''
                <p style="margin: 12px 0; text-align: center;">
                    {''.join(social_parts)}
                </p>
                ''')
        
        if self.show_legal.isChecked():
            legal_parts: list[str] = []
            if legal.get('legal_name'):
                legal_parts.append(legal['legal_name'])
            if legal.get('vat_id'):
                legal_parts.append(f"USt-IdNr.: {legal['vat_id']}")
            if legal.get('register_info'):
                legal_parts.append(legal['register_info'])
            
            if legal_parts:
                parts.append(f'''
                <p style="color: #52525b; font-size: 11px; margin: 12px 0 0 0; text-align: center;">
                    {' • '.join(legal_parts)}
                </p>
                ''')
            
            link_parts: list[str] = []
            if legal.get('imprint_url'):
                link_parts.append(f'<a href="{legal["imprint_url"]}" style="color: #71717a;">Impressum</a>')
            if legal.get('privacy_url'):
                link_parts.append(f'<a href="{legal["privacy_url"]}" style="color: #71717a;">Datenschutz</a>')
            
            if link_parts:
                parts.append(f'''
                <p style="margin: 8px 0 0 0; text-align: center;">
                    {' | '.join(link_parts)}
                </p>
                ''')
        
        if self.show_unsubscribe.isChecked():
            unsubscribe_text = footer_data.get('unsubscribe_text', 'Abmelden')
            footer_text = footer_data.get('text', 'Sie erhalten diese E-Mail, weil Ihre Website öffentlich zugänglich ist.')
            parts.append(f'''
            <hr style="border: none; border-top: 1px solid #27272a; margin: 16px 0;">
            <p style="color: #52525b; font-size: 11px; margin: 0; text-align: center;">
                {footer_text}<br>
                <a href="{{{{UNSUBSCRIBE_URL}}}}" style="color: #71717a;">{unsubscribe_text}</a>
            </p>
            ''')
        
        parts.append('</div>')
        
        return ''.join(parts)
    
    def _update_preview(self):
        """Update the HTML preview with header and footer."""
        html_body = self.html_editor.toPlainText()
        
        # Load company settings
        company = load_company_settings()
        
        # Generate header and footer
        header_html = self._generate_header_html(company)
        footer_html = self._generate_footer_html(company)
        
        # Build full email HTML
        primary_color = company.get('branding', {}).get('primary_color', '#6366f1')
        
        full_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #0a0a0f; }}
        .email-container {{ max-width: 600px; margin: 0 auto; background: #18181b; border-radius: 8px; overflow: hidden; }}
        .email-body {{ padding: 24px; color: #e4e4e7; line-height: 1.6; }}
        a {{ color: {primary_color}; }}
    </style>
</head>
<body>
    <div class="email-container">
        {header_html}
        <div class="email-body">
            {html_body}
        </div>
        {footer_html}
    </div>
</body>
</html>'''
        
        # Replace sample variables for preview
        sample_data = {
            "{{EMAIL}}": "beispiel@domain.de",
            "{{FIRMA}}": "Muster GmbH",
            "{{DOMAIN}}": "muster-gmbh.de",
            "{{PRAXISNAME}}": "Dr. Muster Praxis",
            "{{PROBLEM}}": "Die Website ist nicht mobiloptimiert",
            "{{YEAR}}": "2026",
            "{{UNSUBSCRIBE_URL}}": "#",
        }
        
        for var, value in sample_data.items():
            if var in ["{{UNSUBSCRIBE_URL}}"]:
                full_html = full_html.replace(var, value)
            else:
                full_html = full_html.replace(var, f'<span style="background:{primary_color};padding:2px 4px;border-radius:2px;color:#fff;">{value}</span>')
        
        if _has_webengine:
            self.preview.setHtml(full_html)
        else:
            self.preview.setHtml(full_html)
    
    def get_template_data(self) -> dict[str, Any]:
        """Get form data as dictionary."""
        return {
            "name": self.name_edit.text(),
            "category": self.category_combo.currentText(),
            "subject_template": self.subject_edit.text(),
            "html_content": self.html_editor.toPlainText(),
            "text_content": self.text_editor.toPlainText(),
            "header_options": {
                "show_logo": self.show_logo.isChecked(),
                "show_company_name": self.show_company_name.isChecked(),
                "show_tagline": self.show_tagline.isChecked(),
                "header_bg_color": self.header_bg_color.text(),
            },
            "footer_options": {
                "show_footer": self.show_footer.isChecked(),
                "show_address": self.show_address.isChecked(),
                "show_contact": self.show_contact.isChecked(),
                "show_social": self.show_social.isChecked(),
                "show_legal": self.show_legal.isChecked(),
                "show_unsubscribe": self.show_unsubscribe.isChecked(),
            },
        }


class TemplatesPage(QWidget):
    """Templates management page."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_templates()
    
    def _setup_ui(self):
        """Setup the templates page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # ═══════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("E-Mail Templates")
        title.setStyleSheet("color: #fafafa; font-size: 28px; font-weight: 700;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Category filter
        filter_label = QLabel("Kategorie:")
        filter_label.setStyleSheet("color: #a1a1aa;")
        header_layout.addWidget(filter_label)
        
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Alle", "Ärzte", "Kanzleien", "Immobilien"])
        self.category_filter.setFixedWidth(150)
        header_layout.addWidget(self.category_filter)
        
        self.new_btn = QPushButton("+ Neues Template")
        self.new_btn.setObjectName("primaryButton")
        self.new_btn.clicked.connect(self._create_template)
        header_layout.addWidget(self.new_btn)
        
        layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════
        # TEMPLATES TABLE
        # ═══════════════════════════════════════════════════════════
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Name", "Kategorie", "Betreff", "Verwendet", "Aktionen"
        ])
        
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 150)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        
        layout.addWidget(self.table)
    
    def _load_templates(self):
        """Load templates from database."""
        # Sample data
        templates = [
            ("Arztpraxen - Website", "Ärzte", "Ihre Praxis-Website: Verbesserungspotenzial", 3),
            ("Kanzleien - Mobile", "Kanzleien", "Hinweis zur mobilen Darstellung", 2),
            ("Immobilien - Verwaltung", "Immobilien", "Digitale Hausverwaltung", 1),
            ("Standard Template", "Allgemein", "Kontaktaufnahme", 0),
        ]
        
        self.table.setRowCount(len(templates))
        
        for row, (name, category, subject, usage) in enumerate(templates):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(category))
            self.table.setItem(row, 2, QTableWidgetItem(subject))
            self.table.setItem(row, 3, QTableWidgetItem(f"{usage}x"))
            
            # Actions
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("✎")
            edit_btn.setObjectName("iconButton")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip("Bearbeiten")
            edit_btn.setStyleSheet("font-size: 14px;")
            edit_btn.clicked.connect(lambda _, n=name: self._edit_template(n))  # type: ignore[arg-type]
            actions_layout.addWidget(edit_btn)
            
            copy_btn = QPushButton("⎘")
            copy_btn.setObjectName("iconButton")
            copy_btn.setFixedSize(28, 28)
            copy_btn.setToolTip("Duplizieren")
            copy_btn.setStyleSheet("font-size: 14px;")
            copy_btn.clicked.connect(lambda _, n=name: self._duplicate_template(n))  # type: ignore[arg-type]
            actions_layout.addWidget(copy_btn)
            
            preview_btn = QPushButton("◎")
            preview_btn.setObjectName("iconButton")
            preview_btn.setFixedSize(28, 28)
            preview_btn.setToolTip("Vorschau")
            preview_btn.setStyleSheet("font-size: 14px; color: #6366f1;")
            preview_btn.clicked.connect(lambda _, n=name: self._preview_template(n))  # type: ignore[arg-type]
            actions_layout.addWidget(preview_btn)
            
            delete_btn = QPushButton("✖")
            delete_btn.setObjectName("iconButton")
            delete_btn.setFixedSize(28, 28)
            delete_btn.setToolTip("Löschen")
            delete_btn.setStyleSheet("font-size: 14px; color: #ef4444;")
            delete_btn.clicked.connect(lambda _, n=name: self._delete_template(n))  # type: ignore[arg-type]
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 4, actions)
            self.table.setRowHeight(row, 50)
    
    def _edit_template(self, name: str) -> None:
        """Edit an existing template."""
        QMessageBox.information(
            self,
            "Template bearbeiten",
            f"Template '{name}' bearbeiten.\n(Funktion wird noch implementiert)"
        )
    
    def _duplicate_template(self, name: str) -> None:
        """Duplicate a template."""
        QMessageBox.information(
            self,
            "Template duplizieren",
            f"Template '{name}' duplizieren.\n(Funktion wird noch implementiert)"
        )
    
    def _preview_template(self, name: str) -> None:
        """Preview a template."""
        from PyQt6.QtWidgets import QTextBrowser
        
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(f"Vorschau: {name}")
        preview_dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(preview_dialog)
        
        browser = QTextBrowser()
        browser.setHtml(f"""
        <html>
        <head><style>
            body {{ font-family: Arial; padding: 20px; }}
            h2 {{ color: #333; }}
        </style></head>
        <body>
            <h2>Template: {name}</h2>
            <p>Vorschau wird geladen...</p>
        </body>
        </html>
        """)
        layout.addWidget(browser)
        
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(preview_dialog.close)
        layout.addWidget(close_btn)
        
        preview_dialog.exec()
    
    def _delete_template(self, name: str) -> None:
        """Delete a template."""
        reply = QMessageBox.question(
            self,
            "Template löschen",
            f"Möchten Sie das Template '{name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "Gelöscht",
                f"Template '{name}' wurde gelöscht.\n(Funktion wird noch implementiert)"
            )
            self._load_templates()
    
    def _create_template(self):
        """Open dialog to create new template."""
        dialog = TemplateEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_template_data()
            # TODO: Save to database
            self._load_templates()
            QMessageBox.information(
                self,
                "Template erstellt",
                f"Template '{data['name']}' wurde erstellt."
            )
