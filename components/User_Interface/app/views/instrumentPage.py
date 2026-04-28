"""
Cary 60 UV-Vis Spectrometer GUI — Instrument / Session Screen
Simply — Jack of all Spades
"""

from app.widgets.plot import SamplePlot
from app.dialogs.loginErrorDialogs import InvalidUsernameDialog, ServerOfflineDialog
from app.dialogs.sampleSuccessDialog import SampleSuccessDialog
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
    QDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
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
            QPushButton:hover    {{ background-color: {BG_BTN_HOV}; }}
            QPushButton:pressed  {{ background-color: {BG_BTN_PRS}; }}
            QPushButton:disabled {{ background-color: #E8E8E8; color: #A0A0A0; }}
            """)


# ── Panel 1 : Branding ───────────────────────────────────────────────────────
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
            "Computer Science Capstone, Class of 2026",
        ]:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Helvetica Neue", 8))
            lbl.setStyleSheet(
                f"color: {TEXT_MUTED}; background: transparent; border: none;"
            )
            layout.addWidget(lbl)


# ── Panel 2 : Login ───────────────────────────────────────────────────────────
class LoginPanel(Panel):
    login_changed = pyqtSignal(bool)
    session_reset = pyqtSignal()

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

        self.input_label = QLabel("Enter Username")
        self.input_label.setFont(QFont("Helvetica Neue", 9, QFont.Weight.Normal, True))
        self.input_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_label.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none;"
        )
        layout.addWidget(self.input_label)

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

        self.logged_in_label = QLabel("")
        self.logged_in_label.setFont(QFont("Helvetica Neue", 9))
        self.logged_in_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logged_in_label.setWordWrap(True)
        self.logged_in_label.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        self.logged_in_label.setVisible(False)
        layout.addWidget(self.logged_in_label)

        layout.addSpacing(4)

        self.login_btn = StyledButton("Login")
        self.login_btn.setStyleSheet("""
            QPushButton          { background-color: #4CAF50; color: #FFFFFF;
                                   border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:hover    { background-color: #43A047; }
            QPushButton:pressed  { background-color: #388E3C; }
            QPushButton:disabled { background-color: #E8E8E8; color: #A0A0A0; }
        """)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)

        self.reset_btn = StyledButton("Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton          { background-color: #F9A825; color: #FFFFFF;
                                   border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:hover    { background-color: #F57F17; }
            QPushButton:pressed  { background-color: #E65100; }
            QPushButton:disabled { background-color: #E8E8E8; color: #A0A0A0; }
        """)
        self.reset_btn.clicked.connect(self._on_reset)
        self.reset_btn.setVisible(False)
        layout.addWidget(self.reset_btn)

        # Restore logged-in state if already signed in
        if app and app.state.username:
            self._show_reset_state()

    def _show_login_state(self):
        self.input_label.setVisible(True)
        self.username_input.setVisible(True)
        self.logged_in_label.setVisible(False)
        self.login_btn.setVisible(True)
        self.reset_btn.setVisible(False)

    def _show_reset_state(self):
        username = self.username_input.text().strip()
        self.logged_in_label.setText(f"Logged in as: {username}")
        self.input_label.setVisible(False)
        self.username_input.setVisible(False)
        self.logged_in_label.setVisible(True)
        self.login_btn.setVisible(False)
        self.reset_btn.setVisible(True)

    def _on_login(self):
        if not self.app:
            return
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Login", "Please enter a username.")
            return
        code = self.app.controller.signIn(username)
        if code == 0:
            self.app.state.username = username
            self._show_reset_state()
            self.login_changed.emit(True)
        elif code == 220:
            InvalidUsernameDialog(parent=self).exec()
        elif code == 110:
            dialog = ServerOfflineDialog(parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.app.state.offline_mode = True
                self._show_reset_state()
                self.login_changed.emit(True)
        else:
            error = self.app.controller.ErrorDictionary.get(code, f"Error code: {code}")
            QMessageBox.critical(self, "Login Failed", f"Could not verify username.\n\n{error}")

    def _on_reset(self):
        self.username_input.clear()
        if self.app:
            self.app.state.username = ""
            self.app.state.sample_files.clear()
            self.app.state.offline_mode = False
            ok = self.app.controller.ServController.connect()
            self.app.state.server_status = "OK" if ok else "Disconnected"
        self._show_login_state()
        self.login_changed.emit(False)
        self.session_reset.emit()


# ── Panel 2 : Instructions ────────────────────────────────────────────────────
class InstructionsPanel(Panel):
    def __init__(self, parent=None):
        super().__init__(parent)

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

        # Step buttons + explanation side by side
        body = QHBoxLayout()
        body.setSpacing(10)

        steps_col = QVBoxLayout()
        steps_col.setSpacing(8)

        steps = [
            ("Step 1: Login", 1),
            ("Step 2: Load Sample", 2),
            ("Step 3: Capture Sample", 3),
        ]

        for label, step_num in steps:
            btn = StyledButton(label)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _, n=step_num: self._set_step(n))
            steps_col.addWidget(btn)

        steps_col.addStretch()
        body.addLayout(steps_col, stretch=2)

        inset = InsetBox()
        inset.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.expl_label = QLabel("Enter your ICN username and press Login to begin your session. If the server is unavailable, you may continue in offline mode, samples will still be captured and displayed locally.")
        self.expl_label.setFont(QFont("Helvetica Neue", 10))
        self.expl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.expl_label.setWordWrap(True)
        self.expl_label.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none;"
        )
        inset.layout().addWidget(self.expl_label)
        body.addWidget(inset, stretch=3)

        layout.addLayout(body)

    def _set_step(self, step: int):
        explanations = {
            1: "Enter your ICN username and press Login to begin your session. If the server is unavailable, you may continue in offline mode, samples will still be captured and displayed locally.",
            2: "Open the instrument chamber and place your cuvette in the sample holder. Ensure the holder is clean and free of residue. Orient the cuvette so the clear, smooth face is aligned with the light path. Close the chamber before proceeding.",
            3: "Press 'Take Sample' to begin the measurement. Keep the sample and instrument completely still during the scan. Once complete, the spectrum will appear in the plot below. Repeat for additional samples, each will be overlaid for comparison.",
        }
        self.expl_label.setText(explanations.get(step, "No explanation available."))
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
        self.take_btn.setStyleSheet("""
            QPushButton          { background-color: #4CAF50; color: #FFFFFF;
                                   border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:hover    { background-color: #43A047; }
            QPushButton:pressed  { background-color: #388E3C; }
            QPushButton:disabled { background-color: #E8E8E8; color: #A0A0A0; }
        """)
        self.take_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.take_btn.clicked.connect(self._on_take_sample)
        self.take_btn.setEnabled(bool(app and (app.state.username or app.state.offline_mode)))
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
        from app.dialogs.captureDialog import CaptureDialog, CaptureWorker

        self._sample_cancelled = False

        dialog = CaptureDialog(
            title="Capturing Sample",
            message="Please wait while the sample is being captured...",
            parent=self,
        )
        self._sample_worker = CaptureWorker(self.app.controller.runLabMachine)

        def on_done(result):
            if self._sample_cancelled:
                return
            dialog.done(0)
            code, csv_path = result
            if code == 0 and csv_path:
                sample_name = Path(csv_path).name
                self.app.state.sample_files.append(csv_path)
                SampleSuccessDialog(sample_name, parent=self).exec()
                if self.main_window:
                    data_viewer = self.main_window.pages["session"].data_viewer
                    data_viewer.add_sample_csv(sample_name, csv_path)
            else:
                if code == 110 and csv_path:
                    sample_name = Path(csv_path).name
                    if self.main_window:
                        data_viewer = self.main_window.pages["session"].data_viewer
                        data_viewer.add_sample_csv(sample_name, csv_path)

                QMessageBox.critical(
                    self,
                    "Take Sample",
                    self.app.controller.ErrorDictionary.get(code, f"Error code: {code}"),
                )

        def on_cancel():
            self._sample_cancelled = True

        self._sample_worker.finished.connect(on_done)
        dialog.cancelled.connect(on_cancel)
        self._sample_worker.start()
        dialog.exec()

    def set_take_enabled(self, enabled: bool):
        if self.app and self.app.state.offline_mode:
            self.take_btn.setEnabled(True)
            return
        self.take_btn.setEnabled(enabled)

    def _on_advanced(self):
        from app.dialogs.advancedOptions import AdvancedOptionsDialog

        dialog = AdvancedOptionsDialog(parent=self, app=self.app)
        dialog.exec()


# ── Panel 5 : Data viewer ──────────────────────────────────────────────
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
        self.setStyleSheet("")

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Left column: Branding | Login | Actions (fixed 260px)
        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(8)

        branding = BrandingPanel()
        login = LoginPanel(app=self.app)
        actions = ActionPanel(app=self.app, main_window=self.main_window)
        login.login_changed.connect(actions.set_take_enabled)
        login.session_reset.connect(self._on_session_reset)

        left.addWidget(branding, stretch=1)
        left.addWidget(login)
        left.addWidget(actions, stretch=3)

        left_container = QWidget()
        left_container.setFixedWidth(270)
        left_container.setLayout(left)
        left_container.setStyleSheet("background: transparent;")
        root.addWidget(left_container)

        # Right area: Instructions + Explanation on top, Data viewer below
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(8)

        instructions = InstructionsPanel()

        self.data_viewer = DataViewerPanel()

        right.addWidget(instructions, stretch=1)
        right.addWidget(self.data_viewer, stretch=3)

        root.addLayout(right, stretch=1)

    def _on_session_reset(self):
        self.data_viewer.clear_samples()

    def showEvent(self, event):
        super().showEvent(event)
