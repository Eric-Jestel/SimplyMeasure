# QApplication root + page router
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import QSize

from app.config import APP_TITLE, WINDOW_MIN_SIZE
from app.state import UIState
from app.views.setup_page import SetupPage
from app.views.instrument_page import InstrumentPage

try:
    from components.SystemController import SystemController
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))
    from components.SystemController import SystemController


class PrototypeApp:
    def __init__(self):
        self.qt_app = QApplication.instance() or QApplication(sys.argv)

        self.state = UIState()
        self.controller = SystemController(debug=self.state.debug_mode)

        startup_code = self.controller.startUp()
        self.state.instrument_connected = startup_code != 100
        self.state.server_status = "OK" if startup_code != 110 else "Disconnected"

        # Main window
        self.window = QMainWindow()
        self.window.setWindowTitle(APP_TITLE)
        self.window.setMinimumSize(QSize(*WINDOW_MIN_SIZE))

        # Stacked widget replaces tkinter's overlapping frames
        self.stack = QStackedWidget()
        self.window.setCentralWidget(self.stack)

        # Build pages
        self.pages = {}
        for PageCls, name in [
            (SetupPage, "setup"),
            (InstrumentPage, "session"),
        ]:
            page = PageCls(app=self, main_window=self)
            self.stack.addWidget(page)
            self.pages[name] = page

        self.show("setup")

    def show(self, name: str):
        """Switch the visible page by name."""
        self.stack.setCurrentWidget(self.pages[name])

    # Convenience navigation methods called by the page widgets
    def go_to_setup_page(self):
        self.show("setup")

    def go_to_instrument_page(self):
        self.show("session")

    def run(self):
        self.window.show()
        sys.exit(self.qt_app.exec())
