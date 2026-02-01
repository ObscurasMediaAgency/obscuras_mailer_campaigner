"""
Obscuras Campaign Manager - Blacklist Page
Email and domain blacklist management.
"""

from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QComboBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QTabWidget, QGroupBox
)


class AddToBlacklistDialog(QDialog):
    """Dialog for adding entries to blacklist."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Zur Blacklist hinzufügen")
        self.setMinimumSize(450, 350)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Type selection
        type_group = QGroupBox("Art des Eintrags")
        type_layout = QHBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["E-Mail-Adresse", "Domain (alle E-Mails)"])
        self.type_combo.setFixedWidth(200)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        
        layout.addWidget(type_group)
        
        # Value input
        value_group = QGroupBox("Wert")
        value_layout = QVBoxLayout(value_group)
        
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("E-Mail-Adresse oder Domain eingeben...")
        value_layout.addWidget(self.value_edit)
        
        hint = QLabel("Tipp: Für Domains ohne @ eingeben (z.B. spam-domain.de)")
        hint.setStyleSheet("color: #71717a; font-size: 11px;")
        value_layout.addWidget(hint)
        
        layout.addWidget(value_group)
        
        # Reason
        reason_group = QGroupBox("Grund")
        reason_layout = QVBoxLayout(reason_group)
        
        self.reason_combo = QComboBox()
        self.reason_combo.addItems([
            "Hard Bounce (Mailbox existiert nicht)",
            "Unsubscribe (Abmeldung)",
            "Beschwerde",
            "Ungültige E-Mail",
            "Manuell hinzugefügt",
        ])
        reason_layout.addWidget(self.reason_combo)
        
        layout.addWidget(reason_group)
        
        # Notes
        notes_group = QGroupBox("Notizen (optional)")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Zusätzliche Informationen...")
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setText("Hinzufügen")
        button_box.accepted.connect(self.accept)  # type: ignore[arg-type]
        button_box.rejected.connect(self.reject)  # type: ignore[arg-type]
        
        layout.addWidget(button_box)
    
    def get_data(self) -> dict[str, Any]:
        """Get form data."""
        return {
            "value": self.value_edit.text().lower().strip(),
            "entry_type": "domain" if self.type_combo.currentIndex() == 1 else "email",
            "reason": self.reason_combo.currentText(),
            "notes": self.notes_edit.toPlainText(),
        }


class BlacklistPage(QWidget):
    """Blacklist management page."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._load_blacklist()
    
    def _setup_ui(self) -> None:
        """Setup the blacklist page UI."""
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
        
        title = QLabel("Blacklist")
        title.setStyleSheet("color: #fafafa; font-size: 28px; font-weight: 700;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Gesperrte E-Mail-Adressen und Domains")
        subtitle.setStyleSheet("color: #71717a; font-size: 14px;")
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        self.add_btn = QPushButton("+ Hinzufügen")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.clicked.connect(self._add_entry)  # type: ignore[arg-type]
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
            ("Gesamt", "47", "#fafafa"),
            ("E-Mails", "42", "#ef4444"),
            ("Domains", "5", "#f59e0b"),
            ("Hard Bounces", "38", "#a1a1aa"),
            ("Abmeldungen", "6", "#a1a1aa"),
        ]:
            stat_item = QLabel(f"{label}: <span style='color:{color};font-weight:600;'>{value}</span>")
            stats_layout.addWidget(stat_item)
        
        stats_layout.addStretch()
        layout.addWidget(stats)
        
        # ═══════════════════════════════════════════════════════════
        # TABS
        # ═══════════════════════════════════════════════════════════
        tabs = QTabWidget()
        
        # All entries tab
        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)
        all_layout.setContentsMargins(0, 12, 0, 0)
        
        # Search
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Suchen...")
        self.search_input.setFixedHeight(36)
        search_layout.addWidget(self.search_input)
        
        type_filter = QComboBox()
        type_filter.addItems(["Alle Typen", "E-Mails", "Domains"])
        type_filter.setFixedWidth(150)
        search_layout.addWidget(type_filter)
        
        reason_filter = QComboBox()
        reason_filter.addItems(["Alle Gründe", "Hard Bounce", "Unsubscribe", "Beschwerde", "Manuell"])
        reason_filter.setFixedWidth(150)
        search_layout.addWidget(reason_filter)
        
        all_layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Wert", "Typ", "Grund", "Hinzugefügt", "Aktionen"])
        
        table_header = self.table.horizontalHeader()
        if table_header is not None:
            table_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            table_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            table_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            table_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            table_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 100)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        vertical_header = self.table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)
        
        all_layout.addWidget(self.table)
        
        tabs.addTab(all_tab, "📋 Alle Einträge")
        
        # Bounces tab
        bounces_tab = QWidget()
        bounces_layout = QVBoxLayout(bounces_tab)
        bounces_layout.setContentsMargins(0, 12, 0, 0)
        
        bounces_info = QLabel(
            "Automatisch hinzugefügte Hard-Bounce-Adressen aus fehlgeschlagenen Zustellungen."
        )
        bounces_info.setStyleSheet("color: #71717a; font-size: 13px;")
        bounces_layout.addWidget(bounces_info)
        
        # Similar table structure would go here
        bounces_layout.addStretch()
        
        tabs.addTab(bounces_tab, "📫 Bounces")
        
        # Unsubscribes tab
        unsub_tab = QWidget()
        unsub_layout = QVBoxLayout(unsub_tab)
        unsub_layout.setContentsMargins(0, 12, 0, 0)
        
        unsub_info = QLabel(
            "Kontakte, die sich von E-Mails abgemeldet haben (DSGVO-konform)."
        )
        unsub_info.setStyleSheet("color: #71717a; font-size: 13px;")
        unsub_layout.addWidget(unsub_info)
        
        unsub_layout.addStretch()
        
        tabs.addTab(unsub_tab, "🚫 Abmeldungen")
        
        layout.addWidget(tabs)
    
    def _load_blacklist(self) -> None:
        """Load blacklist entries from database."""
        # Sample data
        entries = [
            ("ungueltig@test.de", "E-Mail", "Hard Bounce", "31.01.2025 09:15"),
            ("noreply@spam-domain.de", "E-Mail", "Hard Bounce", "30.01.2025 14:22"),
            ("spam-domain.de", "Domain", "Manuell", "29.01.2025 11:00"),
            ("abmeldung@firma.de", "E-Mail", "Unsubscribe", "28.01.2025 16:45"),
            ("fake-email.com", "Domain", "Manuell", "27.01.2025 10:30"),
        ]
        
        self.table.setRowCount(len(entries))
        
        for row, (value, entry_type, reason, date) in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(value))
            
            type_item = QTableWidgetItem(entry_type)
            self.table.setItem(row, 1, type_item)
            
            self.table.setItem(row, 2, QTableWidgetItem(reason))
            self.table.setItem(row, 3, QTableWidgetItem(date))
            
            # Actions
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            delete_btn = QPushButton("✖")
            delete_btn.setObjectName("iconButton")
            delete_btn.setFixedSize(28, 28)
            delete_btn.setToolTip("Entfernen")
            delete_btn.setStyleSheet("font-size: 14px; color: #ef4444;")
            actions_layout.addWidget(delete_btn)
            
            info_btn = QPushButton("ⓘ")
            info_btn.setObjectName("iconButton")
            info_btn.setFixedSize(28, 28)
            info_btn.setToolTip("Details")
            info_btn.setStyleSheet("font-size: 14px; color: #6366f1;")
            actions_layout.addWidget(info_btn)
            
            self.table.setCellWidget(row, 4, actions)
            self.table.setRowHeight(row, 44)
    
    def _add_entry(self) -> None:
        """Open dialog to add new blacklist entry."""
        dialog = AddToBlacklistDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["value"]:
                QMessageBox.warning(self, "Fehler", "Bitte einen Wert eingeben.")
                return
            
            # TODO: Save to database
            self._load_blacklist()
            QMessageBox.information(
                self,
                "Hinzugefügt",
                f"'{data['value']}' wurde zur Blacklist hinzugefügt."
            )
