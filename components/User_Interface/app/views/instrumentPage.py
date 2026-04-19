"""
Cary 60 UV-Vis Spectrometer GUI — Instrument / Session Screen
Simply — Jack of all Spades
"""

from app.widgets.plot import SamplePlot
from pathlib import Path
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

# ── Palette ──────────────────────────────────────────
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
        self.setStyleSheet(f"""
            Panel {{
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 5px;
            }}
            """)


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


# ── Panel 1 : Login ───────────────────────────────────────────────────────────
class LoginPanel(Panel):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Login")
        title.setFont(QFont("Georgia", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        layout.addWidget(title)
        layout.addWidget(h_rule())
        layout.addSpacing(4)

        lbl = QLabel("Enter Username")
        lbl.setFont(QFont("Helvetica Neue", 9, QFont.Weight.Normal, True))  # italic
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none;"
        )
        layout.addWidget(lbl)

        self.username_input = QLineEdit()
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_input.setFont(QFont("Helvetica Neue", 9))
        self.username_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_INSET};
                color: {TEXT_MAIN};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 5px 10px;
            }}
            """)
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
            ("Step 2: Load Sample", 2),
            ("Step 3: Capture Sample", 3),
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

        self.expl_label = QLabel("Log in by entering your ICN username.")
        self.expl_label.setFont(QFont("Helvetica Neue", 10))
        self.expl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.expl_label.setWordWrap(True)
        self.expl_label.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none;"
        )
        inset.layout().addWidget(self.expl_label)

        layout.addWidget(inset)

    def set_step(self, step: int):
        explanations = {
            1: "Log in by entering your ICN username.",
            2: "Place your sample in the instrument. Ensure the sample holder is clean and properly positioned. The smooth side of Cuvette should be facing the camera.",
            3: "Press Capture to begin the measurement. Do not move the sample until the reading is complete.",
        }

        text = explanations.get(step, "No explanation available.")
        self.expl_label.setText(text)
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

        self.take_btn = StyledButton("Take sample", large=True)
        self.take_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.take_btn.clicked.connect(self._on_take_sample)
        layout.addWidget(self.take_btn, stretch=1)

        self.adv_btn = StyledButton("Advanced options", large=True)
        self.adv_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.adv_btn.clicked.connect(self._on_advanced)
        layout.addWidget(self.adv_btn)

    def _on_take_sample(self):
        if not self.app:
            return
        code, csv_path = (
            self.app.controller.runLabMachine()
        )  # CSV path is accetped as a return from runLabMachine()
        if code == 0 and csv_path:
            sample_name = Path(csv_path).name
            self.app.state.sample_files.append(csv_path)
            QMessageBox.information(
                self, "Take Sample", f"Sample captured:\n{sample_name}"
            )
            # Plot the new sample on the instrument page data viewer
            if self.main_window:
                data_viewer = self.main_window.pages["session"].data_viewer
                data_viewer.add_sample_csv(sample_name, csv_path)
            return
        QMessageBox.critical(
            self,
            "Take Sample",
            self.app.controller.ErrorDictionary.get(code, f"Error code: {code}"),
        )

    def _on_advanced(self):
        from app.dialogs.advancedOptions import AdvancedOptionsDialog

        dialog = AdvancedOptionsDialog(parent=self, app=self.app)
        dialog.exec()


# ── Panel 5 : Data viewer (plot) ──────────────────────────────────────────────
class DataViewerPanel(SamplePlot):
    """
    Thin subclass of SamplePlot that wraps it in the same Panel styling
    used by the rest of the instrument page.
    All plot logic lives in SamplePlot (app/widgets/plot.py).
    """

    pass


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

    def showEvent(self, event):
        """
        Auto-load the blank into the plot whenever this page becomes visible.
        This ensures the reference curve is always present even if the user
        captures or loads a blank after first navigating here.
        """
        super().showEvent(event)
        if self.app and self.app.state.blank_file_path:
            self.data_viewer.load_blank(self.app.state.blank_file_path)
