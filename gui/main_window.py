"""
Obscuras Campaign Manager - Main Window
Central window with navigation and content areas.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton,
    QStatusBar, QToolBar,
    QMessageBox
)
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent

from gui.widgets.sidebar import Sidebar
from gui.pages.dashboard import DashboardPage
from gui.pages.campaigns import CampaignsPage
from gui.pages.contacts import ContactsPage
from gui.pages.templates import TemplatesPage
from gui.pages.smtp_settings import SmtpSettingsPage
from gui.pages.blacklist import BlacklistPage
from gui.pages.company_settings import CompanySettingsPage
from gui.pages.license import LicensePage
from utils.logging_config import get_logger, log_user_action

logger = get_logger("gui.main_window")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        logger.info("MainWindow wird initialisiert...")
        
        self.setWindowTitle("Mailer Campaigner - Obscuras Media Agency")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Setup UI
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_statusbar()
        
        # Connect signals
        self._connect_signals()
        
        # Show dashboard by default
        self.navigate_to("dashboard")
        logger.info("MainWindow erfolgreich initialisiert")
    
    def _setup_menubar(self) -> None:
        """Setup the menu bar."""
        menubar = self.menuBar()
        if menubar is None:
            return
        
        # ═══════════════════════════════════════════════════════════
        # FILE MENU
        # ═══════════════════════════════════════════════════════════
        file_menu = menubar.addMenu("&Datei")
        if file_menu is not None:
            new_campaign = QAction("&Neue Kampagne", self)
            new_campaign.setShortcut(QKeySequence.StandardKey.New)
            new_campaign.triggered.connect(self._on_new_campaign)
            file_menu.addAction(new_campaign)
            
            import_contacts = QAction("Kontakte &importieren", self)
            import_contacts.setShortcut(QKeySequence("Ctrl+I"))
            import_contacts.triggered.connect(self._on_import_contacts)
            file_menu.addAction(import_contacts)
            
            file_menu.addSeparator()
            
            export_action = QAction("&Exportieren...", self)
            export_action.setShortcut(QKeySequence("Ctrl+E"))
            file_menu.addAction(export_action)
            
            file_menu.addSeparator()
            
            quit_action = QAction("&Beenden", self)
            quit_action.setShortcut(QKeySequence.StandardKey.Quit)
            quit_action.triggered.connect(self.close)
            file_menu.addAction(quit_action)
        
        # ═══════════════════════════════════════════════════════════
        # VIEW MENU
        # ═══════════════════════════════════════════════════════════
        view_menu = menubar.addMenu("&Ansicht")
        if view_menu is not None:
            dashboard_action = QAction("&Dashboard", self)
            dashboard_action.setShortcut(QKeySequence("Ctrl+1"))
            dashboard_action.triggered.connect(lambda: self.navigate_to("dashboard"))
            view_menu.addAction(dashboard_action)
            
            campaigns_action = QAction("&Kampagnen", self)
            campaigns_action.setShortcut(QKeySequence("Ctrl+2"))
            campaigns_action.triggered.connect(lambda: self.navigate_to("campaigns"))
            view_menu.addAction(campaigns_action)
            
            contacts_action = QAction("K&ontakte", self)
            contacts_action.setShortcut(QKeySequence("Ctrl+3"))
            contacts_action.triggered.connect(lambda: self.navigate_to("contacts"))
            view_menu.addAction(contacts_action)
            
            templates_action = QAction("&Templates", self)
            templates_action.setShortcut(QKeySequence("Ctrl+4"))
            templates_action.triggered.connect(lambda: self.navigate_to("templates"))
            view_menu.addAction(templates_action)
        
        # ═══════════════════════════════════════════════════════════
        # CAMPAIGN MENU
        # ═══════════════════════════════════════════════════════════
        campaign_menu = menubar.addMenu("&Kampagne")
        if campaign_menu is not None:
            start_action = QAction("&Starten", self)
            start_action.setShortcut(QKeySequence("F5"))
            start_action.triggered.connect(self._on_start_campaign)
            campaign_menu.addAction(start_action)
            
            pause_action = QAction("&Pausieren", self)
            pause_action.setShortcut(QKeySequence("F6"))
            pause_action.triggered.connect(self._on_pause_campaign)
            campaign_menu.addAction(pause_action)
            
            stop_action = QAction("St&oppen", self)
            stop_action.setShortcut(QKeySequence("Shift+F5"))
            stop_action.triggered.connect(self._on_stop_campaign)
            campaign_menu.addAction(stop_action)
            
            campaign_menu.addSeparator()
            
            preview_action = QAction("&Vorschau", self)
            preview_action.setShortcut(QKeySequence("Ctrl+P"))
            preview_action.triggered.connect(self._on_preview)
            campaign_menu.addAction(preview_action)
            
            test_send_action = QAction("&Test-E-Mail senden", self)
            test_send_action.setShortcut(QKeySequence("Ctrl+T"))
            test_send_action.triggered.connect(self._on_test_email)
            campaign_menu.addAction(test_send_action)
        
        # ═══════════════════════════════════════════════════════════
        # SETTINGS MENU
        # ═══════════════════════════════════════════════════════════
        settings_menu = menubar.addMenu("&Einstellungen")
        if settings_menu is not None:
            company_action = QAction("&Firma / Branding", self)
            company_action.triggered.connect(lambda: self.navigate_to("company"))
            settings_menu.addAction(company_action)
            
            smtp_action = QAction("&SMTP-Profile", self)
            smtp_action.triggered.connect(lambda: self.navigate_to("smtp"))
            settings_menu.addAction(smtp_action)
            
            blacklist_action = QAction("&Blacklist", self)
            blacklist_action.triggered.connect(lambda: self.navigate_to("blacklist"))
            settings_menu.addAction(blacklist_action)
            
            settings_menu.addSeparator()
            
            preferences_action = QAction("&Einstellungen...", self)
            preferences_action.setShortcut(QKeySequence("Ctrl+,"))
            preferences_action.triggered.connect(self._on_preferences)
            settings_menu.addAction(preferences_action)
        
        # ═══════════════════════════════════════════════════════════
        # HELP MENU
        # ═══════════════════════════════════════════════════════════
        help_menu = menubar.addMenu("&Hilfe")
        if help_menu is not None:
            docs_action = QAction("&Dokumentation", self)
            docs_action.setShortcut(QKeySequence.StandardKey.HelpContents)
            help_menu.addAction(docs_action)
            
            help_menu.addSeparator()
            
            about_action = QAction("Ü&ber", self)
            about_action.triggered.connect(self._on_about)
            help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup the main toolbar."""
        toolbar = QToolBar("Hauptwerkzeuge")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Quick actions
        new_btn = QPushButton("+ Neue Kampagne")
        new_btn.setObjectName("primaryButton")
        new_btn.clicked.connect(self._on_new_campaign)
        toolbar.addWidget(new_btn)
        
        toolbar.addSeparator()
        
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self._on_import_contacts)
        toolbar.addWidget(import_btn)
        
        toolbar.addSeparator()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self._on_refresh)
        refresh_btn.setShortcut(QKeySequence("Ctrl+R"))
        toolbar.addWidget(refresh_btn)
        
        # Spacer
        spacer = QWidget()
        spacer.setFixedWidth(20)
        toolbar.addWidget(spacer)
    
    def _setup_central_widget(self):
        """Setup the central widget with sidebar and content area."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar navigation
        self.sidebar = Sidebar()
        layout.addWidget(self.sidebar)
        
        # Content area with stacked pages
        self.content_stack = QStackedWidget()
        self.content_stack.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content_stack, stretch=1)
        
        # Create pages
        self.pages: dict[str, QWidget] = {
            "dashboard": DashboardPage(),
            "campaigns": CampaignsPage(),
            "contacts": ContactsPage(),
            "templates": TemplatesPage(),
            "smtp": SmtpSettingsPage(),
            "blacklist": BlacklistPage(),
            "company": CompanySettingsPage(),
            "license": LicensePage(),
        }
        
        # Set navigate_to callback for pages that need it
        dashboard_page = self.pages["dashboard"]
        if hasattr(dashboard_page, 'navigate_to'):
            dashboard_page.navigate_to = self.navigate_to  # type: ignore[attr-defined]
        
        # Add pages to stack
        for _, page in self.pages.items():
            self.content_stack.addWidget(page)
    
    def _setup_statusbar(self):
        """Setup the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Status sections
        self.status_label = QLabel("Bereit")
        self.statusbar.addWidget(self.status_label, stretch=1)
        
        self.campaign_status = QLabel("")
        self.statusbar.addPermanentWidget(self.campaign_status)
        
        self.connection_status = QLabel("● SMTP OK")
        self.connection_status.setStyleSheet("color: #22c55e;")
        self.statusbar.addPermanentWidget(self.connection_status)
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.sidebar.navigation_changed.connect(self.navigate_to)
    
    def navigate_to(self, page_name: str):
        """Navigate to a specific page."""
        if page_name in self.pages:
            logger.debug(f"Navigation zu: {page_name}")
            log_user_action("Navigation", f"Seite: {page_name}")
            self.content_stack.setCurrentWidget(self.pages[page_name])
            self.sidebar.set_active(page_name)
            self.status_label.setText(f"{page_name.capitalize()} anzeigen")
    
    def _on_new_campaign(self) -> None:
        """Handle new campaign action."""
        logger.info("Neue Kampagne erstellen")
        log_user_action("Neue Kampagne", "Dialog geöffnet")
        self.navigate_to("campaigns")
        campaigns_page = self.pages["campaigns"]
        if hasattr(campaigns_page, 'create_new_campaign'):
            campaigns_page.create_new_campaign()  # type: ignore[attr-defined]
    
    def _on_import_contacts(self) -> None:
        """Handle import contacts action."""
        logger.info("Kontakte importieren")
        log_user_action("Kontakte importieren", "Dialog geöffnet")
        self.navigate_to("contacts")
        contacts_page = self.pages["contacts"]
        if hasattr(contacts_page, 'import_contacts'):
            contacts_page.import_contacts()  # type: ignore[attr-defined]
    
    def _on_refresh(self) -> None:
        """Refresh the current page."""
        logger.debug("Aktualisiere aktuelle Seite...")
        log_user_action("Aktualisieren", "Manuell")
        
        # Sidebar-Stats aktualisieren
        self.sidebar.refresh_stats()
        
        # Aktuelle Seite aktualisieren
        current_widget = self.content_stack.currentWidget()
        if current_widget is not None:
            refresh_method = getattr(current_widget, 'refresh', None)
            refresh_data_method = getattr(current_widget, 'refresh_data', None)
            if callable(refresh_method):
                refresh_method()
            elif callable(refresh_data_method):
                refresh_data_method()
        
        self.status_label.setText("Aktualisiert")
    
    def _on_about(self):
        """Show about dialog."""
        logger.debug("Über-Dialog geöffnet")
        QMessageBox.about(
            self,
            "Über Obscuras Campaign Manager",
            """<h2>Obscuras Campaign Manager</h2>
            <p>Version 1.0.0</p>
            <p>Professionelles E-Mail-Marketing-Tool für Kaltakquise.</p>
            <p>&copy; 2025 Obscuras Media Agency</p>
            <p><a href="https://obscuras-media-agency.de">obscuras-media-agency.de</a></p>
            """
        )
    
    def _on_preview(self) -> None:
        """Show campaign preview."""
        logger.info("Vorschau anzeigen")
        self.navigate_to("campaigns")
        QMessageBox.information(
            self,
            "Vorschau",
            "Bitte öffnen Sie eine Kampagne zum Bearbeiten und klicken Sie dort auf 'Vorschau'."
        )
    
    def _on_test_email(self) -> None:
        """Send test email."""
        logger.info("Testmail senden")
        self.navigate_to("campaigns")
        QMessageBox.information(
            self,
            "Test-E-Mail",
            "Bitte öffnen Sie eine Kampagne zum Bearbeiten und klicken Sie dort auf 'Testmail senden'."
        )
    
    def _on_start_campaign(self) -> None:
        """Start the selected campaign."""
        logger.info("Kampagne starten")
        log_user_action("Kampagne", "Starten")
        self.navigate_to("campaigns")
        campaigns_page = self.pages["campaigns"]
        if hasattr(campaigns_page, 'start_selected_campaign'):
            campaigns_page.start_selected_campaign()  # type: ignore[attr-defined]
        else:
            QMessageBox.information(
                self,
                "Kampagne starten",
                "Bitte wählen Sie eine Kampagne aus der Liste und klicken Sie auf 'Starten'."
            )
    
    def _on_pause_campaign(self) -> None:
        """Pause the running campaign."""
        logger.info("Kampagne pausieren")
        log_user_action("Kampagne", "Pausieren")
        campaigns_page = self.pages["campaigns"]
        if hasattr(campaigns_page, 'pause_selected_campaign'):
            campaigns_page.pause_selected_campaign()  # type: ignore[attr-defined]
        else:
            QMessageBox.information(
                self,
                "Kampagne pausieren",
                "Keine laufende Kampagne zum Pausieren."
            )
    
    def _on_stop_campaign(self) -> None:
        """Stop the running campaign."""
        logger.info("Kampagne stoppen")
        log_user_action("Kampagne", "Stoppen")
        campaigns_page = self.pages["campaigns"]
        if hasattr(campaigns_page, 'stop_selected_campaign'):
            campaigns_page.stop_selected_campaign()  # type: ignore[attr-defined]
        else:
            QMessageBox.information(
                self,
                "Kampagne stoppen",
                "Keine laufende Kampagne zum Stoppen."
            )
    
    def _on_preferences(self) -> None:
        """Open preferences dialog."""
        logger.info("Einstellungen öffnen")
        log_user_action("Einstellungen", "Dialog geöffnet")
        # Navigiere zu Firma/Branding als Standard-Einstellungsseite
        self.navigate_to("company")
    
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Handle window close event."""
        logger.debug("Schließen-Event empfangen")
        # Check for running campaigns
        reply = QMessageBox.question(
            self,
            "Beenden bestätigen",
            "Möchten Sie den Campaign Manager wirklich beenden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Anwendung wird beendet (Benutzer bestätigt)")
            log_user_action("Beenden", "Anwendung geschlossen")
            if a0 is not None:
                a0.accept()
        else:
            logger.debug("Schließen abgebrochen")
            if a0 is not None:
                a0.ignore()
