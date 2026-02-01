"""
Obscuras Campaign Manager - Dark Theme Stylesheet
PyQt6 stylesheet for consistent dark UI appearance.
"""

# ═══════════════════════════════════════════════════════════════════
# COLOR PALETTE (Matching Obscuras Branding)
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    "bg_dark": "#0a0a0f",
    "bg_main": "#18181b",
    "bg_card": "#27272a",
    "bg_hover": "#3f3f46",
    "bg_selected": "#52525b",
    
    "text_primary": "#fafafa",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    
    "accent_primary": "#6366f1",  # Indigo
    "accent_secondary": "#8b5cf6",  # Purple
    "accent_tertiary": "#a855f7",  # Pink-purple
    
    "success": "#22c55e",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",
    
    "border": "#3f3f46",
    "border_light": "#52525b",
}

# ═══════════════════════════════════════════════════════════════════
# MAIN STYLESHEET
# ═══════════════════════════════════════════════════════════════════

DARK_STYLESHEET = """
/* ═══════════════════════════════════════════════════════════════ */
/* GLOBAL STYLES                                                    */
/* ═══════════════════════════════════════════════════════════════ */

QWidget {
    background-color: #18181b;
    color: #fafafa;
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0a0a0f;
}

/* ═══════════════════════════════════════════════════════════════ */
/* MENU BAR                                                         */
/* ═══════════════════════════════════════════════════════════════ */

QMenuBar {
    background-color: #18181b;
    border-bottom: 1px solid #27272a;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #27272a;
}

QMenu {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #6366f1;
}

QMenu::separator {
    height: 1px;
    background-color: #27272a;
    margin: 4px 8px;
}

/* ═══════════════════════════════════════════════════════════════ */
/* TOOLBAR                                                          */
/* ═══════════════════════════════════════════════════════════════ */

QToolBar {
    background-color: #18181b;
    border: none;
    spacing: 8px;
    padding: 8px;
}

QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    color: #a1a1aa;
}

QToolButton:hover {
    background-color: #27272a;
    color: #fafafa;
}

QToolButton:pressed {
    background-color: #3f3f46;
}

QToolButton:checked {
    background-color: #6366f1;
    color: #ffffff;
}

/* ═══════════════════════════════════════════════════════════════ */
/* BUTTONS                                                          */
/* ═══════════════════════════════════════════════════════════════ */

QPushButton {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 8px 16px;
    color: #fafafa;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3f3f46;
    border-color: #52525b;
}

QPushButton:pressed {
    background-color: #52525b;
}

QPushButton:disabled {
    background-color: #18181b;
    color: #71717a;
    border-color: #27272a;
}

/* Primary Button */
QPushButton[class="primary"], QPushButton#primaryButton {
    background-color: #6366f1;
    border-color: #6366f1;
}

QPushButton[class="primary"]:hover, QPushButton#primaryButton:hover {
    background-color: #4f46e5;
    border-color: #4f46e5;
}

/* Success Button */
QPushButton[class="success"] {
    background-color: #22c55e;
    border-color: #22c55e;
}

/* Danger Button */
QPushButton[class="danger"] {
    background-color: #ef4444;
    border-color: #ef4444;
}

/* Icon Buttons (small action buttons in tables) */
QPushButton#iconButton {
    font-size: 16px;
    padding: 2px;
    min-width: 28px;
    min-height: 28px;
}

/* ═══════════════════════════════════════════════════════════════ */
/* INPUT FIELDS                                                     */
/* ═══════════════════════════════════════════════════════════════ */

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0a0a0f;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 8px 12px;
    color: #fafafa;
    selection-background-color: #6366f1;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #6366f1;
}

QLineEdit:disabled, QTextEdit:disabled {
    background-color: #18181b;
    color: #71717a;
}

/* ═══════════════════════════════════════════════════════════════ */
/* COMBO BOX                                                        */
/* ═══════════════════════════════════════════════════════════════ */

QComboBox {
    background-color: #0a0a0f;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 8px 12px;
    padding-right: 30px;
    color: #fafafa;
}

QComboBox:hover {
    border-color: #52525b;
}

QComboBox:focus {
    border-color: #6366f1;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #a1a1aa;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    selection-background-color: #6366f1;
}

/* ═══════════════════════════════════════════════════════════════ */
/* SPIN BOX                                                         */
/* ═══════════════════════════════════════════════════════════════ */

QSpinBox, QDoubleSpinBox {
    background-color: #0a0a0f;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 8px 12px;
    color: #fafafa;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #27272a;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #3f3f46;
}

/* ═══════════════════════════════════════════════════════════════ */
/* CHECKBOX & RADIO                                                 */
/* ═══════════════════════════════════════════════════════════════ */

QCheckBox, QRadioButton {
    spacing: 8px;
    color: #fafafa;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3f3f46;
    background-color: #0a0a0f;
}

QCheckBox::indicator {
    border-radius: 4px;
}

QRadioButton::indicator {
    border-radius: 10px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #6366f1;
    border-color: #6366f1;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #6366f1;
}

/* ═══════════════════════════════════════════════════════════════ */
/* TAB WIDGET                                                       */
/* ═══════════════════════════════════════════════════════════════ */

QTabWidget::pane {
    border: 1px solid #27272a;
    border-radius: 8px;
    background-color: #18181b;
}

QTabBar::tab {
    background-color: #0a0a0f;
    border: 1px solid #27272a;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 2px;
    color: #a1a1aa;
}

QTabBar::tab:selected {
    background-color: #18181b;
    color: #fafafa;
    border-color: #6366f1;
    border-top: 2px solid #6366f1;
}

QTabBar::tab:hover:!selected {
    background-color: #27272a;
    color: #fafafa;
}

/* ═══════════════════════════════════════════════════════════════ */
/* TABLE VIEW                                                       */
/* ═══════════════════════════════════════════════════════════════ */

QTableView, QTableWidget {
    background-color: #0a0a0f;
    border: 1px solid #27272a;
    border-radius: 8px;
    gridline-color: #27272a;
    selection-background-color: #6366f1;
}

QTableView::item, QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #27272a;
}

QTableView::item:selected, QTableWidget::item:selected {
    background-color: #6366f1;
}

QHeaderView::section {
    background-color: #18181b;
    border: none;
    border-bottom: 1px solid #27272a;
    border-right: 1px solid #27272a;
    padding: 10px 12px;
    color: #a1a1aa;
    font-weight: 600;
}

QHeaderView::section:hover {
    background-color: #27272a;
}

/* ═══════════════════════════════════════════════════════════════ */
/* TREE VIEW & LIST VIEW                                            */
/* ═══════════════════════════════════════════════════════════════ */

QTreeView, QListView {
    background-color: #0a0a0f;
    border: 1px solid #27272a;
    border-radius: 8px;
    selection-background-color: #6366f1;
}

QTreeView::item, QListView::item {
    padding: 8px;
    border-radius: 4px;
}

QTreeView::item:selected, QListView::item:selected {
    background-color: #6366f1;
}

QTreeView::item:hover, QListView::item:hover {
    background-color: #27272a;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    border-image: none;
}

/* ═══════════════════════════════════════════════════════════════ */
/* SCROLL BAR                                                       */
/* ═══════════════════════════════════════════════════════════════ */

QScrollBar:vertical {
    background-color: #0a0a0f;
    width: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #3f3f46;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #52525b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #0a0a0f;
    height: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #3f3f46;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #52525b;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ═══════════════════════════════════════════════════════════════ */
/* PROGRESS BAR                                                     */
/* ═══════════════════════════════════════════════════════════════ */

QProgressBar {
    background-color: #27272a;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:0.5 #8b5cf6, stop:1 #a855f7);
    border-radius: 6px;
}

/* ═══════════════════════════════════════════════════════════════ */
/* GROUP BOX                                                        */
/* ═══════════════════════════════════════════════════════════════ */

QGroupBox {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 24px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 8px;
    background-color: #18181b;
    color: #a1a1aa;
}

/* ═══════════════════════════════════════════════════════════════ */
/* SPLITTER                                                         */
/* ═══════════════════════════════════════════════════════════════ */

QSplitter::handle {
    background-color: #27272a;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #6366f1;
}

/* ═══════════════════════════════════════════════════════════════ */
/* DIALOG                                                           */
/* ═══════════════════════════════════════════════════════════════ */

QDialog {
    background-color: #18181b;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
}

/* ═══════════════════════════════════════════════════════════════ */
/* STATUS BAR                                                       */
/* ═══════════════════════════════════════════════════════════════ */

QStatusBar {
    background-color: #0a0a0f;
    border-top: 1px solid #27272a;
    color: #71717a;
}

QStatusBar::item {
    border: none;
}

/* ═══════════════════════════════════════════════════════════════ */
/* TOOLTIP                                                          */
/* ═══════════════════════════════════════════════════════════════ */

QToolTip {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    padding: 6px 10px;
    color: #fafafa;
}

/* ═══════════════════════════════════════════════════════════════ */
/* DOCK WIDGET                                                      */
/* ═══════════════════════════════════════════════════════════════ */

QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QDockWidget::title {
    background-color: #18181b;
    border-bottom: 1px solid #27272a;
    padding: 8px;
    text-align: left;
}

QDockWidget::close-button, QDockWidget::float-button {
    border: none;
    background: transparent;
    padding: 2px;
}

/* ═══════════════════════════════════════════════════════════════ */
/* LABEL VARIANTS                                                   */
/* ═══════════════════════════════════════════════════════════════ */

QLabel {
    color: #fafafa;
}

QLabel[class="header"] {
    font-size: 24px;
    font-weight: 700;
    color: #fafafa;
}

QLabel[class="subheader"] {
    font-size: 14px;
    color: #a1a1aa;
}

QLabel[class="muted"] {
    color: #71717a;
}

QLabel[class="success"] {
    color: #22c55e;
}

QLabel[class="error"] {
    color: #ef4444;
}

QLabel[class="warning"] {
    color: #f59e0b;
}
"""
