"""
Obscuras Campaign Manager - Sidebar Navigation Widget
Left sidebar with navigation buttons.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from utils.logging_config import get_logger

logger = get_logger("gui.widgets.sidebar")

# Logo-Pfad
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"


class NavButton(QPushButton):
    """Custom navigation button for sidebar."""
    
    def __init__(self, icon: str, text: str, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.name = name
        self.setText(f"  {icon}  {text}")
        self.setCheckable(True)
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 16px;
                border: none;
                border-radius: 8px;
                background-color: transparent;
                color: #a1a1aa;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #27272a;
                color: #fafafa;
            }
            QPushButton:checked {
                background-color: #6366f1;
                color: #ffffff;
            }
        """)


class Sidebar(QWidget):
    """Sidebar navigation widget."""
    
    navigation_changed = pyqtSignal(str)
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self.setFixedWidth(240)
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0a0f;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)
        
        # ═══════════════════════════════════════════════════════════
        # LOGO / HEADER
        # ═══════════════════════════════════════════════════════════
        header = QWidget()
        header.setFixedHeight(220)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 10, 8, 10)
        
        # Logo aus Datei laden
        logo_label = QLabel()
        logo_label.setFixedSize(200, 200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if LOGO_PATH.exists():
            pixmap = QPixmap(str(LOGO_PATH))
            scaled_pixmap = pixmap.scaled(
                200, 200, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
            logger.debug(f"Logo geladen: {LOGO_PATH}")
        else:
            # Fallback: Text-Symbol
            logo_label.setText("◈")
            logo_label.setStyleSheet("""
                font-size: 56px;
                color: #6366f1;
            """)
            logger.warning(f"Logo nicht gefunden: {LOGO_PATH}")
        
        header_layout.addWidget(logo_label)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #27272a;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        layout.addSpacing(16)
        
        # ═══════════════════════════════════════════════════════════
        # NAVIGATION SECTION - MAIN
        # ═══════════════════════════════════════════════════════════
        section_label = QLabel("HAUPTMENÜ")
        section_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #52525b;
            padding-left: 12px;
            padding-top: 8px;
            padding-bottom: 8px;
        """)
        layout.addWidget(section_label)
        
        self.nav_buttons: dict[str, NavButton] = {}
        
        # Navigation items
        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("📧", "Kampagnen", "campaigns"),
            ("👥", "Kontakte", "contacts"),
            ("📝", "Templates", "templates"),
        ]
        
        for icon, text, name in nav_items:
            btn = NavButton(icon, text, name)
            btn.clicked.connect(lambda _checked=False, n=name: self._on_nav_clicked(n))  # type: ignore[arg-type]
            self.nav_buttons[name] = btn
            layout.addWidget(btn)
        
        layout.addSpacing(24)
        
        # ═══════════════════════════════════════════════════════════
        # NAVIGATION SECTION - SETTINGS
        # ═══════════════════════════════════════════════════════════
        settings_label = QLabel("EINSTELLUNGEN")
        settings_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #52525b;
            padding-left: 12px;
            padding-top: 8px;
            padding-bottom: 8px;
        """)
        layout.addWidget(settings_label)
        
        settings_items = [
            ("🏢", "Firma / Branding", "company"),
            ("⚙️", "SMTP-Profile", "smtp"),
            ("🚫", "Blacklist", "blacklist"),
        ]
        
        for icon, text, name in settings_items:
            btn = NavButton(icon, text, name)
            btn.clicked.connect(lambda _checked=False, n=name: self._on_nav_clicked(n))  # type: ignore[arg-type]
            self.nav_buttons[name] = btn
            layout.addWidget(btn)
        
        # Spacer
        layout.addStretch()
        
        # ═══════════════════════════════════════════════════════════
        # FOOTER - STATUS INFO
        # ═══════════════════════════════════════════════════════════
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background-color: #27272a;")
        separator2.setFixedHeight(1)
        layout.addWidget(separator2)
        layout.addSpacing(12)
        
        # Quick stats
        self.stats_widget = QWidget()
        self.stats_widget.setStyleSheet("""
            QWidget {
                background-color: #18181b;
                border-radius: 8px;
                border: 1px solid #27272a;
            }
        """)
        stats_layout = QVBoxLayout(self.stats_widget)
        stats_layout.setContentsMargins(12, 12, 12, 12)
        stats_layout.setSpacing(8)
        
        stats_title = QLabel("Heute versendet")
        stats_title.setStyleSheet("color: #71717a; font-size: 11px;")
        stats_layout.addWidget(stats_title)
        
        self.stats_value_label = QLabel("0 / 200")
        self.stats_value_label.setStyleSheet("color: #fafafa; font-size: 20px; font-weight: 700;")
        stats_layout.addWidget(self.stats_value_label)
        
        from PyQt6.QtWidgets import QProgressBar
        self.stats_progress = QProgressBar()
        self.stats_progress.setMaximum(200)
        self.stats_progress.setValue(0)
        self.stats_progress.setTextVisible(False)
        self.stats_progress.setFixedHeight(6)
        stats_layout.addWidget(self.stats_progress)
        
        layout.addWidget(self.stats_widget)
        
        # Initial stats laden
        self._update_stats()
    
    def _on_nav_clicked(self, name: str):
        """Handle navigation button click."""
        self.set_active(name)
        self.navigation_changed.emit(name)
    
    def set_active(self, name: str):
        """Set the active navigation button."""
        for btn_name, btn in self.nav_buttons.items():
            btn.setChecked(btn_name == name)
    
    def _update_stats(self):
        """Update the quick stats from database."""
        try:
            from datetime import datetime, timezone
            from models.database import get_session_simple
            from models.send_log import SendLog, SendResult
            from sqlalchemy import func
            
            session = get_session_simple()
            today = datetime.now(timezone.utc).date()
            
            # Heute versendete E-Mails zählen
            sent_today = session.query(func.count(SendLog.id)).filter(
                func.date(SendLog.sent_at) == today,
                SendLog.result == SendResult.SUCCESS
            ).scalar() or 0
            
            session.close()
            
            max_per_day = 200  # TODO: Von Einstellungen laden
            self.stats_value_label.setText(f"{sent_today} / {max_per_day}")
            self.stats_progress.setMaximum(max_per_day)
            self.stats_progress.setValue(min(sent_today, max_per_day))
            
            logger.debug(f"Stats aktualisiert: {sent_today}/{max_per_day}")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Stats: {e}")
    
    def refresh_stats(self):
        """Public method to refresh statistics."""
        self._update_stats()
