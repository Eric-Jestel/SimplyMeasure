"""
Cary 60 UV-Vis Spectrometer GUI — Instrument / Session Screen
Chemistry Instrumentation — Jack of all Spades
"""

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QLineEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# ── Palette (matches setup_page.py) ──────────────────────────────────────────
BG = "#E4E4E4"
BG_INSET = "#DCDCDC"
BG_BTN = "#C8C8C8"
BG_BTN_HOV = "#BEBEBE"
BG_BTN_PRS = "#B0B0B0"
BORDER = "#CACACA"
TEXT_MAIN = "#484848"
TEXT_MUTED = "#909090"
TEXT_BTN = "#3A3A3A"


# ── Shared helpers ────────────────────────────────────────────────────────────
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


def h_rule():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background-color: {BORDER}; border: none;")
    return f


class StyledButton(QPushButton):
    def __init__(self, text: str, large: bool = False, parent=None):
        super().__init__(text, parent)
        size = 10 if large else 9
        height = 46 if large else 38
        self.setMinimumHeight(height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Helvetica Neue", size))
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


# ── Panel 1 : Login ───────────────────────────────────────────────────────────
class LoginPanel(Panel):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Enter Username")
        title.setFont(QFont("Georgia", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        layout.addWidget(title)
        layout.addWidget(h_rule())
        layout.addSpacing(4)

        lbl = QLabel("Username")
        lbl.setFont(QFont("Helvetica Neue", 9, QFont.Weight.Normal, True))  # italic
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none;"
        )
        layout.addWidget(lbl)

        self.username_input = QLineEdit()
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_input.setFont(QFont("Helvetica Neue", 9))
        self.username_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {BG_INSET};
                color: {TEXT_MAIN};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 5px 10px;
            }}
        """
        )
        if app:
            self.username_input.setText(app.state.username)
        layout.addWidget(self.username_input)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.login_btn = StyledButton("Login")
        self.login_btn.clicked.connect(self._on_login)
        self.reset_btn = StyledButton("Reset")
        self.reset_btn.clicked.connect(self._on_reset)
        btn_row.addWidget(self.login_btn)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

    def _on_login(self):
        if not self.app:
            return
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Login", "Please enter a username.")
            return
        self.app.state.username = username
        code = self.app.controller.signIn(username)
        if code == 0:
            QMessageBox.information(self, "Login", f"Logged in as {username}")
        else:
            QMessageBox.critical(
                self,
                "Login",
                self.app.controller.ErrorDictionary.get(code, f"Error code: {code}"),
            )

    def _on_reset(self):
        self.username_input.clear()
        if self.app:
            self.app.state.username = ""


# ── Panel 2 : Instructions ────────────────────────────────────────────────────
class InstructionsPanel(Panel):
    def __init__(self, explanation_panel: "ExplanationPanel", parent=None):
        super().__init__(parent)
        self.explanation_panel = explanation_panel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Instructions")
        title.setFont(QFont("Georgia", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        layout.addWidget(title)
        layout.addWidget(h_rule())
        layout.addSpacing(4)

        steps = [
            ("Step 1: Login", 1),
            ("Step 2: Capture sample", 2),
            ("Step N: …", 3),
        ]

        for label, step_num in steps:
            btn = StyledButton(label)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(
                lambda _, n=step_num: self.explanation_panel.set_step(n)
            )
            layout.addWidget(btn)

        layout.addStretch()


# ── Panel 3 : Explanation ─────────────────────────────────────────────────────
class ExplanationPanel(Panel):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        inset = InsetBox()
        inset.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.expl_label = QLabel("Explanation of step 1, 2…")
        self.expl_label.setFont(QFont("Helvetica Neue", 10))
        self.expl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.expl_label.setWordWrap(True)
        self.expl_label.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none;"
        )
        inset.layout().addWidget(self.expl_label)

        layout.addWidget(inset)

    def set_step(self, step: int):
        self.expl_label.setText(f"Step {step} explanation placeholder.")
        self.expl_label.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )


# ── Panel 4 : Actions (left bottom) ──────────────────────────────────────────
class ActionPanel(Panel):
    def __init__(self, app=None, main_window=None, parent=None):
        super().__init__(parent)
        self.app = app
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(12)
        layout.addStretch()

        self.take_btn = StyledButton("Take sample", large=True)
        self.take_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.take_btn.clicked.connect(self._on_take_sample)
        layout.addWidget(self.take_btn)

        self.adv_btn = StyledButton("Advanced options", large=True)
        self.adv_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.adv_btn.clicked.connect(self._on_advanced)
        layout.addWidget(self.adv_btn)

        layout.addStretch()

    def _on_take_sample(self):
        if not self.app:
            return
        code, sample = self.app.controller.runLabMachine()
        if code == 0 and sample:
            self.app.state.sample_files.append(sample.name)
            QMessageBox.information(
                self, "Take Sample", f"Sample captured:\n{sample.name}"
            )
            if self.main_window:
                self.main_window.go_to_setup_page()
            return
        QMessageBox.critical(
            self,
            "Take Sample",
            self.app.controller.ErrorDictionary.get(code, f"Error code: {code}"),
        )

    def _on_advanced(self):
        QMessageBox.information(self, "Advanced Options", "Prototype placeholder.")


# ── Panel 5 : Data viewer (plot) ──────────────────────────────────────────────
class DataViewerPanel(Panel):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Data Viewer")
        title.setFont(QFont("Georgia", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        layout.addWidget(title)
        layout.addWidget(h_rule())

        pg.setConfigOptions(antialias=True, background=BG_INSET, foreground=TEXT_MAIN)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.plot_widget.setStyleSheet("border: none; border-radius: 3px;")
        self.plot_widget.getPlotItem().showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("bottom", "Wavelength (nm)", color=TEXT_MAIN)
        self.plot_widget.setLabel("left", "Absorbance (AU)", color=TEXT_MAIN)
        self.plot_widget.setTitle("Sample Data", color=TEXT_MAIN, size="11pt")

        axis_pen = pg.mkPen(color=BORDER, width=1)
        for axis in ["bottom", "left", "top", "right"]:
            self.plot_widget.getPlotItem().getAxis(axis).setPen(axis_pen)
            self.plot_widget.getPlotItem().getAxis(axis).setTextPen(TEXT_MAIN)

        self.placeholder = pg.TextItem(
            text="No samples taken yet — use 'Take sample' to begin",
            color=TEXT_MUTED,
            anchor=(0.5, 0.5),
        )
        self.plot_widget.addItem(self.placeholder)
        self.placeholder.setPos(0.5, 0.5)

        self._curves = {}
        layout.addWidget(self.plot_widget)

    def add_sample(self, name: str, x: list, y: list):
        """Plot a new sample curve. Removes placeholder on first sample."""
        if not self._curves:
            self.plot_widget.removeItem(self.placeholder)

        curve = self.plot_widget.plot(x, y, name=name, pen=pg.mkPen(width=1.5))
        self._curves[name] = curve


# ── Instrument Page ───────────────────────────────────────────────────────────
class InstrumentPage(QWidget):
    def __init__(self, app=None, main_window=None, parent=None):
        super().__init__(parent)
        self.app = app
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Top row: Login | Instructions | Explanation
        top = QHBoxLayout()
        top.setSpacing(8)

        explanation = ExplanationPanel()

        login = LoginPanel(app=self.app)
        login.setMinimumWidth(300)

        instructions = InstructionsPanel(explanation_panel=explanation)
        instructions.setMinimumWidth(300)

        top.addWidget(login, stretch=2)
        top.addWidget(instructions, stretch=2)
        top.addWidget(explanation, stretch=3)

        # Bottom row: Actions | Data viewer
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        actions = ActionPanel(app=self.app, main_window=self.main_window)
        actions.setFixedWidth(260)

        self.data_viewer = DataViewerPanel()

        bottom.addWidget(actions)
        bottom.addWidget(self.data_viewer)

        root.addLayout(top, stretch=1)
        root.addLayout(bottom, stretch=3)
