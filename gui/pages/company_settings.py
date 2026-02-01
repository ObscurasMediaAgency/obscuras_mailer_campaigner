"""
Obscuras Campaign Manager - Company Settings Page
Global company branding settings for email templates.
"""

import os
from typing import Any, cast

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QGroupBox, QFormLayout, QScrollArea,
    QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from utils.logging_config import get_logger, log_user_action

logger = get_logger("gui.pages.company_settings")


class CompanySettingsPage(QWidget):
    """Company branding and settings page."""
    
    # Settings file path
    SETTINGS_FILE = "config/company.yaml"
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup the company settings UI."""
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #0a0a0f;")
        
        content = QWidget()
        content.setStyleSheet("background-color: #0a0a0f;")
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # ═══════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        
        title = QLabel("Firmeneinstellungen")
        title.setStyleSheet("color: #fafafa; font-size: 28px; font-weight: 700;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Branding für E-Mail-Header und Footer konfigurieren")
        subtitle.setStyleSheet("color: #71717a; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        save_btn = QPushButton("💾 Speichern")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._save_settings)
        header_layout.addWidget(save_btn)
        
        layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════
        # COMPANY BRANDING
        # ═══════════════════════════════════════════════════════════
        branding_group = QGroupBox("Firmen-Branding")
        branding_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #fafafa;
                border: 1px solid #27272a;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        branding_layout = QFormLayout(branding_group)
        branding_layout.setContentsMargins(20, 24, 20, 20)
        branding_layout.setSpacing(16)
        branding_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Company name
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("z.B. Obscuras Media Agency")
        self.company_name.setMinimumHeight(36)
        branding_layout.addRow("Firmenname:", self.company_name)
        
        # Tagline
        self.tagline = QLineEdit()
        self.tagline.setPlaceholderText("z.B. Digitale Lösungen für Ihren Erfolg")
        self.tagline.setMinimumHeight(36)
        branding_layout.addRow("Tagline/Slogan:", self.tagline)
        
        # Logo
        logo_widget = QWidget()
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(12)
        
        self.logo_path = QLineEdit()
        self.logo_path.setPlaceholderText("Pfad zum Logo (PNG, JPG, max 200x80px)")
        self.logo_path.setMinimumHeight(36)
        self.logo_path.setReadOnly(True)
        logo_layout.addWidget(self.logo_path, stretch=1)
        
        logo_browse_btn = QPushButton("Durchsuchen...")
        logo_browse_btn.setMinimumHeight(36)
        logo_browse_btn.clicked.connect(self._browse_logo)
        logo_layout.addWidget(logo_browse_btn)
        
        branding_layout.addRow("Logo:", logo_widget)
        
        # Logo preview
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(200, 80)
        self.logo_preview.setStyleSheet("""
            QLabel {
                background-color: #18181b;
                border: 1px dashed #3f3f46;
                border-radius: 8px;
            }
        """)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setText("Kein Logo")
        branding_layout.addRow("Vorschau:", self.logo_preview)
        
        # Primary color
        self.primary_color = QLineEdit()
        self.primary_color.setPlaceholderText("#6366f1")
        self.primary_color.setMinimumHeight(36)
        self.primary_color.setMaximumWidth(150)
        branding_layout.addRow("Primärfarbe:", self.primary_color)
        
        layout.addWidget(branding_group)
        
        # ═══════════════════════════════════════════════════════════
        # CONTACT INFORMATION
        # ═══════════════════════════════════════════════════════════
        contact_group = QGroupBox("Kontaktdaten")
        contact_group.setStyleSheet(branding_group.styleSheet())
        contact_layout = QFormLayout(contact_group)
        contact_layout.setContentsMargins(20, 24, 20, 20)
        contact_layout.setSpacing(16)
        contact_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.contact_email = QLineEdit()
        self.contact_email.setPlaceholderText("kontakt@ihre-firma.de")
        self.contact_email.setMinimumHeight(36)
        contact_layout.addRow("E-Mail:", self.contact_email)
        
        self.contact_phone = QLineEdit()
        self.contact_phone.setPlaceholderText("+49 123 456789")
        self.contact_phone.setMinimumHeight(36)
        contact_layout.addRow("Telefon:", self.contact_phone)
        
        self.website = QLineEdit()
        self.website.setPlaceholderText("https://ihre-firma.de")
        self.website.setMinimumHeight(36)
        contact_layout.addRow("Website:", self.website)
        
        self.address = QTextEdit()
        self.address.setPlaceholderText("Musterstraße 123\n12345 Musterstadt\nDeutschland")
        self.address.setMaximumHeight(80)
        contact_layout.addRow("Adresse:", self.address)
        
        layout.addWidget(contact_group)
        
        # ═══════════════════════════════════════════════════════════
        # SOCIAL MEDIA
        # ═══════════════════════════════════════════════════════════
        social_group = QGroupBox("Social Media Links")
        social_group.setStyleSheet(branding_group.styleSheet())
        social_layout = QFormLayout(social_group)
        social_layout.setContentsMargins(20, 24, 20, 20)
        social_layout.setSpacing(16)
        social_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.linkedin = QLineEdit()
        self.linkedin.setPlaceholderText("https://linkedin.com/company/...")
        self.linkedin.setMinimumHeight(36)
        social_layout.addRow("LinkedIn:", self.linkedin)
        
        self.xing = QLineEdit()
        self.xing.setPlaceholderText("https://xing.com/pages/...")
        self.xing.setMinimumHeight(36)
        social_layout.addRow("XING:", self.xing)
        
        self.facebook = QLineEdit()
        self.facebook.setPlaceholderText("https://facebook.com/...")
        self.facebook.setMinimumHeight(36)
        social_layout.addRow("Facebook:", self.facebook)
        
        self.instagram = QLineEdit()
        self.instagram.setPlaceholderText("https://instagram.com/...")
        self.instagram.setMinimumHeight(36)
        social_layout.addRow("Instagram:", self.instagram)
        
        layout.addWidget(social_group)
        
        # ═══════════════════════════════════════════════════════════
        # LEGAL / IMPRESSUM
        # ═══════════════════════════════════════════════════════════
        legal_group = QGroupBox("Rechtliches / Impressum")
        legal_group.setStyleSheet(branding_group.styleSheet())
        legal_layout = QFormLayout(legal_group)
        legal_layout.setContentsMargins(20, 24, 20, 20)
        legal_layout.setSpacing(16)
        legal_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.legal_name = QLineEdit()
        self.legal_name.setPlaceholderText("Vollständiger Firmenname inkl. Rechtsform")
        self.legal_name.setMinimumHeight(36)
        legal_layout.addRow("Rechtlicher Name:", self.legal_name)
        
        self.vat_id = QLineEdit()
        self.vat_id.setPlaceholderText("DE123456789")
        self.vat_id.setMinimumHeight(36)
        legal_layout.addRow("USt-IdNr.:", self.vat_id)
        
        self.register_info = QLineEdit()
        self.register_info.setPlaceholderText("HRB 12345, Amtsgericht Musterstadt")
        self.register_info.setMinimumHeight(36)
        legal_layout.addRow("Handelsregister:", self.register_info)
        
        self.ceo_name = QLineEdit()
        self.ceo_name.setPlaceholderText("Max Mustermann")
        self.ceo_name.setMinimumHeight(36)
        legal_layout.addRow("Geschäftsführer:", self.ceo_name)
        
        self.privacy_url = QLineEdit()
        self.privacy_url.setPlaceholderText("https://ihre-firma.de/datenschutz")
        self.privacy_url.setMinimumHeight(36)
        legal_layout.addRow("Datenschutz-URL:", self.privacy_url)
        
        self.imprint_url = QLineEdit()
        self.imprint_url.setPlaceholderText("https://ihre-firma.de/impressum")
        self.imprint_url.setMinimumHeight(36)
        legal_layout.addRow("Impressum-URL:", self.imprint_url)
        
        layout.addWidget(legal_group)
        
        # ═══════════════════════════════════════════════════════════
        # EMAIL FOOTER SETTINGS
        # ═══════════════════════════════════════════════════════════
        footer_group = QGroupBox("E-Mail Footer")
        footer_group.setStyleSheet(branding_group.styleSheet())
        footer_layout = QFormLayout(footer_group)
        footer_layout.setContentsMargins(20, 24, 20, 20)
        footer_layout.setSpacing(16)
        footer_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.footer_text = QTextEdit()
        self.footer_text.setPlaceholderText(
            "Sie erhalten diese E-Mail, weil Ihre Website {{DOMAIN}} öffentlich zugänglich ist.\n"
            "Wenn Sie keine weiteren E-Mails erhalten möchten, antworten Sie mit 'Abmelden'."
        )
        self.footer_text.setMaximumHeight(100)
        footer_layout.addRow("Footer-Text:", self.footer_text)
        
        self.unsubscribe_text = QLineEdit()
        self.unsubscribe_text.setPlaceholderText("Abmelden")
        self.unsubscribe_text.setMinimumHeight(36)
        footer_layout.addRow("Abmelde-Link Text:", self.unsubscribe_text)
        
        layout.addWidget(footer_group)
        
        # Spacer
        layout.addStretch()
    
    def _browse_logo(self):
        """Open file dialog to select logo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Logo auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.gif *.svg)"
        )
        if file_path:
            self.logo_path.setText(file_path)
            self._update_logo_preview(file_path)
    
    def _update_logo_preview(self, path: str):
        """Update logo preview."""
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    200, 80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_preview.setPixmap(scaled)
            else:
                self.logo_preview.setText("Fehler beim Laden")
        else:
            self.logo_preview.setText("Datei nicht gefunden")
    
    def _load_settings(self):
        """Load settings from YAML file."""
        import yaml
        
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            self.SETTINGS_FILE
        )
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    raw_data: Any = yaml.safe_load(f)
                    data: dict[str, Any] = cast(dict[str, Any], raw_data) if isinstance(raw_data, dict) else {}
                
                # Branding
                branding: dict[str, Any] = cast(dict[str, Any], data.get('branding', {}))
                self.company_name.setText(str(branding.get('company_name', '')))
                self.tagline.setText(str(branding.get('tagline', '')))
                self.logo_path.setText(str(branding.get('logo_path', '')))
                self.primary_color.setText(str(branding.get('primary_color', '#6366f1')))
                
                logo_path_value = str(branding.get('logo_path', ''))
                if logo_path_value:
                    self._update_logo_preview(logo_path_value)
                
                # Contact
                contact: dict[str, Any] = cast(dict[str, Any], data.get('contact', {}))
                self.contact_email.setText(str(contact.get('email', '')))
                self.contact_phone.setText(str(contact.get('phone', '')))
                self.website.setText(str(contact.get('website', '')))
                self.address.setPlainText(str(contact.get('address', '')))
                
                # Social
                social: dict[str, Any] = cast(dict[str, Any], data.get('social', {}))
                self.linkedin.setText(str(social.get('linkedin', '')))
                self.xing.setText(str(social.get('xing', '')))
                self.facebook.setText(str(social.get('facebook', '')))
                self.instagram.setText(str(social.get('instagram', '')))
                
                # Legal
                legal: dict[str, Any] = cast(dict[str, Any], data.get('legal', {}))
                self.legal_name.setText(str(legal.get('legal_name', '')))
                self.vat_id.setText(str(legal.get('vat_id', '')))
                self.register_info.setText(str(legal.get('register_info', '')))
                self.ceo_name.setText(str(legal.get('ceo_name', '')))
                self.privacy_url.setText(str(legal.get('privacy_url', '')))
                self.imprint_url.setText(str(legal.get('imprint_url', '')))
                
                # Footer
                footer: dict[str, Any] = cast(dict[str, Any], data.get('footer', {}))
                self.footer_text.setPlainText(str(footer.get('text', '')))
                self.unsubscribe_text.setText(str(footer.get('unsubscribe_text', 'Abmelden')))
                
                logger.info("Firmeneinstellungen geladen")
                
            except Exception as e:
                logger.error(f"Fehler beim Laden der Einstellungen: {e}")
    
    def _save_settings(self):
        """Save settings to YAML file."""
        import yaml
        
        data = {
            'branding': {
                'company_name': self.company_name.text(),
                'tagline': self.tagline.text(),
                'logo_path': self.logo_path.text(),
                'primary_color': self.primary_color.text() or '#6366f1',
            },
            'contact': {
                'email': self.contact_email.text(),
                'phone': self.contact_phone.text(),
                'website': self.website.text(),
                'address': self.address.toPlainText(),
            },
            'social': {
                'linkedin': self.linkedin.text(),
                'xing': self.xing.text(),
                'facebook': self.facebook.text(),
                'instagram': self.instagram.text(),
            },
            'legal': {
                'legal_name': self.legal_name.text(),
                'vat_id': self.vat_id.text(),
                'register_info': self.register_info.text(),
                'ceo_name': self.ceo_name.text(),
                'privacy_url': self.privacy_url.text(),
                'imprint_url': self.imprint_url.text(),
            },
            'footer': {
                'text': self.footer_text.toPlainText(),
                'unsubscribe_text': self.unsubscribe_text.text() or 'Abmelden',
            }
        }
        
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            self.SETTINGS_FILE
        )
        
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            log_user_action("Firmeneinstellungen gespeichert", "")
            logger.info("Firmeneinstellungen gespeichert")
            
            QMessageBox.information(
                self,
                "Gespeichert",
                "Firmeneinstellungen wurden erfolgreich gespeichert."
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )
    
    def get_company_data(self) -> dict[str, str]:
        """Get all company data as dictionary for use in templates."""
        return {
            'company_name': self.company_name.text(),
            'tagline': self.tagline.text(),
            'logo_path': self.logo_path.text(),
            'primary_color': self.primary_color.text() or '#6366f1',
            'email': self.contact_email.text(),
            'phone': self.contact_phone.text(),
            'website': self.website.text(),
            'address': self.address.toPlainText(),
            'linkedin': self.linkedin.text(),
            'xing': self.xing.text(),
            'facebook': self.facebook.text(),
            'instagram': self.instagram.text(),
            'legal_name': self.legal_name.text(),
            'vat_id': self.vat_id.text(),
            'register_info': self.register_info.text(),
            'ceo_name': self.ceo_name.text(),
            'privacy_url': self.privacy_url.text(),
            'imprint_url': self.imprint_url.text(),
            'footer_text': self.footer_text.toPlainText(),
            'unsubscribe_text': self.unsubscribe_text.text() or 'Abmelden',
        }
    
    def refresh(self):
        """Refresh/reload settings."""
        self._load_settings()
