"""
Obscuras Campaign Manager - Contacts Page
Contact management and import functionality.
"""

import csv
from pathlib import Path
from typing import Sequence
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QFileDialog,
    QDialogButtonBox, QMessageBox,
    QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt

from models.contact import Contact, ContactStatus
from models.campaign import Campaign
from models.database import get_session_simple
from utils.logging_config import get_logger, log_user_action

logger = get_logger("gui.pages.contacts")


class ImportWizardDialog(QDialog):
    """Dialog for importing contacts from CSV/Excel."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kontakte importieren")
        self.setMinimumSize(600, 500)
        self.file_path: str | None = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # ═══════════════════════════════════════════════════════════
        # FILE SELECTION
        # ═══════════════════════════════════════════════════════════
        file_group = QGroupBox("1. Datei auswählen")
        file_layout = QHBoxLayout(file_group)
        
        self.file_label = QLabel("Keine Datei ausgewählt")
        self.file_label.setStyleSheet("color: #71717a;")
        file_layout.addWidget(self.file_label, stretch=1)
        
        browse_btn = QPushButton("Durchsuchen...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addWidget(file_group)
        
        # ═══════════════════════════════════════════════════════════
        # CAMPAIGN SELECTION
        # ═══════════════════════════════════════════════════════════
        campaign_group = QGroupBox("2. Kampagne zuordnen")
        campaign_layout = QFormLayout(campaign_group)
        
        self.campaign_combo = QComboBox()
        self._load_campaigns()
        self.campaign_combo.addItem("+ Neue Kampagne erstellen...")
        campaign_layout.addRow("Kampagne:", self.campaign_combo)
        
        layout.addWidget(campaign_group)
        
        # ═══════════════════════════════════════════════════════════
        # FIELD MAPPING
        # ═══════════════════════════════════════════════════════════
        mapping_group = QGroupBox("3. Felder zuordnen")
        mapping_layout = QFormLayout(mapping_group)
        
        self.email_combo = QComboBox()
        self.email_combo.addItems(["EMAIL", "E-Mail", "email", "Mail"])
        mapping_layout.addRow("E-Mail-Feld:", self.email_combo)
        
        self.company_combo = QComboBox()
        self.company_combo.addItems(["PRAXISNAME", "FIRMA", "Company", "Unternehmen"])
        mapping_layout.addRow("Firmenname:", self.company_combo)
        
        self.domain_combo = QComboBox()
        self.domain_combo.addItems(["DOMAIN", "Website", "URL"])
        mapping_layout.addRow("Domain:", self.domain_combo)
        
        layout.addWidget(mapping_group)
        
        # ═══════════════════════════════════════════════════════════
        # OPTIONS
        # ═══════════════════════════════════════════════════════════
        options_group = QGroupBox("4. Optionen")
        options_layout = QVBoxLayout(options_group)
        
        self.skip_duplicates = QCheckBox("Duplikate überspringen")
        self.skip_duplicates.setChecked(True)
        options_layout.addWidget(self.skip_duplicates)
        
        self.validate_emails = QCheckBox("E-Mail-Adressen validieren")
        self.validate_emails.setChecked(True)
        options_layout.addWidget(self.validate_emails)
        
        self.check_mx = QCheckBox("MX-Records prüfen (langsamer)")
        options_layout.addWidget(self.check_mx)
        
        layout.addWidget(options_group)
        
        # ═══════════════════════════════════════════════════════════
        # PREVIEW
        # ═══════════════════════════════════════════════════════════
        preview_label = QLabel("Vorschau (erste 5 Zeilen):")
        preview_label.setStyleSheet("color: #a1a1aa; font-weight: 500;")
        layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(150)
        layout.addWidget(self.preview_table)
        
        # ═══════════════════════════════════════════════════════════
        # BUTTONS
        # ═══════════════════════════════════════════════════════════
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setText("Importieren")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def _browse_file(self):
        """Open file browser."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Kontaktdatei auswählen",
            str(Path.home()),
            "CSV-Dateien (*.csv);;Excel-Dateien (*.xlsx *.xls);;Alle Dateien (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_label.setText(Path(file_path).name)
            self.file_label.setStyleSheet("color: #22c55e;")
            self._load_preview()
    
    def _load_preview(self):
        """Load file preview."""
        if not self.file_path:
            return
        
        try:
            import csv
            with open(self.file_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                rows = [next(reader) for _ in range(min(5, 100))]
            
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)
            self.preview_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                for j, cell in enumerate(row):
                    self.preview_table.setItem(i, j, QTableWidgetItem(cell))
            
            # Update field mapping dropdowns
            self.email_combo.clear()
            self.email_combo.addItems(headers)
            self.company_combo.clear()
            self.company_combo.addItems(headers)
            self.domain_combo.clear()
            self.domain_combo.addItems(headers)
            
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Datei konnte nicht gelesen werden: {e}")
    
    def _load_campaigns(self):
        """Load campaigns into dropdown."""
        session = get_session_simple()
        try:
            campaigns = session.query(Campaign).order_by(Campaign.name).all()
            for campaign in campaigns:
                self.campaign_combo.addItem(campaign.name)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Kampagnen: {e}")
        finally:
            session.close()


class ContactsPage(QWidget):
    """Contacts management page."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_contacts()
    
    def _setup_ui(self):
        """Setup the contacts page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # ═══════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Kontakte")
        title.setStyleSheet("color: #fafafa; font-size: 28px; font-weight: 700;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Filter by campaign
        filter_label = QLabel("Kampagne:")
        filter_label.setStyleSheet("color: #a1a1aa;")
        header_layout.addWidget(filter_label)
        
        self.campaign_filter = QComboBox()
        self.campaign_filter.addItem("Alle Kampagnen", None)
        self._load_campaign_filter()
        self.campaign_filter.setFixedWidth(250)
        self.campaign_filter.currentIndexChanged.connect(self._load_contacts)
        header_layout.addWidget(self.campaign_filter)
        
        self.import_btn = QPushButton("📥 Importieren")
        self.import_btn.clicked.connect(self.import_contacts)
        header_layout.addWidget(self.import_btn)
        
        self.add_btn = QPushButton("+ Hinzufügen")
        self.add_btn.setObjectName("primaryButton")
        header_layout.addWidget(self.add_btn)
        
        layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════
        # STATS BAR
        # ═══════════════════════════════════════════════════════════
        stats = QWidget()
        stats_layout = QHBoxLayout(stats)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(24)
        
        for label, value, color in [
            ("Gesamt", "302", "#fafafa"),
            ("Ausstehend", "156", "#a1a1aa"),
            ("Gesendet", "138", "#22c55e"),
            ("Bounced", "5", "#ef4444"),
            ("Ungültig", "3", "#f59e0b"),
        ]:
            stat_item = QLabel(f"{label}: <span style='color:{color};font-weight:600;'>{value}</span>")
            stats_layout.addWidget(stat_item)
        
        stats_layout.addStretch()
        layout.addWidget(stats)
        
        # ═══════════════════════════════════════════════════════════
        # SEARCH BAR
        # ═══════════════════════════════════════════════════════════
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suchen nach E-Mail, Firma, Domain...")
        self.search_input.setFixedHeight(40)
        search_layout.addWidget(self.search_input)
        
        status_filter = QComboBox()
        status_filter.addItems(["Alle Status", "Ausstehend", "Gesendet", "Bounced", "Ungültig"])
        status_filter.setFixedWidth(150)
        search_layout.addWidget(status_filter)
        
        layout.addLayout(search_layout)
        
        # ═══════════════════════════════════════════════════════════
        # CONTACTS TABLE
        # ═══════════════════════════════════════════════════════════
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "E-Mail", "Firma", "Domain", "Status", "Kampagne", "Gesendet", "Aktionen"
        ])
        
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(5, 150)
        self.table.setColumnWidth(6, 120)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        
        layout.addWidget(self.table)
    
    def _load_campaign_filter(self):
        """Load campaigns into filter dropdown."""
        session = get_session_simple()
        try:
            campaigns = session.query(Campaign).order_by(Campaign.name).all()
            for campaign in campaigns:
                self.campaign_filter.addItem(campaign.name, campaign.id)
        finally:
            session.close()
    
    def _load_contacts(self):
        """Load contacts from database."""
        logger.debug("Lade Kontakte aus Datenbank...")
        
        session = get_session_simple()
        try:
            # Filter nach Kampagne
            campaign_id = self.campaign_filter.currentData()
            
            query = session.query(Contact).join(Campaign)
            if campaign_id:
                query = query.filter(Contact.campaign_id == campaign_id)
            
            contacts = query.order_by(Contact.created_at.desc()).limit(500).all()
            
            self.table.setRowCount(len(contacts))
            
            for row, contact in enumerate(contacts):
                # E-Mail
                email_item = QTableWidgetItem(contact.email or "")
                email_item.setData(Qt.ItemDataRole.UserRole, contact.id)
                self.table.setItem(row, 0, email_item)
                
                # Firma
                self.table.setItem(row, 1, QTableWidgetItem(contact.company_name or ""))
                
                # Domain
                self.table.setItem(row, 2, QTableWidgetItem(contact.domain or ""))
                
                # Status
                status_labels = {
                    ContactStatus.PENDING: "Ausstehend",
                    ContactStatus.SENT: "Gesendet",
                    ContactStatus.BOUNCED: "Bounced",
                    ContactStatus.ERROR: "Fehler",
                    ContactStatus.BLACKLISTED: "Blacklisted",
                    ContactStatus.UNSUBSCRIBED: "Abgemeldet",
                }
                status_text = status_labels.get(contact.status, "Unbekannt")
                status_item = QTableWidgetItem(status_text)
                self.table.setItem(row, 3, status_item)
                
                # Kampagne
                campaign_name = contact.campaign.name if contact.campaign else ""
                self.table.setItem(row, 4, QTableWidgetItem(campaign_name))
                
                # Gesendet am
                sent_at = contact.sent_at.strftime("%d.%m.%Y %H:%M") if contact.sent_at else "-"
                self.table.setItem(row, 5, QTableWidgetItem(sent_at))
                
                # Aktionen
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(4)
                
                edit_btn = QPushButton("✎")
                edit_btn.setObjectName("iconButton")
                edit_btn.setFixedSize(28, 28)
                edit_btn.setToolTip("Kontakt bearbeiten")
                edit_btn.setStyleSheet("font-size: 14px;")
                edit_btn.clicked.connect(lambda _, cid=contact.id: self._edit_contact(cid))  # type: ignore[arg-type]
                actions_layout.addWidget(edit_btn)
                
                blacklist_btn = QPushButton("⊘")
                blacklist_btn.setObjectName("iconButton")
                blacklist_btn.setFixedSize(28, 28)
                blacklist_btn.setToolTip("Zur Blacklist hinzufügen")
                blacklist_btn.setStyleSheet("font-size: 14px;")
                blacklist_btn.clicked.connect(lambda _, cid=contact.id: self._blacklist_contact(cid))  # type: ignore[arg-type]
                actions_layout.addWidget(blacklist_btn)
                
                delete_btn = QPushButton("✖")
                delete_btn.setObjectName("iconButton")
                delete_btn.setFixedSize(28, 28)
                delete_btn.setToolTip("Kontakt löschen")
                delete_btn.setStyleSheet("font-size: 14px; color: #ef4444;")
                delete_btn.clicked.connect(lambda _, cid=contact.id: self._delete_contact(cid))  # type: ignore[arg-type]
                actions_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, 6, actions_widget)
                self.table.setRowHeight(row, 44)
            
            # Stats aktualisieren
            self._update_stats(contacts)
            
            logger.info(f"{len(contacts)} Kontakte geladen")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Kontakte: {e}")
        finally:
            session.close()
    
    def _update_stats(self, contacts: Sequence[Contact]) -> None:
        """Update statistics bar."""
        # Stats werden in einer zukünftigen Version aktualisiert
        pass
    
    def import_contacts(self):
        """Open import dialog."""
        dialog = ImportWizardDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._do_import(dialog)
    
    def _do_import(self, dialog: ImportWizardDialog):
        """Actually perform the contact import."""
        if not dialog.file_path:
            QMessageBox.warning(self, "Fehler", "Keine Datei ausgewählt!")
            return
        
        # Kampagne ermitteln
        campaign_idx = dialog.campaign_combo.currentIndex()
        if campaign_idx == dialog.campaign_combo.count() - 1:
            # "Neue Kampagne erstellen" ausgewählt
            QMessageBox.information(self, "Info", "Bitte zuerst eine Kampagne erstellen.")
            return
        
        campaign_name = dialog.campaign_combo.currentText()
        
        session = get_session_simple()
        try:
            # Kampagne finden
            campaign = session.query(Campaign).filter(Campaign.name == campaign_name).first()
            if not campaign:
                QMessageBox.warning(self, "Fehler", f"Kampagne '{campaign_name}' nicht gefunden!")
                return
            
            # Feld-Mapping
            email_field = dialog.email_combo.currentText()
            company_field = dialog.company_combo.currentText()
            domain_field = dialog.domain_combo.currentText()
            
            imported = 0
            skipped = 0
            
            with open(dialog.file_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    email = row.get(email_field, "").strip().lower()
                    if not email:
                        continue
                    
                    # Duplikat prüfen
                    if dialog.skip_duplicates.isChecked():
                        exists = session.query(Contact).filter(
                            Contact.email == email,
                            Contact.campaign_id == campaign.id
                        ).first()
                        if exists:
                            skipped += 1
                            continue
                    
                    # E-Mail validieren
                    if dialog.validate_emails.isChecked():
                        from utils.email_validator import validate_email
                        is_valid, _ = validate_email(email)
                        if not is_valid:
                            skipped += 1
                            continue
                    
                    # Kontakt erstellen
                    contact = Contact(
                        email=email,
                        company_name=row.get(company_field, ""),
                        domain=row.get(domain_field, ""),
                        campaign_id=campaign.id,
                        status=ContactStatus.PENDING,
                    )
                    session.add(contact)
                    imported += 1
            
            # Kampagnen-Counter aktualisieren
            campaign.total_contacts = (campaign.total_contacts or 0) + imported
            session.commit()
            
            log_user_action("Kontakte importiert", f"{imported} Kontakte in '{campaign_name}'")
            logger.info(f"Import: {imported} importiert, {skipped} übersprungen")
            
            QMessageBox.information(
                self,
                "Import erfolgreich",
                f"{imported} Kontakte importiert.\n{skipped} übersprungen."
            )
            
            self._load_contacts()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Import-Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Import fehlgeschlagen:\n{e}")
        finally:
            session.close()
    
    def _edit_contact(self, contact_id: int) -> None:
        """Edit a contact."""
        session = get_session_simple()
        try:
            contact = session.query(Contact).filter(Contact.id == contact_id).first()
            if contact:
                from PyQt6.QtWidgets import QInputDialog
                new_email, ok = QInputDialog.getText(
                    self, 
                    "Kontakt bearbeiten",
                    "E-Mail-Adresse:",
                    text=contact.email or ""
                )
                if ok and new_email:
                    contact.email = new_email.strip().lower()
                    session.commit()
                    log_user_action("Kontakt bearbeitet", new_email)
                    self._load_contacts()
        finally:
            session.close()
    
    def _blacklist_contact(self, contact_id: int) -> None:
        """Add contact to blacklist."""
        session = get_session_simple()
        try:
            contact = session.query(Contact).filter(Contact.id == contact_id).first()
            if contact:
                reply = QMessageBox.question(
                    self,
                    "Zur Blacklist hinzufügen",
                    f"'{contact.email}' zur Blacklist hinzufügen?\nDer Kontakt wird nicht mehr kontaktiert.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    contact.status = ContactStatus.BLACKLISTED
                    
                    # Auch zur globalen Blacklist hinzufügen
                    from models.blacklist import BlacklistEntry, BlacklistReason, BlacklistType
                    existing = session.query(BlacklistEntry).filter(BlacklistEntry.value == contact.email).first()
                    if not existing:
                        blacklist_entry = BlacklistEntry(
                            value=contact.email,
                            entry_type=BlacklistType.EMAIL,
                            reason=BlacklistReason.MANUAL,
                        )
                        session.add(blacklist_entry)
                    
                    session.commit()
                    log_user_action("Kontakt blacklisted", contact.email)
                    self._load_contacts()
        finally:
            session.close()
    
    def _delete_contact(self, contact_id: int) -> None:
        """Delete a contact."""
        reply = QMessageBox.question(
            self,
            "Kontakt löschen",
            "Möchten Sie diesen Kontakt wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            session = get_session_simple()
            try:
                contact = session.query(Contact).filter(Contact.id == contact_id).first()
                if contact:
                    email = contact.email
                    session.delete(contact)
                    session.commit()
                    log_user_action("Kontakt gelöscht", email)
                    self._load_contacts()
            finally:
                session.close()
    
    def refresh(self):
        """Refresh the contacts list."""
        self._load_contacts()
