# QApplication root + page router
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import QSize

from app.config import APP_TITLE, WINDOW_MIN_SIZE
from app.state import UIState
from app.views.setupPage import SetupPage
from app.views.instrumentPage import InstrumentPage
from components.SystemController import SystemController


class App:
    def __init__(self, PROJECT_ROOT):
        self.PROJECT_ROOT = PROJECT_ROOT
        self.qt_app = QApplication.instance() or QApplication(sys.argv)

        self.state = UIState()
        self.controller = SystemController(
            debug=self.state.debug_mode, PROJECT_ROOT=self.PROJECT_ROOT
        )

        startup_code = self.controller.startUp()
        self.state.instrument_connected = startup_code != 100
        self.state.server_status = "OK" if startup_code == 0 else "Disconnected"

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

        self.window.closeEvent = self.closeEvent

    def closeEvent(self, event):
        print("[App][RECEIVED] closeEvent")

        if self.controller:
            print("[App][TX] SystemController.stopProgram")
            self.controller.stopProgram()

        print("[App][EXECUTED] closeEvent -> accepted")
        event.accept()


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
