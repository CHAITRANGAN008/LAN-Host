"""Premium dark theme stylesheet for LAN Host application."""

PREMIUM_DARK_THEME = """
/* ============================================================================
   LAN HOST - PREMIUM DARK THEME
   Color Palette:
   - Main Background:     #10111B (Deep Navy)
   - Card Background:     #1B1D2B
   - Secondary Surface:   #242738
   - Primary Accent:      #5798FF (Electric Blue)
   - Success:             #35D69A
   - Error:               #FF5C68
   - Primary Text:        #F4F6FF
   - Secondary Text:      #929BB5
   ============================================================================ */

/* --- Global Application --- */
QApplication {
    background-color: #10111B;
    color: #F4F6FF;
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
}

/* --- Main Window --- */
QMainWindow {
    background-color: #10111B;
    border: none;
}

QMainWindow::separator {
    background: #242738;
    width: 1px;
    height: 1px;
}

/* --- Central Widget --- */
QWidget#centralWidget {
    background-color: #10111B;
}

/* --- Cards / Panels --- */
QFrame#card {
    background-color: #1B1D2B;
    border: 1px solid #242738;
    border-radius: 14px;
    padding: 16px;
}

QFrame#card:hover {
    border-color: #2E3142;
}

QFrame#cardHeader {
    background-color: transparent;
    border: none;
}

/* --- Labels --- */
QLabel {
    color: #F4F6FF;
    background-color: transparent;
}

QLabel#titleLabel {
    font-size: 30px;
    font-weight: 700;
    color: #F4F6FF;
    letter-spacing: -0.5px;
}

QLabel#subtitleLabel {
    font-size: 13px;
    color: #929BB5;
    margin-top: -2px;
}

QLabel#versionLabel {
    font-size: 11px;
    font-weight: 600;
    color: #5798FF;
    background-color: #1B1D2B;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid #2E3142;
}

QLabel#sectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #F4F6FF;
    margin-bottom: 8px;
}

QLabel#sectionSubtitle {
    font-size: 12px;
    color: #929BB5;
}

QLabel#footerLabel {
    font-size: 11px;
    color: #5A627A;
    font-weight: 400;
}

QLabel#statusLabel {
    font-size: 13px;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 20px;
    min-width: 140px;
}

QLabel#statusLabel[status="running"] {
    background-color: rgba(53, 214, 154, 0.15);
    color: #35D69A;
    border: 1px solid rgba(53, 214, 154, 0.3);
}

QLabel#statusLabel[status="stopped"] {
    background-color: rgba(255, 92, 104, 0.15);
    color: #FF5C68;
    border: 1px solid rgba(255, 92, 104, 0.3);
}

QLabel#statusLabel[status="starting"] {
    background-color: rgba(87, 152, 255, 0.15);
    color: #5798FF;
    border: 1px solid rgba(87, 152, 255, 0.3);
}

QLabel#statusLabel[status="stopping"] {
    background-color: rgba(255, 165, 0, 0.15);
    color: #FFA500;
    border: 1px solid rgba(255, 165, 0, 0.3);
}

QLabel#statusLabel[status="error"] {
    background-color: rgba(255, 92, 104, 0.2);
    color: #FF5C68;
    border: 1px solid rgba(255, 92, 104, 0.4);
}

QLabel#pathLabel {
    font-size: 12px;
    color: #B8BDD0;
    background-color: #242738;
    padding: 12px 14px;
    border-radius: 10px;
    border: 1px solid #2E3142;
    font-family: "Consolas", "Cascadia Code", "JetBrains Mono", monospace;
}

QLabel#ipLabel {
    font-size: 17px;
    font-weight: 600;
    color: #5798FF;
    font-family: "Consolas", "Cascadia Code", "JetBrains Mono", monospace;
    background-color: #242738;
    padding: 14px 18px;
    border-radius: 10px;
    border: 1px solid #2E3142;
}

QLabel#urlLabel {
    font-size: 13px;
    color: #5798FF;
    background-color: #242738;
    padding: 12px 14px;
    border-radius: 10px;
    border: 1px solid #2E3142;
    font-family: "Consolas", "Cascadia Code", "JetBrains Mono", monospace;
}

QLabel#placeholderLabel {
    font-size: 13px;
    color: #6C758A;
    font-style: italic;
}

/* --- Buttons --- */
QPushButton {
    background-color: #242738;
    color: #F4F6FF;
    border: 1px solid #2E3142;
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #2E3142;
    border-color: #3A3E52;
}

QPushButton:pressed {
    background-color: #1B1D2B;
    border-color: #242738;
}

QPushButton:disabled {
    background-color: #1A1C2A;
    color: #5A627A;
    border-color: #242738;
}

QPushButton:focus {
    border-color: #5798FF;
    outline: none;
}

/* Primary Action Button */
QPushButton#primaryButton {
    background-color: #5798FF;
    color: #10111B;
    border: none;
    font-weight: 600;
    padding: 14px 32px;
    font-size: 14px;
    border-radius: 10px;
}

QPushButton#primaryButton:hover {
    background-color: #6BA4FF;
}

QPushButton#primaryButton:pressed {
    background-color: #4880E6;
}

QPushButton#primaryButton:disabled {
    background-color: #2E3142;
    color: #5A627A;
}

/* Danger/Stop Button */
QPushButton#dangerButton {
    background-color: #FF5C68;
    color: #10111B;
    border: none;
    font-weight: 600;
    padding: 14px 32px;
    font-size: 14px;
    border-radius: 10px;
}

QPushButton#dangerButton:hover {
    background-color: #FF737D;
}

QPushButton#dangerButton:pressed {
    background-color: #E04A54;
}

QPushButton#dangerButton:disabled {
    background-color: #2E3142;
    color: #5A627A;
}

/* Secondary Button */
QPushButton#secondaryButton {
    background-color: #242738;
    color: #F4F6FF;
    border: 1px solid #2E3142;
    padding: 10px 18px;
    font-size: 12px;
    font-weight: 500;
    border-radius: 10px;
}

QPushButton#secondaryButton:hover {
    background-color: #2E3142;
    border-color: #3A3E52;
}

QPushButton#secondaryButton:pressed {
    background-color: #1B1D2B;
}

/* Icon Button */
QPushButton#iconButton {
    background-color: transparent;
    border: none;
    padding: 8px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    border-radius: 8px;
    font-size: 16px;
}

QPushButton#iconButton:hover {
    background-color: #242738;
}

QPushButton#iconButton:pressed {
    background-color: #2E3142;
}

/* --- Line Edit / Spin Box --- */
QLineEdit, QSpinBox {
    background-color: #242738;
    color: #F4F6FF;
    border: 1px solid #2E3142;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: #5798FF;
    selection-color: #10111B;
}

QLineEdit:hover, QSpinBox:hover {
    border-color: #3A3E52;
}

QLineEdit:focus, QSpinBox:focus {
    border-color: #5798FF;
    background-color: #1B1D2B;
}

QLineEdit:disabled, QSpinBox:disabled {
    background-color: #1A1C2A;
    color: #5A627A;
    border-color: #242738;
}

/* Spin Box specific */
QSpinBox::up-button, QSpinBox::down-button {
    background-color: transparent;
    border: none;
    width: 24px;
    subcontrol-origin: border;
}

QSpinBox::up-button {
    subcontrol-position: top right;
    border-radius: 0 10px 0 0;
}

QSpinBox::down-button {
    subcontrol-position: bottom right;
    border-radius: 0 0 10px 0;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #2E3142;
}

QSpinBox::up-arrow, QSpinBox::down-arrow {
    width: 12px;
    height: 12px;
}

QSpinBox::up-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM5MjliQjUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMTggMTVsLTYtNi02IDYiLz48L3N2Zz4=);
}

QSpinBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM5MjliQjUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNNiA5bDYgNiA2LTYiLz48L3N2Zz4=);
}

/* --- Scroll Area --- */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #10111B;
    width: 8px;
    border: none;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #3A3E52;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4A4F66;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* --- Separator --- */
QFrame[frameShape="4"] {
    background-color: #2E3142;
    max-height: 1px;
    max-width: 1px;
    border: none;
}

/* --- ToolTip --- */
QToolTip {
    background-color: #1B1D2B;
    color: #F4F6FF;
    border: 1px solid #2E3142;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}

/* --- Message Box --- */
QMessageBox {
    background-color: #1B1D2B;
}

QMessageBox QLabel {
    color: #F4F6FF;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* --- Dialog --- */
QDialog {
    background-color: #1B1D2B;
    color: #F4F6FF;
}

/* --- QFileDialog --- */
QFileDialog {
    background-color: #1B1D2B;
    color: #F4F6FF;
}

QFileDialog QLabel {
    color: #F4F6FF;
}

QFileDialog QPushButton {
    background-color: #242738;
    color: #F4F6FF;
    border: 1px solid #2E3142;
    border-radius: 8px;
    padding: 8px 16px;
}

QFileDialog QPushButton:hover {
    background-color: #2E3142;
    border-color: #3A3E52;
}

QFileDialog QListView, QFileDialog QTreeView {
    background-color: #10111B;
    border: 1px solid #2E3142;
    border-radius: 8px;
    color: #F4F6FF;
}

QFileDialog QLineEdit {
    background-color: #242738;
    color: #F4F6FF;
    border: 1px solid #2E3142;
    border-radius: 8px;
    padding: 8px 12px;
}
"""

def get_stylesheet() -> str:
    """Return the complete premium dark theme stylesheet."""
    return PREMIUM_DARK_THEME