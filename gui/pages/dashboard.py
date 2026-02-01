"""
Obscuras Campaign Manager - Dashboard Page
Main dashboard with campaign statistics and overview.
"""

from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QScrollArea, QPushButton,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer

from utils.logging_config import get_logger

logger = get_logger("gui.pages.dashboard")


class StatCard(QFrame):
    """Statistics card widget."""
    
    def __init__(self, title: str, value: str, subtitle: str = "", 
                 color: str = "#6366f1", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #71717a; font-size: 12px; font-weight: 500;")
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            color: {color}; 
            font-size: 32px; 
            font-weight: 700;
        """)
        layout.addWidget(self.value_label)
        
        # Subtitle
        self.sub_label = QLabel(subtitle)
        self.sub_label.setStyleSheet("color: #52525b; font-size: 11px;")
        if subtitle:
            layout.addWidget(self.sub_label)
        else:
            self.sub_label.hide()
        
        layout.addStretch()
    
    def update_value(self, value: str, subtitle: str = ""):
        """Update the card value and subtitle."""
        self.value_label.setText(value)
        if subtitle:
            self.sub_label.setText(subtitle)
            self.sub_label.show()
        elif not self.sub_label.isHidden():
            pass  # Behalte existierenden Subtitle


class CampaignRow(QFrame):
    """Campaign row widget for recent campaigns list."""
    
    def __init__(self, name: str, status: str, progress: int, 
                 sent: int, total: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self.setStyleSheet("""
            QFrame {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #3f3f46;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Campaign name
        name_label = QLabel(name)
        name_label.setStyleSheet("color: #fafafa; font-weight: 500;")
        layout.addWidget(name_label, stretch=2)
        
        # Status badge
        status_colors = {
            "draft": ("#71717a", "Entwurf"),
            "running": ("#22c55e", "Aktiv"),
            "paused": ("#f59e0b", "Pausiert"),
            "completed": ("#6366f1", "Abgeschlossen"),
        }
        color, label = status_colors.get(status, ("#71717a", status))
        
        status_label = QLabel(f"● {label}")
        status_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        status_label.setFixedWidth(100)
        layout.addWidget(status_label)
        
        # Progress
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(progress)
        progress_bar.setFixedWidth(120)
        progress_bar.setFixedHeight(8)
        progress_bar.setTextVisible(False)
        layout.addWidget(progress_bar)
        
        # Count
        count_label = QLabel(f"{sent} / {total}")
        count_label.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        count_label.setFixedWidth(80)
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(count_label)


class DashboardPage(QWidget):
    """Dashboard page with overview statistics."""
    
    # Signal für Navigation zu anderen Seiten
    navigate_to = None  # Wird vom MainWindow gesetzt
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        
        # Statistik-Cards speichern für Updates
        self.stat_cards: dict[str, StatCard] = {}
        
        # Auto-Refresh Timer (alle 30 Sekunden)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)
        
        # Initial Daten laden
        QTimer.singleShot(100, self.refresh_data)
    
    def _setup_ui(self):
        """Setup the dashboard UI."""
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
        
        title = QLabel("Dashboard")
        title.setStyleSheet("color: #fafafa; font-size: 28px; font-weight: 700;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Übersicht Ihrer E-Mail-Kampagnen")
        subtitle.setStyleSheet("color: #71717a; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        # Quick action button
        self.new_btn = QPushButton("+ Neue Kampagne")
        self.new_btn.setObjectName("primaryButton")
        self.new_btn.setFixedHeight(40)
        self.new_btn.clicked.connect(self._on_new_campaign)
        header_layout.addWidget(self.new_btn)
        
        layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════
        # STATISTICS CARDS
        # ═══════════════════════════════════════════════════════════
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        cards = [
            ("Aktive Kampagnen", "3", "2 laufen gerade", "#6366f1"),
            ("Heute versendet", "47", "von 200 möglich", "#22c55e"),
            ("Gesamt versendet", "1.234", "diesen Monat", "#8b5cf6"),
            ("Bounce-Rate", "2.3%", "sehr gut", "#22c55e"),
        ]
        
        for i, (title, value, sub, color) in enumerate(cards):
            card = StatCard(title, value, sub, color)
            card.setMinimumHeight(140)
            stats_grid.addWidget(card, 0, i)
        
        layout.addLayout(stats_grid)
        
        # ═══════════════════════════════════════════════════════════
        # RECENT CAMPAIGNS
        # ═══════════════════════════════════════════════════════════
        campaigns_header = QWidget()
        campaigns_header_layout = QHBoxLayout(campaigns_header)
        campaigns_header_layout.setContentsMargins(0, 0, 0, 0)
        
        campaigns_title = QLabel("Aktuelle Kampagnen")
        campaigns_title.setStyleSheet("color: #fafafa; font-size: 18px; font-weight: 600;")
        campaigns_header_layout.addWidget(campaigns_title)
        campaigns_header_layout.addStretch()
        
        view_all = QPushButton("Alle anzeigen →")
        view_all.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #6366f1;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #818cf8;
            }
        """)
        view_all.clicked.connect(self._on_view_all_campaigns)
        campaigns_header_layout.addWidget(view_all)
        
        layout.addWidget(campaigns_header)
        
        # Campaign list
        campaigns_container = QWidget()
        campaigns_layout = QVBoxLayout(campaigns_container)
        campaigns_layout.setContentsMargins(0, 0, 0, 0)
        campaigns_layout.setSpacing(8)
        
        # Sample campaigns (will be loaded from DB)
        sample_campaigns = [
            ("Arztpraxen – Website-Modernisierung", "running", 45, 23, 50),
            ("Kanzleien – Mobile Optimierung", "paused", 78, 78, 100),
            ("Immobilien – Hausverwaltung", "draft", 0, 0, 150),
        ]
        
        for name, status, progress, sent, total in sample_campaigns:
            row = CampaignRow(name, status, progress, sent, total)
            campaigns_layout.addWidget(row)
        
        layout.addWidget(campaigns_container)
        
        # ═══════════════════════════════════════════════════════════
        # RECENT ACTIVITY
        # ═══════════════════════════════════════════════════════════
        activity_title = QLabel("Letzte Aktivitäten")
        activity_title.setStyleSheet("color: #fafafa; font-size: 18px; font-weight: 600;")
        layout.addWidget(activity_title)
        
        activity_frame = QFrame()
        activity_frame.setStyleSheet("""
            QFrame {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 12px;
            }
        """)
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        activity_layout.setSpacing(12)
        
        # Sample activities
        activities = [
            ("✓", "E-Mail erfolgreich gesendet an praxis@hausarzt-mueller.de", "vor 2 Min", "#22c55e"),
            ("✓", "E-Mail erfolgreich gesendet an info@zahnaerzte-park.de", "vor 4 Min", "#22c55e"),
            ("⚠", "Bounce: mailbox@ungueltig.de - Mailbox not found", "vor 10 Min", "#f59e0b"),
            ("ℹ", "Kampagne 'Arztpraxen' pausiert (Zeitfenster)", "vor 1 Std", "#6366f1"),
        ]
        
        for icon, text, time, color in activities:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"color: {color}; font-size: 14px;")
            icon_label.setFixedWidth(24)
            row_layout.addWidget(icon_label)
            
            text_label = QLabel(text)
            text_label.setStyleSheet("color: #a1a1aa; font-size: 13px;")
            row_layout.addWidget(text_label, stretch=1)
            
            time_label = QLabel(time)
            time_label.setStyleSheet("color: #52525b; font-size: 12px;")
            row_layout.addWidget(time_label)
            
            activity_layout.addWidget(row)
        
        layout.addWidget(activity_frame)
        
        # Bottom spacer
        layout.addStretch()
    
    def refresh_data(self):
        """Refresh dashboard data from database."""
        logger.debug("Dashboard-Daten werden aktualisiert...")
        try:
            stats = self._load_stats_from_db()
            
            # Update stat cards
            if hasattr(self, 'stat_cards') and self.stat_cards:
                for key, card in self.stat_cards.items():
                    if key in stats:
                        card.update_value(stats[key]['value'], stats[key].get('subtitle', ''))
            
            # Update campaign list
            self._refresh_campaigns()
            
            # Update activity log
            self._refresh_activities()
            
            logger.debug("Dashboard aktualisiert")
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Dashboards: {e}")
    
    def _load_stats_from_db(self) -> dict[str, dict[str, str]]:
        """Load statistics from database."""
        from models.database import get_session_simple
        from models.campaign import Campaign, CampaignStatus
        from models.send_log import SendLog, SendResult
        from sqlalchemy import func
        
        session = get_session_simple()
        stats: dict[str, dict[str, str]] = {}
        
        try:
            today = datetime.now(timezone.utc).date()
            month_start = today.replace(day=1)
            
            # Aktive Kampagnen
            active_count = session.query(func.count(Campaign.id)).filter(
                Campaign.status.in_([CampaignStatus.RUNNING, CampaignStatus.SCHEDULED])
            ).scalar() or 0
            
            running_count = session.query(func.count(Campaign.id)).filter(
                Campaign.status == CampaignStatus.RUNNING
            ).scalar() or 0
            
            stats['active_campaigns'] = {
                'value': str(active_count),
                'subtitle': f'{running_count} laufen gerade'
            }
            
            # Heute versendet
            sent_today = session.query(func.count(SendLog.id)).filter(
                func.date(SendLog.sent_at) == today,
                SendLog.result == SendResult.SUCCESS
            ).scalar() or 0
            
            stats['sent_today'] = {
                'value': str(sent_today),
                'subtitle': 'von 200 möglich'
            }
            
            # Gesamt diesen Monat
            sent_month = session.query(func.count(SendLog.id)).filter(
                func.date(SendLog.sent_at) >= month_start,
                SendLog.result == SendResult.SUCCESS
            ).scalar() or 0
            
            stats['sent_month'] = {
                'value': f'{sent_month:,}'.replace(',', '.'),
                'subtitle': 'diesen Monat'
            }
            
            # Bounce-Rate
            total_sent = session.query(func.count(SendLog.id)).filter(
                func.date(SendLog.sent_at) >= month_start
            ).scalar() or 0
            
            bounces = session.query(func.count(SendLog.id)).filter(
                func.date(SendLog.sent_at) >= month_start,
                SendLog.result == SendResult.BOUNCE
            ).scalar() or 0
            
            bounce_rate = (bounces / total_sent * 100) if total_sent > 0 else 0.0
            quality = "sehr gut" if bounce_rate < 3 else "gut" if bounce_rate < 5 else "kritisch"
            
            stats['bounce_rate'] = {
                'value': f'{bounce_rate:.1f}%',
                'subtitle': quality
            }
            
        finally:
            session.close()
        
        return stats
    
    def _refresh_campaigns(self):
        """Refresh campaign list."""
        # Wird in zukünftiger Version implementiert
        pass
    
    def _refresh_activities(self):
        """Refresh activity log."""
        # Wird in zukünftiger Version implementiert
        pass
    
    def _on_new_campaign(self) -> None:
        """Handle new campaign button click."""
        if callable(self.navigate_to):
            self.navigate_to("campaigns")
            # Signal an MainWindow um Dialog zu öffnen
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, '_on_new_campaign'):
                    parent._on_new_campaign()  # type: ignore[attr-defined]
                    return
                parent = parent.parent()
    
    def _on_view_all_campaigns(self) -> None:
        """Handle view all campaigns button click."""
        if callable(self.navigate_to):
            self.navigate_to("campaigns")
