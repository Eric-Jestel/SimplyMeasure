"""
Cary 60 UV-Vis Spectrometer GUI — Setup / Blank Screen
Chemistry Instrumentation — Jack of all Spades
"""

import os

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.widgets.plot import BlankPlot
from app.dialogs.wavelengthDialog import WavelengthDialog

# ── Palette ───────────────────────────────────────────────────────────────────
BG = "#E4E4E4"
BG_INSET = "#DCDCDC"
BG_BTN = "#C8C8C8"
BG_BTN_HOV = "#BEBEBE"
BG_BTN_PRS = "#B0B0B0"
BORDER = "#CACACA"
TEXT_MAIN = "#484848"
TEXT_MUTED = "#909090"
TEXT_BTN = "#3A3A3A"


# ── Button ────────────────────────────────────────────────────────────────────
class StyledButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Helvetica Neue", 9))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_BTN};
                color: {TEXT_BTN};
                border: none;
                border-radius: 4px;
                padding: 5px 16px;
            }}
            QPushButton:hover   {{ background-color: {BG_BTN_HOV}; }}
            QPushButton:pressed {{ background-color: {BG_BTN_PRS}; }}
            """)


# ── Panel ─────────────────────────────────────────────────────────────────────
class Panel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            Panel {{
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 5px;
            }}
            """)


# ── Inset box ─────────────────────────────────────────────────────────────────
class InsetBox(QFrame):
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_INSET};
                border: none;
                border-radius: 3px;
            }}
            """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        if text:
            lbl = QLabel(text)
            lbl.setFont(QFont("Helvetica Neue", 9))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"color: {TEXT_MUTED}; background: transparent; border: none;"
            )
            layout.addWidget(lbl)


# ── Thin rule ─────────────────────────────────────────────────────────────────
def h_rule():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background-color: {BORDER}; border: none;")
    return f


# ── Panel 1 : Title Widget ────────────────────────────────────────────────────────
class BrandingPanel(Panel):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(4)

        title = QLabel("SimplyMeasure")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Georgia", 17, QFont.Weight.Bold))
        title.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(h_rule())
        layout.addSpacing(10)

        for text in [
            "Developed by Jack of all Spades",
            "Computer Science Capstone, Class of 2026"
        ]:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Helvetica Neue", 8))
            lbl.setStyleSheet(
                f"color: {TEXT_MUTED}; background: transparent; border: none;"
            )
            layout.addWidget(lbl)


# ── Connection sub-panel ──────────────────────────────────────────────────────
class ConnectionSubPanel(QWidget):
    def __init__(
        self,
        heading: str,
        info_text: str,
        reconnect_cmd=None,
        parent=None,
    ):
        super().__init__(parent)
        self._reconnect_cmd = reconnect_cmd
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        heading_lbl = QLabel(heading)
        heading_lbl.setFont(QFont("Helvetica Neue", 10))
        heading_lbl.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        layout.addWidget(heading_lbl)

        row = QHBoxLayout()
        row.setSpacing(10)

        info_box = InsetBox(info_text)
        info_box.setMinimumHeight(90)
        info_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        right = QVBoxLayout()
        right.setSpacing(4)

        status_lbl = QLabel("Connection status:")
        status_lbl.setFont(QFont("Helvetica Neue", 9))
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none;"
        )

        self.status_btn = QPushButton("Checking...")
        self.status_btn.setFixedWidth(140)
        self.status_btn.setFixedHeight(38)
        self.status_btn.setFont(QFont("Helvetica Neue", 9))
        self.status_btn.setCursor(Qt.CursorShape.ArrowCursor)
        self.status_btn.clicked.connect(self._on_status_clicked)
        self._apply_neutral_style()

        right.addStretch()
        right.addWidget(status_lbl)
        right.addWidget(self.status_btn)
        right.addStretch()

        row.addWidget(info_box)
        row.addLayout(right)
        layout.addLayout(row)

    def _on_status_clicked(self):
        if self._reconnect_cmd:
            self._reconnect_cmd()

    def _apply_neutral_style(self):
        self.status_btn.setEnabled(False)
        self.status_btn.setStyleSheet("""
            QPushButton          { background-color: #C8C8C8; color: #484848;
                                   border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:disabled { background-color: #C8C8C8; color: #484848; }
        """)

    def set_status(self, text: str, ok: bool = True):
        if ok:
            self.status_btn.setText("Connected")
            self.status_btn.setEnabled(False)
            self.status_btn.setCursor(Qt.CursorShape.ArrowCursor)
            self.status_btn.setStyleSheet("""
                QPushButton          { background-color: #4CAF50; color: #FFFFFF;
                                       border: none; border-radius: 4px; padding: 5px 16px; }
                QPushButton:disabled { background-color: #4CAF50; color: #FFFFFF; }
            """)
        else:
            self.status_btn.setText("Reconnect")
            self.status_btn.setEnabled(True)
            self.status_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.status_btn.setStyleSheet("""
                QPushButton         { background-color: #C04040; color: #FFFFFF;
                                      border: none; border-radius: 4px; padding: 5px 16px; }
                QPushButton:hover   { background-color: #B03030; }
                QPushButton:pressed { background-color: #A02020; }
            """)


# ── Panel 2 : Status ──────────────────────────────────────────────────────────
class StatusPanel(Panel):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(24)

        self.instr_sub = ConnectionSubPanel(
            "Instrument Information",
            "Ensure the instrument is powered on and connected via USB before continuing. If the status shows disconnected, check the cable and press Reconnect.",
            reconnect_cmd=self._on_reconnect_instrument,
        )
        layout.addWidget(self.instr_sub, stretch=1)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFixedWidth(1)
        div.setStyleSheet(f"background-color: {BORDER}; border: none;")
        layout.addWidget(div)

        self.server_sub = ConnectionSubPanel(
            "ICN Server Information",
            "The ICN server is required to log in and upload sample data. If the connection cannot be established, you may continue in offline mode, though data will not be synced until reconnected.",
            reconnect_cmd=self._on_reconnect_server,
        )
        layout.addWidget(self.server_sub, stretch=1)

        if app:
            instr_ok = app.state.instrument_connected
            self.instr_sub.set_status(
                "Connected" if instr_ok else "Disconnected", ok=instr_ok
            )
            serv_ok = app.state.server_status == "OK"
            self.server_sub.set_status(
                "Connected" if serv_ok else "Disconnected", ok=serv_ok
            )

    def _on_reconnect_instrument(self):
        if not self.app:
            return
        connected = self.app.controller.InstController.ping()
        self.app.state.instrument_connected = connected
        self.instr_sub.set_status(
            "Connected" if connected else "Disconnected", ok=connected
        )
        if not connected:
            msg = QMessageBox(self)
            msg.setWindowTitle("Instrument")
            msg.setText("Instrument reconnect failed.")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.exec()

    def _on_reconnect_server(self):
        if not self.app:
            return
        ok = self.app.controller.ServController.connect()
        self.app.state.server_status = "OK" if ok else "Disconnected"
        self.server_sub.set_status("OK" if ok else "Disconnected", ok=ok)
        if not ok:
            msg = QMessageBox(self)
            msg.setWindowTitle("Server")
            msg.setText("Server reconnect failed.")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.exec()


# ── Panel 3 : Actions ─────────────────────────────────────────────────────────
class ActionPanel(Panel):
    def __init__(
        self, plot_panel: "PlotPanel", app=None, main_window=None, parent=None
    ):
        super().__init__(parent)
        self.plot_panel = plot_panel
        self.app = app
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(8)

        button_defs = [
            ("Capture Blank", self._on_capture_blank),
            ("Load Blank from File", self._on_load_blank),
            ("Reset Blank", self._on_reset_blank),
            ("Set Wavelength", self._on_set_wavelength),
            ("Continue to main session", self._on_continue)
        ]

        for text, handler in button_defs:
            btn = StyledButton(text)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            if handler:
                btn.clicked.connect(handler)
            layout.addWidget(btn)

    def _on_capture_blank(self):
        if not self.app:
            return
        from app.dialogs.blanksFolder import get_blanks_folder
        from app.dialogs.captureDialog import CaptureDialog, CaptureWorker
        from datetime import datetime

        blanks_dir = get_blanks_folder(parent=self)
        filename = str(blanks_dir / f"blank_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        self._blank_cancelled = False

        dialog = CaptureDialog(
            title="Capturing Blank",
            message="Please wait while the blank is being captured...",
            parent=self,
        )
        self._blank_worker = CaptureWorker(self.app.controller.takeBlank, filename)

        def on_done(result):
            if self._blank_cancelled:
                return
            dialog.done(0)
            code, blank_path = result
            if code == 0:
                self.app.state.blank_file_path = blank_path
                if blank_path and os.path.exists(blank_path):
                    QMessageBox.information(
                        self, "Capture Blank", f"Blank captured:\n{blank_path}"
                    )
                    self.plot_panel.load_csv(blank_path)
                else:
                    QMessageBox.information(
                        self,
                        "Capture Blank",
                        "Blank command completed. No CSV file was returned by the instrument bridge.",
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Capture Blank",
                    self.app.controller.ErrorDictionary.get(code, f"Error code: {code}"),
                )

        def on_cancel():
            self._blank_cancelled = True
            self.app.state.blank_file_path = None
            if hasattr(self.app.controller.InstController, "clear_blank"):
                self.app.controller.InstController.clear_blank()
            self.plot_panel.clear_plot()

        self._blank_worker.finished.connect(on_done)
        dialog.cancelled.connect(on_cancel)
        self._blank_worker.start()
        dialog.exec()

    def _on_load_blank(self):
        from app.dialogs.blanksFolder import open_blank_file
        filepath = open_blank_file(parent=self)
        if not filepath:
            return

        if self.app:
            code = self.app.controller.setBlank(filepath)
            if code == 0:
                self.app.state.blank_file_path = (
                    filepath  # Set the filepath to plot blank
                )
                self.plot_panel.load_csv(filepath)
                QMessageBox.information(
                    self, "Load Blank", f"Loaded blank file:\n{filepath}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Load Blank",
                    self.app.controller.ErrorDictionary.get(
                        code, f"Error code: {code}"
                    ),
                )

    def _on_reset_blank(self):
        if not self.app:
            return
        if hasattr(self.app.controller.InstController, "clear_blank"):
            self.app.controller.InstController.clear_blank()
        self.app.state.blank_file_path = None
        self.plot_panel.clear_plot()
        instrument_page = self.app.pages.get("session")
        if instrument_page is not None:
            instrument_page.data_viewer.clear_blank()

    def _on_set_wavelength(self):
        dialog = WavelengthDialog(app=self.app, parent=self)
        dialog.exec()

    def _on_continue(self):
        if not self.main_window:
            return
        server_down = self.app and self.app.state.server_status != "OK"
        if server_down:
            reply = QMessageBox.question(
                self,
                "No Server Connection",
                "The server is not connected. Proceed in offline mode?\n\n"
                "In offline mode you can take samples without logging in.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.app.state.offline_mode = True
        self.main_window.go_to_instrument_page()

    def _on_toggle_debug(self):
        if not self.app:
            return
        self.app.state.debug_mode = not self.app.state.debug_mode
        debug_on = self.app.state.debug_mode
        self.app.controller.debug = debug_on
        self.app.controller.InstController.debug = debug_on
        self.app.controller.ServController.debug = debug_on
        QMessageBox.information(
            self, "Debug Mode", f"Debug mode {'enabled' if debug_on else 'disabled'}."
        )


# ── Panel 4 : Plot ────────────────────────────────────────────────────────────
# BlankPlot is imported from app.widgets.plot — it wraps a pyqtgraph PlotWidget
# and exposes load_csv() and clear_plot() exactly as the old inline class did.
PlotPanel = BlankPlot


# ── Setup Page ────────────────────────────────────────────────────────────────
class SetupPage(QWidget):
    def __init__(self, app=None, main_window=None, parent=None):
        super().__init__(parent)
        self.app = app
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Top row
        top = QHBoxLayout()
        top.setSpacing(8)
        branding = BrandingPanel()
        branding.setFixedWidth(270)
        self.status_panel = StatusPanel(app=self.app)
        top.addWidget(branding)
        top.addWidget(self.status_panel)

        # Bottom row
        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        plot = PlotPanel()
        actions = ActionPanel(
            plot_panel=plot, app=self.app, main_window=self.main_window
        )
        actions.setFixedWidth(270)
        bottom.addWidget(actions)
        bottom.addWidget(plot)

        root.addLayout(top, stretch=1)
        root.addLayout(bottom, stretch=3)
