"""
Obscuras Campaign Manager - SMTP Settings Page
SMTP profile management interface.
"""

import smtplib
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QSpinBox,
    QDialogButtonBox, QMessageBox, QCheckBox, QGroupBox,
    QScrollArea
)
from PyQt6.QtCore import Qt

from models.smtp_profile import SmtpProfile
from models.database import get_session_simple
from utils.logging_config import get_logger, log_user_action

logger = get_logger("gui.pages.smtp_settings")


class SmtpProfileDialog(QDialog):
    """Dialog for creating/editing SMTP profiles."""
    
    def __init__(self, profile: SmtpProfile | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("Neues SMTP-Profil" if not profile else "SMTP-Profil bearbeiten")
        self.setMinimumSize(550, 750)
        self.resize(550, 800)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ScrollArea für den gesamten Inhalt
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        
        # Container-Widget für ScrollArea
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # ═══════════════════════════════════════════════════════════
        # PROFILE INFO
        # ═══════════════════════════════════════════════════════════
        info_group = QGroupBox("Profil-Informationen")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(16, 20, 16, 16)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("z.B. Hauptkonto, Backup...")
        self.name_edit.setMinimumHeight(36)
        info_layout.addRow("Profilname:", self.name_edit)
        
        self.default_check = QCheckBox("Als Standard-Profil verwenden")
        info_layout.addRow("", self.default_check)
        
        layout.addWidget(info_group)
        
        # ═══════════════════════════════════════════════════════════
        # SERVER SETTINGS
        # ═══════════════════════════════════════════════════════════
        server_group = QGroupBox("Server-Einstellungen")
        server_layout = QFormLayout(server_group)
        server_layout.setSpacing(12)
        server_layout.setContentsMargins(16, 20, 16, 16)
        
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("z.B. smtp.domain.de")
        self.host_edit.setMinimumHeight(36)
        server_layout.addRow("SMTP-Host:", self.host_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(465)
        self.port_spin.setMinimumHeight(36)
        server_layout.addRow("Port:", self.port_spin)
        
        security_layout = QHBoxLayout()
        self.ssl_check = QCheckBox("SSL")
        self.ssl_check.setChecked(True)
        security_layout.addWidget(self.ssl_check)
        
        self.tls_check = QCheckBox("STARTTLS")
        security_layout.addWidget(self.tls_check)
        security_layout.addStretch()
        
        server_layout.addRow("Verschlüsselung:", security_layout)
        
        layout.addWidget(server_group)
        
        # ═══════════════════════════════════════════════════════════
        # AUTHENTICATION
        # ═══════════════════════════════════════════════════════════
        auth_group = QGroupBox("Authentifizierung")
        auth_layout = QFormLayout(auth_group)
        auth_layout.setSpacing(12)
        auth_layout.setContentsMargins(16, 20, 16, 16)
        
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("SMTP-Benutzername / E-Mail")
        self.user_edit.setMinimumHeight(36)
        auth_layout.addRow("Benutzername:", self.user_edit)
        
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("SMTP-Passwort")
        self.pass_edit.setMinimumHeight(36)
        auth_layout.addRow("Passwort:", self.pass_edit)
        
        self.keyring_check = QCheckBox("Im System-Keyring speichern (empfohlen)")
        self.keyring_check.setChecked(True)
        auth_layout.addRow("", self.keyring_check)
        
        layout.addWidget(auth_group)
        
        # ═══════════════════════════════════════════════════════════
        # SENDER INFO
        # ═══════════════════════════════════════════════════════════
        sender_group = QGroupBox("Absender-Informationen")
        sender_layout = QFormLayout(sender_group)
        sender_layout.setSpacing(12)
        sender_layout.setContentsMargins(16, 20, 16, 16)
        
        self.from_name_edit = QLineEdit()
        self.from_name_edit.setPlaceholderText("z.B. Max Mustermann")
        self.from_name_edit.setMinimumHeight(36)
        sender_layout.addRow("Absender-Name:", self.from_name_edit)
        
        self.from_email_edit = QLineEdit()
        self.from_email_edit.setPlaceholderText("z.B. info@domain.de")
        self.from_email_edit.setMinimumHeight(36)
        sender_layout.addRow("Absender-E-Mail:", self.from_email_edit)
        
        self.reply_to_edit = QLineEdit()
        self.reply_to_edit.setPlaceholderText("Optional, falls anders als Absender")
        self.reply_to_edit.setMinimumHeight(36)
        sender_layout.addRow("Reply-To:", self.reply_to_edit)
        
        layout.addWidget(sender_group)
        
        # ═══════════════════════════════════════════════════════════
        # RATE LIMITS
        # ═══════════════════════════════════════════════════════════
        limits_group = QGroupBox("Rate-Limits")
        limits_layout = QFormLayout(limits_group)
        limits_layout.setSpacing(12)
        limits_layout.setContentsMargins(16, 20, 16, 16)
        
        self.max_hour_spin = QSpinBox()
        self.max_hour_spin.setRange(1, 500)
        self.max_hour_spin.setValue(50)
        self.max_hour_spin.setMinimumHeight(36)
        self.max_hour_spin.setSuffix(" E-Mails")
        limits_layout.addRow("Max. pro Stunde:", self.max_hour_spin)
        
        self.max_day_spin = QSpinBox()
        self.max_day_spin.setRange(1, 5000)
        self.max_day_spin.setValue(500)
        self.max_day_spin.setMinimumHeight(36)
        self.max_day_spin.setSuffix(" E-Mails")
        limits_layout.addRow("Max. pro Tag:", self.max_day_spin)
        
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(10, 600)
        self.delay_spin.setValue(80)
        self.delay_spin.setMinimumHeight(36)
        self.delay_spin.setSuffix(" Sekunden")
        limits_layout.addRow("Verzögerung:", self.delay_spin)
        
        layout.addWidget(limits_group)
        
        # Spacer am Ende des scrollbaren Bereichs
        layout.addStretch()
        
        # ScrollArea mit Container verbinden
        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)
        
        # ═══════════════════════════════════════════════════════════
        # TEST & BUTTONS (außerhalb der ScrollArea)
        # ═══════════════════════════════════════════════════════════
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(20, 10, 20, 20)
        button_layout.setSpacing(12)
        
        test_btn = QPushButton("🔌 Verbindung testen")
        test_btn.setMinimumHeight(40)
        test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(test_btn)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        button_layout.addWidget(button_box)
        main_layout.addWidget(button_container)
    
    def _test_connection(self):
        """Test SMTP connection."""
        host = self.host_edit.text()
        port = self.port_spin.value()
        username = self.user_edit.text()
        password = self.pass_edit.text()
        use_ssl = self.ssl_check.isChecked()
        use_tls = self.tls_check.isChecked()
        
        if not host or not username:
            QMessageBox.warning(self, "Fehler", "Bitte Host und Benutzername eingeben!")
            return
        
        try:
            logger.info(f"Teste SMTP-Verbindung zu {host}:{port}")
            
            if use_ssl:
                # Verwende SMTP_SSL ohne strikten Context (wie send_campaign.py)
                # Manche Shared-Hosting-Server haben Zertifikate für andere Hostnamen
                server = smtplib.SMTP_SSL(host, port, timeout=15)
            else:
                server = smtplib.SMTP(host, port, timeout=15)
                if use_tls:
                    server.starttls()
            
            if password:
                server.login(username, password)
            
            server.quit()
            
            logger.info("SMTP-Verbindungstest erfolgreich")
            QMessageBox.information(
                self,
                "Verbindungstest",
                f"✓ Verbindung zu SMTP-Server erfolgreich!\n\n"
                f"Host: {host}\n"
                f"Port: {port}"
            )
            
        except Exception as e:
            logger.error(f"SMTP-Verbindungstest fehlgeschlagen: {e}")
            QMessageBox.critical(
                self,
                "Verbindungsfehler",
                f"✗ Verbindung fehlgeschlagen:\n\n{e}"
            )
    
    def get_profile_data(self) -> dict[str, Any]:
        """Get form data as dictionary."""
        return {
            "name": self.name_edit.text(),
            "is_default": self.default_check.isChecked(),
            "host": self.host_edit.text(),
            "port": self.port_spin.value(),
            "use_ssl": self.ssl_check.isChecked(),
            "use_tls": self.tls_check.isChecked(),
            "username": self.user_edit.text(),
            "password": self.pass_edit.text(),
            "use_keyring": self.keyring_check.isChecked(),
            "from_name": self.from_name_edit.text(),
            "from_email": self.from_email_edit.text(),
            "reply_to": self.reply_to_edit.text(),
            "max_per_hour": self.max_hour_spin.value(),
            "max_per_day": self.max_day_spin.value(),
            "delay_seconds": self.delay_spin.value(),
        }


class SmtpSettingsPage(QWidget):
    """SMTP profiles management page."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_profiles()
    
    def _setup_ui(self):
        """Setup the SMTP settings page UI."""
        layout = QVBoxLayout(self)
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
        
        title = QLabel("SMTP-Profile")
        title.setStyleSheet("color: #fafafa; font-size: 28px; font-weight: 700;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Verwalten Sie Ihre E-Mail-Server-Konfigurationen")
        subtitle.setStyleSheet("color: #71717a; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        self.new_btn = QPushButton("+ Neues Profil")
        self.new_btn.setObjectName("primaryButton")
        self.new_btn.clicked.connect(self._create_profile)
        header_layout.addWidget(self.new_btn)
        
        layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════
        # INFO BOX
        # ═══════════════════════════════════════════════════════════
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(99, 102, 241, 0.1);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 8px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)
        
        info_icon = QLabel("ℹ️")
        info_layout.addWidget(info_icon)
        
        info_text = QLabel(
            "SMTP-Profile ermöglichen den Versand über verschiedene E-Mail-Konten. "
            "Passwörter werden sicher im System-Keyring oder verschlüsselt gespeichert."
        )
        info_text.setStyleSheet("color: #a1a1aa; font-size: 13px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text, stretch=1)
        
        layout.addWidget(info_frame)
        
        # ═══════════════════════════════════════════════════════════
        # PROFILES TABLE
        # ═══════════════════════════════════════════════════════════
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Host", "Absender", "Limit/h", "Gesendet", "Status", "Aktionen"
        ])
        
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 120)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        
        layout.addWidget(self.table)
    
    def _load_profiles(self):
        """Load SMTP profiles from database."""
        logger.debug("Lade SMTP-Profile aus Datenbank...")
        
        session = get_session_simple()
        try:
            profiles = session.query(SmtpProfile).order_by(SmtpProfile.is_default.desc(), SmtpProfile.name).all()
            
            self.table.setRowCount(len(profiles))
            
            for row, profile in enumerate(profiles):
                # Name
                name_text = f"⭐ {profile.name}" if profile.is_default else profile.name
                name_item = QTableWidgetItem(name_text)
                name_item.setData(Qt.ItemDataRole.UserRole, profile.id)
                self.table.setItem(row, 0, name_item)
                
                # Host
                self.table.setItem(row, 1, QTableWidgetItem(profile.host or ""))
                
                # Absender
                self.table.setItem(row, 2, QTableWidgetItem(profile.from_email or ""))
                
                # Limit/h
                self.table.setItem(row, 3, QTableWidgetItem(str(profile.max_per_hour or 50)))
                
                # Gesendet
                self.table.setItem(row, 4, QTableWidgetItem(str(profile.total_sent or 0)))
                
                # Status
                status_text = "● Aktiv" if profile.is_active else "○ Inaktiv"
                status_item = QTableWidgetItem(status_text)
                self.table.setItem(row, 5, status_item)
                
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
                edit_btn.clicked.connect(lambda _, pid=profile.id: self._edit_profile(pid))  # type: ignore[arg-type]
                actions_layout.addWidget(edit_btn)
                
                test_btn = QPushButton("↻")
                test_btn.setObjectName("iconButton")
                test_btn.setFixedSize(28, 28)
                test_btn.setToolTip("Testen")
                test_btn.setStyleSheet("font-size: 14px; color: #6366f1;")
                test_btn.clicked.connect(lambda _, pid=profile.id: self._test_profile(pid))  # type: ignore[arg-type]
                actions_layout.addWidget(test_btn)
                
                delete_btn = QPushButton("✖")
                delete_btn.setObjectName("iconButton")
                delete_btn.setFixedSize(28, 28)
                delete_btn.setToolTip("Löschen")
                delete_btn.setStyleSheet("font-size: 14px; color: #ef4444;")
                delete_btn.clicked.connect(lambda _, pid=profile.id: self._delete_profile(pid))  # type: ignore[arg-type]
                actions_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, 6, actions)
                self.table.setRowHeight(row, 50)
            
            logger.info(f"{len(profiles)} SMTP-Profile geladen")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der SMTP-Profile: {e}")
        finally:
            session.close()
    
    def _edit_profile(self, profile_id: int):
        """Edit an existing profile."""
        session = get_session_simple()
        try:
            profile = session.query(SmtpProfile).filter(SmtpProfile.id == profile_id).first()
            if profile:
                dialog = SmtpProfileDialog(profile, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_profile_data()
                    password = data.pop('password', '')
                    
                    for key, value in data.items():
                        if hasattr(profile, key):
                            setattr(profile, key, value)
                    
                    if password:
                        profile.set_password(password)
                    
                    session.commit()
                    log_user_action("SMTP-Profil bearbeitet", profile.name)
                    self._load_profiles()
        finally:
            session.close()
    
    def _test_profile(self, profile_id: int):
        """Test an existing profile connection."""
        session = get_session_simple()
        try:
            profile = session.query(SmtpProfile).filter(SmtpProfile.id == profile_id).first()
            if profile:
                try:
                    password = profile.get_password()
                    
                    if profile.use_ssl:
                        # Ohne strikten SSL-Context (Shared-Hosting-Kompatibilität)
                        server = smtplib.SMTP_SSL(profile.host, profile.port, timeout=15)
                    else:
                        server = smtplib.SMTP(profile.host, profile.port, timeout=15)
                        if profile.use_tls:
                            server.starttls()
                    
                    if password:
                        server.login(profile.username, password)
                    
                    server.quit()
                    
                    QMessageBox.information(self, "Test erfolgreich", f"✓ Verbindung zu {profile.host} erfolgreich!")
                    
                except Exception as e:
                    QMessageBox.critical(self, "Test fehlgeschlagen", f"✗ {e}")
        finally:
            session.close()
    
    def _delete_profile(self, profile_id: int):
        """Delete a profile."""
        reply = QMessageBox.question(
            self,
            "Profil löschen",
            "Möchten Sie dieses SMTP-Profil wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session = get_session_simple()
            try:
                profile = session.query(SmtpProfile).filter(SmtpProfile.id == profile_id).first()
                if profile:
                    name = profile.name
                    session.delete(profile)
                    session.commit()
                    log_user_action("SMTP-Profil gelöscht", name)
                    self._load_profiles()
            finally:
                session.close()
    
    def _create_profile(self):
        """Open dialog to create new SMTP profile."""
        dialog = SmtpProfileDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_profile_data()
            password = data.pop('password', '')
            
            session = get_session_simple()
            try:
                profile = SmtpProfile(
                    name=data['name'],
                    host=data['host'],
                    port=data['port'],
                    use_ssl=data['use_ssl'],
                    use_tls=data['use_tls'],
                    username=data['username'],
                    use_keyring=data['use_keyring'],
                    from_name=data['from_name'],
                    from_email=data['from_email'],
                    reply_to=data.get('reply_to'),
                    max_per_hour=data['max_per_hour'],
                    max_per_day=data['max_per_day'],
                    delay_seconds=data['delay_seconds'],
                    is_default=data['is_default'],
                    is_active=True,
                )
                
                session.add(profile)
                session.flush()  # Get ID
                
                if password:
                    profile.set_password(password)
                
                # Wenn als Standard markiert, andere Profile deaktivieren
                if data['is_default']:
                    session.query(SmtpProfile).filter(
                        SmtpProfile.id != profile.id
                    ).update({'is_default': False})
                
                session.commit()
                
                log_user_action("Neues SMTP-Profil erstellt", data['name'])
                logger.info(f"SMTP-Profil erstellt: {data['name']}")
                
                self._load_profiles()
                QMessageBox.information(
                    self,
                    "Profil erstellt",
                    f"SMTP-Profil '{data['name']}' wurde erstellt."
                )
            except Exception as e:
                session.rollback()
                logger.error(f"Fehler beim Erstellen des SMTP-Profils: {e}")
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Profil konnte nicht erstellt werden:\n{e}"
                )
            finally:
                session.close()
    
    def refresh(self):
        """Refresh the profiles list."""
        self._load_profiles()
