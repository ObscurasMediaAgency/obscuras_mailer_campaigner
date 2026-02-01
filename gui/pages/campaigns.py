"""
Obscuras Campaign Manager - Campaigns Page
Campaign management and editing interface.
"""

from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDialogButtonBox, QMessageBox,
    QTabWidget, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt

from models.campaign import Campaign, CampaignStatus
from models.database import get_session_simple
from utils.logging_config import get_logger, log_user_action

logger = get_logger("gui.pages.campaigns")


class CampaignEditorDialog(QDialog):
    """Dialog for creating/editing campaigns."""
    
    def __init__(self, campaign: Campaign | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.campaign = campaign
        self.setWindowTitle("Neue Kampagne" if not campaign else "Kampagne bearbeiten")
        self.setMinimumSize(700, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Tab widget for sections
        tabs = QTabWidget()
        
        # ═══════════════════════════════════════════════════════════
        # BASIC INFO TAB
        # ═══════════════════════════════════════════════════════════
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        basic_layout.setSpacing(12)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("z.B. Arztpraxen – Website-Modernisierung")
        basic_layout.addRow("Kampagnenname:", self.name_edit)
        
        self.slug_edit = QLineEdit()
        self.slug_edit.setPlaceholderText("z.B. aerzte_website (Ordnername)")
        basic_layout.addRow("Slug:", self.slug_edit)
        
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("Betreffzeile der E-Mail")
        basic_layout.addRow("Betreff:", self.subject_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Optionale Beschreibung...")
        self.description_edit.setMaximumHeight(100)
        basic_layout.addRow("Beschreibung:", self.description_edit)
        
        tabs.addTab(basic_tab, "📋 Grunddaten")
        
        # ═══════════════════════════════════════════════════════════
        # CONTENT TAB
        # ═══════════════════════════════════════════════════════════
        content_tab = QWidget()
        content_layout = QFormLayout(content_tab)
        content_layout.setSpacing(12)
        
        self.greeting_edit = QLineEdit()
        self.greeting_edit.setPlaceholderText("z.B. Sehr geehrte Damen und Herren der {{FIRMA}},")
        content_layout.addRow("Begrüßung:", self.greeting_edit)
        
        self.intro_edit = QTextEdit()
        self.intro_edit.setPlaceholderText("Einleitungstext...")
        self.intro_edit.setMaximumHeight(80)
        content_layout.addRow("Einleitung:", self.intro_edit)
        
        self.highlight_edit = QLineEdit()
        self.highlight_edit.setPlaceholderText("{{PROBLEM}} - Hervorgehobener Text")
        content_layout.addRow("Highlight:", self.highlight_edit)
        
        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText("Haupttext der E-Mail...")
        content_layout.addRow("Hauptinhalt:", self.body_edit)
        
        cta_group = QGroupBox("Call-to-Action")
        cta_layout = QFormLayout(cta_group)
        
        self.cta_text_edit = QLineEdit()
        self.cta_text_edit.setPlaceholderText("z.B. Kostenlose Erstberatung →")
        cta_layout.addRow("Button-Text:", self.cta_text_edit)
        
        self.cta_url_edit = QLineEdit()
        self.cta_url_edit.setPlaceholderText("https://...")
        cta_layout.addRow("URL:", self.cta_url_edit)
        
        content_layout.addRow(cta_group)
        
        tabs.addTab(content_tab, "✏️ Inhalt")
        
        # ═══════════════════════════════════════════════════════════
        # SCHEDULE TAB
        # ═══════════════════════════════════════════════════════════
        schedule_tab = QWidget()
        schedule_layout = QFormLayout(schedule_tab)
        schedule_layout.setSpacing(12)
        
        self.days_edit = QLineEdit("1-5")
        self.days_edit.setPlaceholderText("1-5 (Mo-Fr)")
        schedule_layout.addRow("Wochentage:", self.days_edit)
        
        self.hours_edit = QLineEdit("9-17")
        self.hours_edit.setPlaceholderText("9-17 Uhr")
        schedule_layout.addRow("Uhrzeiten:", self.hours_edit)
        
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(30, 300)
        self.delay_spin.setValue(80)
        self.delay_spin.setSuffix(" Sekunden")
        schedule_layout.addRow("Verzögerung:", self.delay_spin)
        
        self.max_hour_spin = QSpinBox()
        self.max_hour_spin.setRange(1, 100)
        self.max_hour_spin.setValue(50)
        self.max_hour_spin.setSuffix(" E-Mails")
        schedule_layout.addRow("Max. pro Stunde:", self.max_hour_spin)
        
        self.max_day_spin = QSpinBox()
        self.max_day_spin.setRange(1, 500)
        self.max_day_spin.setValue(200)
        self.max_day_spin.setSuffix(" E-Mails")
        schedule_layout.addRow("Max. pro Tag:", self.max_day_spin)
        
        tabs.addTab(schedule_tab, "⏰ Zeitplan")
        
        # ═══════════════════════════════════════════════════════════
        # SMTP TAB
        # ═══════════════════════════════════════════════════════════
        smtp_tab = QWidget()
        smtp_layout = QFormLayout(smtp_tab)
        smtp_layout.setSpacing(12)
        
        self.smtp_combo = QComboBox()
        self.smtp_combo.addItem("Standard-SMTP-Profil")
        # TODO: Load SMTP profiles from database
        smtp_layout.addRow("SMTP-Profil:", self.smtp_combo)
        
        tabs.addTab(smtp_tab, "📤 Versand")
        
        layout.addWidget(tabs)
        
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
        
        # Load existing data if editing
        if self.campaign:
            self._load_campaign_data()
    
    def _load_campaign_data(self) -> None:
        """Load campaign data into form."""
        if not self.campaign:
            return
        
        self.name_edit.setText(str(self.campaign.name or ""))
        self.slug_edit.setText(str(self.campaign.slug or ""))
        self.subject_edit.setText(str(self.campaign.subject or ""))
        self.description_edit.setText(str(self.campaign.description or ""))
        self.greeting_edit.setText(str(self.campaign.greeting or ""))
        self.intro_edit.setText(str(self.campaign.intro or ""))
        self.highlight_edit.setText(str(self.campaign.highlight or ""))
        self.body_edit.setText(str(self.campaign.body_content or ""))
        self.cta_text_edit.setText(str(self.campaign.cta_text or ""))
        self.cta_url_edit.setText(str(self.campaign.cta_url or ""))
        self.days_edit.setText(str(self.campaign.schedule_days or "1-5"))
        self.hours_edit.setText(str(self.campaign.schedule_hours or "9-17"))
        delay = self.campaign.delay_seconds if self.campaign else 80
        self.delay_spin.setValue(delay)
        max_hour = self.campaign.max_per_hour if self.campaign else 50
        self.max_hour_spin.setValue(max_hour)
        max_day = self.campaign.max_per_day if self.campaign else 200
        self.max_day_spin.setValue(max_day)
    
    def get_campaign_data(self) -> dict[str, Any]:
        """Get form data as dictionary."""
        return {
            "name": self.name_edit.text(),
            "slug": self.slug_edit.text(),
            "subject": self.subject_edit.text(),
            "description": self.description_edit.toPlainText(),
            "greeting": self.greeting_edit.text(),
            "intro": self.intro_edit.toPlainText(),
            "highlight": self.highlight_edit.text(),
            "body_content": self.body_edit.toPlainText(),
            "cta_text": self.cta_text_edit.text(),
            "cta_url": self.cta_url_edit.text(),
            "schedule_days": self.days_edit.text(),
            "schedule_hours": self.hours_edit.text(),
            "delay_seconds": self.delay_spin.value(),
            "max_per_hour": self.max_hour_spin.value(),
            "max_per_day": self.max_day_spin.value(),
        }


class CampaignsPage(QWidget):
    """Campaigns management page."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_campaigns()
    
    def _setup_ui(self):
        """Setup the campaigns page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # ═══════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Kampagnen")
        title.setStyleSheet("color: #fafafa; font-size: 28px; font-weight: 700;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.new_btn = QPushButton("+ Neue Kampagne")
        self.new_btn.setObjectName("primaryButton")
        self.new_btn.clicked.connect(self.create_new_campaign)
        header_layout.addWidget(self.new_btn)
        
        layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════
        # CAMPAIGNS TABLE
        # ═══════════════════════════════════════════════════════════
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Status", "Kontakte", "Gesendet", "Bounce", "Fortschritt", "Aktionen"
        ])
        
        # Table styling
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 150)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        
        layout.addWidget(self.table)
    
    def _load_campaigns(self):
        """Load campaigns from database."""
        logger.debug("Lade Kampagnen aus Datenbank...")
        
        session = get_session_simple()
        try:
            campaigns = session.query(Campaign).order_by(Campaign.created_at.desc()).all()
            
            self.table.setRowCount(len(campaigns))
            
            for row, campaign in enumerate(campaigns):
                # Name
                name_item = QTableWidgetItem(campaign.name or "")
                name_item.setData(Qt.ItemDataRole.UserRole, campaign.id)
                self.table.setItem(row, 0, name_item)
                
                # Status
                status_labels = {
                    CampaignStatus.DRAFT: "Entwurf",
                    CampaignStatus.SCHEDULED: "Geplant",
                    CampaignStatus.RUNNING: "Aktiv",
                    CampaignStatus.PAUSED: "Pausiert",
                    CampaignStatus.COMPLETED: "Abgeschlossen",
                    CampaignStatus.CANCELLED: "Abgebrochen",
                }
                status_text = status_labels.get(campaign.status, "Unbekannt")
                status_item = QTableWidgetItem(status_text)
                self.table.setItem(row, 1, status_item)
                
                # Kontakte
                self.table.setItem(row, 2, QTableWidgetItem(str(campaign.total_contacts or 0)))
                
                # Gesendet
                self.table.setItem(row, 3, QTableWidgetItem(str(campaign.sent_count or 0)))
                
                # Bounce
                self.table.setItem(row, 4, QTableWidgetItem(str(campaign.bounce_count or 0)))
                
                # Fortschritt
                total = campaign.total_contacts or 0
                sent = campaign.sent_count or 0
                progress = int((sent / total * 100) if total > 0 else 0)
                
                progress_widget = QWidget()
                progress_layout = QHBoxLayout(progress_widget)
                progress_layout.setContentsMargins(4, 4, 4, 4)
                
                progress_bar = QProgressBar()
                progress_bar.setMaximum(100)
                progress_bar.setValue(progress)
                progress_bar.setFixedHeight(16)
                progress_bar.setFormat(f"{progress}%")
                progress_layout.addWidget(progress_bar)
                
                self.table.setCellWidget(row, 5, progress_widget)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(4)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(28, 28)
                edit_btn.setToolTip("Bearbeiten")
                edit_btn.clicked.connect(lambda _, cid=campaign.id: self._edit_campaign(cid))  # type: ignore[arg-type]
                actions_layout.addWidget(edit_btn)
                
                if campaign.status in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
                    play_btn = QPushButton("▶")
                    play_btn.setToolTip("Starten")
                    play_btn.clicked.connect(lambda _, cid=campaign.id: self._start_campaign(cid))  # type: ignore[arg-type]
                else:
                    play_btn = QPushButton("⏸")
                    play_btn.setToolTip("Pausieren")
                    play_btn.clicked.connect(lambda _, cid=campaign.id: self._pause_campaign(cid))  # type: ignore[arg-type]
                
                play_btn.setFixedSize(28, 28)
                actions_layout.addWidget(play_btn)
                
                delete_btn = QPushButton("🗑")
                delete_btn.setFixedSize(28, 28)
                delete_btn.setToolTip("Löschen")
                delete_btn.clicked.connect(lambda _, cid=campaign.id: self._delete_campaign(cid))  # type: ignore[arg-type]
                actions_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, 6, actions_widget)
                self.table.setRowHeight(row, 50)
            
            logger.info(f"{len(campaigns)} Kampagnen geladen")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Kampagnen: {e}")
        finally:
            session.close()
    
    def _edit_campaign(self, campaign_id: int):
        """Edit an existing campaign."""
        session = get_session_simple()
        try:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if campaign:
                dialog = CampaignEditorDialog(campaign, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_campaign_data()
                    for key, value in data.items():
                        if hasattr(campaign, key):
                            setattr(campaign, key, value)
                    session.commit()
                    log_user_action("Kampagne bearbeitet", campaign.name)
                    self._load_campaigns()
        finally:
            session.close()
    
    def _start_campaign(self, campaign_id: int):
        """Start a campaign."""
        session = get_session_simple()
        try:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if campaign:
                campaign.status = CampaignStatus.RUNNING
                session.commit()
                log_user_action("Kampagne gestartet", campaign.name)
                self._load_campaigns()
        finally:
            session.close()
    
    def _pause_campaign(self, campaign_id: int):
        """Pause a campaign."""
        session = get_session_simple()
        try:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if campaign:
                campaign.status = CampaignStatus.PAUSED
                session.commit()
                log_user_action("Kampagne pausiert", campaign.name)
                self._load_campaigns()
        finally:
            session.close()
    
    def _delete_campaign(self, campaign_id: int):
        """Delete a campaign."""
        reply = QMessageBox.question(
            self,
            "Kampagne löschen",
            "Möchten Sie diese Kampagne wirklich löschen?\nAlle zugehörigen Kontakte werden ebenfalls gelöscht!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_session_simple()
            try:
                campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
                if campaign:
                    name = campaign.name
                    session.delete(campaign)
                    session.commit()
                    log_user_action("Kampagne gelöscht", name)
                    self._load_campaigns()
            finally:
                session.close()
    
    def create_new_campaign(self):
        """Open dialog to create new campaign."""
        dialog = CampaignEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_campaign_data()
            
            # In Datenbank speichern
            session = get_session_simple()
            try:
                campaign = Campaign(
                    name=data['name'],
                    slug=data['slug'] or data['name'].lower().replace(' ', '_').replace('–', '_'),
                    subject=data['subject'],
                    description=data.get('description'),
                    greeting=data.get('greeting'),
                    intro=data.get('intro'),
                    highlight=data.get('highlight'),
                    body_content=data.get('body_content'),
                    cta_text=data.get('cta_text'),
                    cta_url=data.get('cta_url'),
                    schedule_days=data.get('schedule_days', '1-5'),
                    schedule_hours=data.get('schedule_hours', '9-17'),
                    delay_seconds=data.get('delay_seconds', 80),
                    max_per_hour=data.get('max_per_hour', 50),
                    max_per_day=data.get('max_per_day', 200),
                    status=CampaignStatus.DRAFT,
                )
                session.add(campaign)
                session.commit()
                
                log_user_action("Neue Kampagne erstellt", data['name'])
                logger.info(f"Kampagne erstellt: {data['name']}")
                
                self._load_campaigns()
                QMessageBox.information(
                    self, 
                    "Kampagne erstellt", 
                    f"Kampagne '{data['name']}' wurde erstellt."
                )
            except Exception as e:
                session.rollback()
                logger.error(f"Fehler beim Erstellen der Kampagne: {e}")
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Kampagne konnte nicht erstellt werden:\n{e}"
                )
            finally:
                session.close()
    
    def refresh(self):
        """Refresh the campaigns list."""
        self._load_campaigns()
