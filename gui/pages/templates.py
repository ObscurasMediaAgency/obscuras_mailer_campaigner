"""
Obscuras Campaign Manager - Templates Page
Email template management with HTML editor and preview.
"""

from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QComboBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QSplitter, QTabWidget,
    QPlainTextEdit, QGroupBox
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
    
    def _update_preview(self):
        """Update the HTML preview."""
        html = self.html_editor.toPlainText()
        
        # Replace sample variables for preview
        sample_data = {
            "{{EMAIL}}": "beispiel@domain.de",
            "{{FIRMA}}": "Muster GmbH",
            "{{DOMAIN}}": "muster-gmbh.de",
            "{{PRAXISNAME}}": "Dr. Muster Praxis",
            "{{PROBLEM}}": "Die Website ist nicht mobiloptimiert",
            "{{YEAR}}": "2025",
        }
        
        for var, value in sample_data.items():
            html = html.replace(var, f'<span style="background:#6366f1;padding:2px 4px;border-radius:2px;">{value}</span>')
        
        if _has_webengine:
            self.preview.setHtml(html)
        else:
            self.preview.setHtml(html)
    
    def get_template_data(self) -> dict[str, Any]:
        """Get form data as dictionary."""
        return {
            "name": self.name_edit.text(),
            "category": self.category_combo.currentText(),
            "subject_template": self.subject_edit.text(),
            "html_content": self.html_editor.toPlainText(),
            "text_content": self.text_editor.toPlainText(),
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
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip("Bearbeiten")
            actions_layout.addWidget(edit_btn)
            
            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(28, 28)
            copy_btn.setToolTip("Duplizieren")
            actions_layout.addWidget(copy_btn)
            
            preview_btn = QPushButton("👁")
            preview_btn.setFixedSize(28, 28)
            preview_btn.setToolTip("Vorschau")
            actions_layout.addWidget(preview_btn)
            
            delete_btn = QPushButton("🗑")
            delete_btn.setFixedSize(28, 28)
            delete_btn.setToolTip("Löschen")
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 4, actions)
            self.table.setRowHeight(row, 50)
    
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
