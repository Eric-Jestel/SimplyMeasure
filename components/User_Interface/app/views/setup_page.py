"""
Cary 60 UV-Vis Spectrometer GUI — Setup / Blank Screen
Chemistry Instrumentation — Jack of all Spades
"""

import csv
from datetime import datetime
from pathlib import Path

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    # QApplication,
    # QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QComboBox,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

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
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_BTN};
                color: {TEXT_BTN};
                border: none;
                border-radius: 4px;
                padding: 5px 16px;
            }}
            QPushButton:hover   {{ background-color: {BG_BTN_HOV}; }}
            QPushButton:pressed {{ background-color: {BG_BTN_PRS}; }}
        """
        )


# ── Panel ─────────────────────────────────────────────────────────────────────
class Panel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            Panel {{
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 5px;
            }}
        """
        )


# ── Inset box ─────────────────────────────────────────────────────────────────
class InsetBox(QFrame):
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_INSET};
                border: none;
                border-radius: 3px;
            }}
        """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        if text:
            lbl = QLabel(text)
            lbl.setFont(QFont("Helvetica Neue", 9))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
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


# ── Panel 1 : Branding ────────────────────────────────────────────────────────
class BrandingPanel(Panel):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(4)

        title = QLabel("Chemistry\nInstrumentation")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Georgia", 15, QFont.Weight.Bold))
        title.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(h_rule())
        layout.addSpacing(10)

        for text in [
            "Developed by Jack of all Spades",
            "Licensed under …, 2025",
            "Developer Contact Info?",
        ]:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Helvetica Neue", 9))
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
        show_instrument_selector: bool = False,
        reconnect_cmd=None,
        parent=None,
    ):
        super().__init__(parent)
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

        if show_instrument_selector:
            type_label = QLabel("Instrument type")
            type_label.setFont(QFont("Helvetica Neue", 9))
            type_label.setStyleSheet(
                f"color: {TEXT_MUTED}; background: transparent; border: none;"
            )

            self.instrument_combo = QComboBox()
            self.instrument_combo.addItems(
                [
                    "Cary 60 UV-Vis",
                    "Bruker Alpha II IR",
                ]
            )
            self.instrument_combo.setFont(QFont("Helvetica Neue", 9))
            self.instrument_combo.setStyleSheet(
                f"""
                QComboBox {{
                    background-color: {BG_INSET};
                    color: {TEXT_MAIN};
                    border: 1px solid {BORDER};
                    border-radius: 4px;
                    padding: 4px 8px;
                    height: 26px;
                }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
                QComboBox QAbstractItemView {{
                    background-color: {BG_INSET};
                    color: {TEXT_MAIN};
                    selection-background-color: {BG_BTN};
                    selection-color: {TEXT_BTN};
                    border: 1px solid {BORDER};
                }}
            """
            )

            layout.addWidget(type_label)
            layout.addWidget(self.instrument_combo)
            layout.addWidget(h_rule())

        row = QHBoxLayout()
        row.setSpacing(10)

        # Status label that can be updated
        self.status_box = InsetBox("Connection status")
        self.status_box.setFixedWidth(140)
        self.status_box.setFixedHeight(38)

        info_box = InsetBox(info_text)
        info_box.setMinimumHeight(68)
        info_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        right = QVBoxLayout()
        right.setSpacing(6)
        right.addWidget(self.status_box)

        reconnect_btn = StyledButton("Reconnect")
        reconnect_btn.setFixedWidth(140)
        if reconnect_cmd:
            reconnect_btn.clicked.connect(reconnect_cmd)
        right.addWidget(reconnect_btn)
        right.addStretch()

        row.addWidget(info_box)
        row.addLayout(right)
        layout.addLayout(row)

    def set_status(self, text: str, ok: bool = True):
        """Update the connection status label text and colour."""
        # Clear old label and set a new one
        layout = self.status_box.layout()
        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        color = TEXT_MAIN if ok else "#B04040"
        lbl = QLabel(text)
        lbl.setFont(QFont("Helvetica Neue", 9))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        layout.addWidget(lbl)


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
            "Instrument information",
            show_instrument_selector=True,
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
            "Server Diagnostic\nInformation",
            reconnect_cmd=self._on_reconnect_server,
        )
        layout.addWidget(self.server_sub, stretch=1)

    def _on_reconnect_instrument(self):
        if not self.app:
            return
        connected = self.app.controller.InstController.ping()
        self.app.state.instrument_connected = connected
        self.instr_sub.set_status(
            "Connected" if connected else "Disconnected", ok=connected
        )
        if not connected:
            QMessageBox.warning(self, "Instrument", "Instrument reconnect failed.")

    def _on_reconnect_server(self):
        if not self.app:
            return
        ok = self.app.controller.ServController.connect()
        self.app.state.server_status = "OK" if ok else "Disconnected"
        self.server_sub.set_status("OK" if ok else "Disconnected", ok=ok)
        if not ok:
            QMessageBox.warning(self, "Server", "Server reconnect failed.")


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
        layout.setSpacing(0)

        button_defs = [
            ("Capture Blank", self._on_capture_blank),
            ("Load Blank from File", self._on_load_blank),
            ("Reset Blank", self._on_reset_blank),
            ("Save Blank to File", self._on_save_blank),
            ("Continue to main session", self._on_continue),
            ("Debugging mode", self._on_toggle_debug),
        ]

        layout.addStretch()
        for text, handler in button_defs:
            btn = StyledButton(text)
            btn.setFixedHeight(34)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            if handler:
                btn.clicked.connect(handler)
            layout.addWidget(btn)
            layout.addStretch()

    def _on_capture_blank(self):
        if not self.app:
            return
        target = (
            Path(self.app.controller.ServController.file_dir)
            / f"blank_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        code, blank_path = self.app.controller.takeBlank(str(target))
        if code == 0:
            self.app.state.blank_file_path = blank_path
            QMessageBox.information(
                self, "Capture Blank", f"Blank captured:\n{blank_path}"
            )
        else:
            QMessageBox.critical(
                self,
                "Capture Blank",
                self.app.controller.ErrorDictionary.get(code, f"Error code: {code}"),
            )

    def _on_load_blank(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Blank Spectrum", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not filepath:
            return

        if self.app:
            code = self.app.controller.setBlank(filepath)
            if code == 0:
                self.app.state.blank_file_path = filepath
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

        # Always plot the file regardless of controller result
        self.plot_panel.load_csv(filepath)

    def _on_reset_blank(self):
        if not self.app:
            return
        if hasattr(self.app.controller.InstController, "clear_blank"):
            self.app.controller.InstController.clear_blank()
        self.app.state.blank_file_path = None
        self.plot_panel.clear_plot()

    def _on_save_blank(self):
        if not self.app:
            return
        if self.app.state.blank_file_path:
            QMessageBox.information(
                self,
                "Save Blank",
                "Blank is already stored by the instrument bridge at:\n"
                f"{self.app.state.blank_file_path}",
            )
        else:
            QMessageBox.warning(self, "Save Blank", "No blank is currently loaded.")

    def _on_continue(self):
        if self.main_window:
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
class PlotPanel(Panel):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)

        pg.setConfigOptions(antialias=True, background=BG_INSET, foreground=TEXT_MAIN)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.plot_widget.setStyleSheet("border: none; border-radius: 3px;")
        self.plot_widget.getPlotItem().showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("bottom", "Wavelength (nm)", color=TEXT_MAIN)
        self.plot_widget.setLabel("left", "Absorbance (AU)", color=TEXT_MAIN)
        self.plot_widget.setTitle("Blank Spectrum", color=TEXT_MAIN, size="11pt")

        axis_pen = pg.mkPen(color=BORDER, width=1)
        for axis in ["bottom", "left", "top", "right"]:
            self.plot_widget.getPlotItem().getAxis(axis).setPen(axis_pen)
            self.plot_widget.getPlotItem().getAxis(axis).setTextPen(TEXT_MAIN)

        self.placeholder = pg.TextItem(
            text="No data loaded — use 'Load Blank from File' or 'Capture Blank'",
            color=TEXT_MUTED,
            anchor=(0.5, 0.5),
        )
        self.plot_widget.addItem(self.placeholder)
        self.placeholder.setPos(0.5, 0.5)

        self._curve = None
        outer.addWidget(self.plot_widget)

    def load_csv(self, filepath: str):
        """Read a two-column CSV (wavelength, absorbance) and plot it."""
        x, y = [], []
        try:
            with open(filepath, newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) < 2:
                        continue
                    try:
                        x.append(float(row[0]))
                        y.append(float(row[1]))
                    except ValueError:
                        continue

            if not x:
                raise ValueError("No numeric data found in file.")

            self.plot_widget.removeItem(self.placeholder)

            if self._curve is not None:
                self.plot_widget.removeItem(self._curve)

            self._curve = self.plot_widget.plot(
                x, y, pen=pg.mkPen(color=TEXT_MAIN, width=1.5)
            )

            if header and len(header) >= 2:
                self.plot_widget.setLabel("bottom", header[0], color=TEXT_MAIN)
                self.plot_widget.setLabel("left", header[1], color=TEXT_MAIN)

        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load spectrum:\n{e}")

    def clear_plot(self):
        """Remove current curve and restore placeholder."""
        if self._curve is not None:
            self.plot_widget.removeItem(self._curve)
            self._curve = None
        self.plot_widget.addItem(self.placeholder)
        self.placeholder.setPos(0.5, 0.5)


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
        branding.setFixedWidth(260)
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
        actions.setFixedWidth(260)
        bottom.addWidget(actions)
        bottom.addWidget(plot)

        root.addLayout(top, stretch=1)
        root.addLayout(bottom, stretch=3)
