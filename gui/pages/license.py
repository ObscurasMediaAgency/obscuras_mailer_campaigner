"""
Obscuras Campaign Manager - License Page
Displays license status and upgrade options.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QLineEdit, QMessageBox,
    QProgressBar, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt

from utils.logging_config import get_logger
from utils.license_service import get_license_service
from utils.stripe_service import get_stripe_service

logger = get_logger("gui.pages.license")


class LicenseCard(QFrame):
    """Card widget for displaying license information."""
    
    def __init__(self, title: str, value: str, description: str = "",
                 highlight: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        bg_color = "#1a1a2e" if highlight else "#18181b"
        border_color = "#6366f1" if highlight else "#27272a"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #71717a; font-size: 12px; font-weight: 500;")
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 600;")
        layout.addWidget(self.value_label)
        
        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #52525b; font-size: 11px;")
            layout.addWidget(desc_label)
    
    def update_value(self, value: str) -> None:
        """Update the displayed value."""
        self.value_label.setText(value)


class LicensePage(QWidget):
    """License management page."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_license_info()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Header
        header = QLabel("Lizenz")
        header.setStyleSheet("color: #ffffff; font-size: 28px; font-weight: 700;")
        layout.addWidget(header)
        
        # Status card (large)
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 16px;
            }
        """)
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(32, 32, 32, 32)
        status_layout.setSpacing(16)
        
        # Status header row
        status_header = QHBoxLayout()
        
        self.status_label = QLabel("Trial-Version")
        self.status_label.setStyleSheet("color: #fbbf24; font-size: 24px; font-weight: 700;")
        status_header.addWidget(self.status_label)
        
        status_header.addStretch()
        
        self.status_badge = QLabel("AKTIV")
        self.status_badge.setStyleSheet("""
            background-color: #22c55e;
            color: #ffffff;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 10px;
        """)
        status_header.addWidget(self.status_badge)
        
        status_layout.addLayout(status_header)
        
        # Progress bar for trial
        self.trial_progress_container = QWidget()
        trial_progress_layout = QVBoxLayout(self.trial_progress_container)
        trial_progress_layout.setContentsMargins(0, 0, 0, 0)
        trial_progress_layout.setSpacing(8)
        
        self.trial_days_label = QLabel("14 Tage verbleibend")
        self.trial_days_label.setStyleSheet("color: #a1a1aa; font-size: 13px;")
        trial_progress_layout.addWidget(self.trial_days_label)
        
        self.trial_progress = QProgressBar()
        self.trial_progress.setMaximum(14)
        self.trial_progress.setValue(14)
        self.trial_progress.setTextVisible(False)
        self.trial_progress.setFixedHeight(8)
        self.trial_progress.setStyleSheet("""
            QProgressBar {
                background-color: #27272a;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 4px;
            }
        """)
        trial_progress_layout.addWidget(self.trial_progress)
        
        status_layout.addWidget(self.trial_progress_container)
        
        layout.addWidget(self.status_frame)
        
        # Info cards grid
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        
        self.campaigns_card = LicenseCard(
            "Kampagnen",
            "0 / 3",
            "Im Trial maximal 3 Kampagnen"
        )
        cards_row.addWidget(self.campaigns_card)
        
        self.emails_card = LicenseCard(
            "E-Mails heute",
            "0 / 300",
            "Im Trial maximal 300 E-Mails/Tag"
        )
        cards_row.addWidget(self.emails_card)
        
        self.valid_until_card = LicenseCard(
            "Gültig bis",
            "—",
            "Lizenzablaufdatum"
        )
        cards_row.addWidget(self.valid_until_card)
        
        layout.addLayout(cards_row)
        
        # Upgrade section
        upgrade_frame = QFrame()
        upgrade_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e1b4b, stop:1 #312e81
                );
                border: 1px solid #4338ca;
                border-radius: 16px;
            }
        """)
        upgrade_layout = QVBoxLayout(upgrade_frame)
        upgrade_layout.setContentsMargins(32, 24, 32, 24)
        upgrade_layout.setSpacing(16)
        
        upgrade_header = QHBoxLayout()
        
        upgrade_text = QVBoxLayout()
        upgrade_text.setSpacing(4)
        
        upgrade_title = QLabel("⭐ Pro-Lizenz erwerben")
        upgrade_title.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 700;")
        upgrade_text.addWidget(upgrade_title)
        
        upgrade_desc = QLabel("Unbegrenzte Kampagnen • Unbegrenzte E-Mails • 1 Jahr gültig")
        upgrade_desc.setStyleSheet("color: #a5b4fc; font-size: 13px;")
        upgrade_text.addWidget(upgrade_desc)
        
        upgrade_header.addLayout(upgrade_text)
        upgrade_header.addStretch()
        
        # Price
        price_layout = QVBoxLayout()
        price_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        price_label = QLabel("129 €")
        price_label.setStyleSheet("color: #ffffff; font-size: 28px; font-weight: 700;")
        price_layout.addWidget(price_label)
        
        price_period = QLabel("/Jahr")
        price_period.setStyleSheet("color: #a5b4fc; font-size: 12px;")
        price_period.setAlignment(Qt.AlignmentFlag.AlignRight)
        price_layout.addWidget(price_period)
        
        upgrade_header.addLayout(price_layout)
        
        upgrade_layout.addLayout(upgrade_header)
        
        # Buttons row
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)
        
        self.buy_btn = QPushButton("Jetzt kaufen")
        self.buy_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:pressed {
                background-color: #4338ca;
            }
        """)
        self.buy_btn.clicked.connect(self._on_buy_clicked)
        buttons_row.addWidget(self.buy_btn)
        
        self.activate_btn = QPushButton("Lizenzschlüssel eingeben")
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a5b4fc;
                border: 1px solid #4338ca;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(99, 102, 241, 0.1);
                color: #ffffff;
            }
        """)
        self.activate_btn.clicked.connect(self._on_activate_clicked)
        buttons_row.addWidget(self.activate_btn)
        
        buttons_row.addStretch()
        upgrade_layout.addLayout(buttons_row)
        
        layout.addWidget(upgrade_frame)
        
        layout.addStretch()
    
    def _load_license_info(self) -> None:
        """Load and display current license information."""
        license_service = get_license_service()
        info = license_service.get_status_info()
        
        # Update status
        if info["is_pro"]:
            self.status_label.setText("Pro-Lizenz")
            self.status_label.setStyleSheet("color: #6366f1; font-size: 24px; font-weight: 700;")
            self.status_badge.setText("PRO")
            self.status_badge.setStyleSheet("""
                background-color: #6366f1;
                color: #ffffff;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 12px;
                border-radius: 10px;
            """)
            self.trial_progress_container.hide()
            
            # Update cards for pro
            self.campaigns_card.update_value("Unbegrenzt")
            self.emails_card.update_value("Unbegrenzt")
            
        else:
            # Trial version
            days_remaining = info.get("trial_days_remaining", 0)
            
            if days_remaining > 0:
                self.status_label.setText("Trial-Version")
                self.status_label.setStyleSheet("color: #fbbf24; font-size: 24px; font-weight: 700;")
                self.status_badge.setText("AKTIV")
                self.status_badge.setStyleSheet("""
                    background-color: #22c55e;
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 4px 12px;
                    border-radius: 10px;
                """)
            else:
                self.status_label.setText("Trial abgelaufen")
                self.status_label.setStyleSheet("color: #ef4444; font-size: 24px; font-weight: 700;")
                self.status_badge.setText("ABGELAUFEN")
                self.status_badge.setStyleSheet("""
                    background-color: #ef4444;
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 4px 12px;
                    border-radius: 10px;
                """)
            
            # Update progress
            self.trial_days_label.setText(f"{max(0, days_remaining)} Tage verbleibend")
            self.trial_progress.setValue(max(0, days_remaining))
            self.trial_progress_container.show()
            
            # Update cards  
            campaign_count = info.get("campaigns_used", 0)
            emails_today = info.get("emails_sent_today", 0)
            
            self.campaigns_card.update_value(f"{campaign_count} / {info['max_campaigns']}")
            self.emails_card.update_value(f"{emails_today} / {info['max_emails_per_day']}")
        
        # Valid until
        if info.get("license_valid_until"):
            self.valid_until_card.update_value(
                info["license_valid_until"].strftime("%d.%m.%Y")
            )
        else:
            self.valid_until_card.update_value("—")
    
    def _on_buy_clicked(self) -> None:
        """Handle buy button click."""
        stripe_service = get_stripe_service()
        
        if not stripe_service.is_configured:
            QMessageBox.warning(
                self,
                "Stripe nicht konfiguriert",
                "Die Zahlungsabwicklung ist noch nicht eingerichtet.\n\n"
                "Bitte kontaktieren Sie den Support oder geben Sie Ihren "
                "Lizenzschlüssel manuell ein."
            )
            return
        
        success, message = stripe_service.open_checkout()
        
        if success:
            QMessageBox.information(
                self,
                "Zahlungsseite geöffnet",
                message + "\n\nNach erfolgreicher Zahlung erhalten Sie Ihren Lizenzschlüssel."
            )
        else:
            QMessageBox.critical(self, "Fehler", message)
    
    def _on_activate_clicked(self) -> None:
        """Handle activate license button click."""
        dialog = ActivateLicenseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_license_info()
    
    def refresh(self) -> None:
        """Refresh license information."""
        self._load_license_info()


class ActivateLicenseDialog(QDialog):
    """Dialog for entering a license key."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Lizenz aktivieren")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background-color: #09090b;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("Lizenzschlüssel eingeben")
        header.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "Geben Sie Ihren Lizenzschlüssel ein, den Sie nach dem Kauf "
            "erhalten haben."
        )
        desc.setStyleSheet("color: #71717a; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Input
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.key_input.setStyleSheet("""
            QLineEdit {
                background-color: #18181b;
                color: #ffffff;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 16px;
                font-family: monospace;
                letter-spacing: 2px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)
        self.key_input.textChanged.connect(self._format_key)
        layout.addWidget(self.key_input)
        
        # Buttons
        buttons = QDialogButtonBox()
        
        self.activate_btn = QPushButton("Aktivieren")
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        self.activate_btn.clicked.connect(self._activate)
        buttons.addButton(self.activate_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #27272a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3f3f46;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(buttons)
    
    def _format_key(self, text: str) -> None:
        """Auto-format the license key with dashes."""
        # Remove existing dashes and spaces
        clean = text.replace("-", "").replace(" ", "").upper()
        
        # Limit to 16 characters
        clean = clean[:16]
        
        # Add dashes every 4 characters
        formatted = "-".join([clean[i:i+4] for i in range(0, len(clean), 4)])
        
        # Update if changed (avoid recursion)
        if formatted != text:
            self.key_input.blockSignals(True)
            self.key_input.setText(formatted)
            self.key_input.setCursorPosition(len(formatted))
            self.key_input.blockSignals(False)
    
    def _activate(self) -> None:
        """Activate the license."""
        key = self.key_input.text().strip()
        
        if not key:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Lizenzschlüssel ein.")
            return
        
        stripe_service = get_stripe_service()
        success, message = stripe_service.activate_with_key(key)
        
        if success:
            QMessageBox.information(
                self,
                "Lizenz aktiviert",
                "Ihre Pro-Lizenz wurde erfolgreich aktiviert!\n\n"
                "Sie haben jetzt Zugriff auf alle Funktionen."
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Aktivierung fehlgeschlagen", message)
