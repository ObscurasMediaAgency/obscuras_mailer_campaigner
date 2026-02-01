#!/usr/bin/env python3
"""
Obscuras Campaign Manager - Main Application Entry Point
PyQt6-based GUI for email campaign management.

Usage:
    python main.py
    python main.py --debug  # Enable debug mode
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Initialize logging FIRST (before any other imports that use logging)
from utils.logging_config import setup_logging, get_logger

# Check for debug flag
DEBUG_MODE = "--debug" in sys.argv or "-d" in sys.argv
logger = setup_logging(debug_mode=DEBUG_MODE)
main_logger = get_logger("main")

from PyQt6.QtWidgets import QApplication
# from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPalette, QColor

from gui.main_window import MainWindow
from gui.styles import DARK_STYLESHEET
from models.database import init_database


def setup_dark_palette(app: QApplication):
    """Configure dark theme palette."""
    palette = QPalette()
    
    # Base colors (matching Obscuras branding)
    palette.setColor(QPalette.ColorRole.Window, QColor(24, 24, 27))  # #18181b
    palette.setColor(QPalette.ColorRole.WindowText, QColor(250, 250, 250))  # #fafafa
    palette.setColor(QPalette.ColorRole.Base, QColor(10, 10, 15))  # #0a0a0f
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(39, 39, 42))  # #27272a
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(39, 39, 42))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(250, 250, 250))
    palette.setColor(QPalette.ColorRole.Text, QColor(250, 250, 250))
    palette.setColor(QPalette.ColorRole.Button, QColor(39, 39, 42))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(250, 250, 250))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(129, 140, 248))  # #818cf8
    palette.setColor(QPalette.ColorRole.Highlight, QColor(99, 102, 241))  # #6366f1
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    # Disabled colors
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(113, 113, 122))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(113, 113, 122))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(113, 113, 122))
    
    app.setPalette(palette)


def main():
    """Main application entry point."""
    main_logger.info("Starte Obscuras Campaign Manager...")
    
    # Initialize database
    try:
        init_database()
    except Exception as e:
        main_logger.critical(f"Datenbank-Initialisierung fehlgeschlagen: {e}")
        sys.exit(1)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Obscuras Campaign Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Obscuras Media Agency")
    app.setOrganizationDomain("obscuras-media-agency.de")
    
    main_logger.debug("Qt-Anwendung erstellt")
    
    # Apply dark theme
    setup_dark_palette(app)
    app.setStyleSheet(DARK_STYLESHEET)
    main_logger.debug("Dark Theme angewendet")
    
    # Set application icon (if exists)
    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        main_logger.debug(f"Icon geladen: {icon_path}")
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        main_logger.info("Hauptfenster geöffnet")
    except Exception as e:
        main_logger.critical(f"Fenster konnte nicht erstellt werden: {e}")
        sys.exit(1)
    
    # Run application
    main_logger.info("Anwendung läuft...")
    exit_code = app.exec()
    main_logger.info(f"Anwendung beendet (Exit-Code: {exit_code})")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
