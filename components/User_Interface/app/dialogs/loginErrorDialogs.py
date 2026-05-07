"""
Login error dialogs — Instrument Page
Chemistry Instrumentation — Jack of all Spades
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# ── Palette (mirrors the rest of the UI) ─────────────────────────────────────
BG       = "#E4E4E4"
BG_BTN   = "#C8C8C8"
BG_BTN_H = "#BEBEBE"
BG_BTN_P = "#B0B0B0"
BORDER   = "#CACACA"
TEXT_MAIN  = "#484848"
TEXT_MUTED = "#909090"


def _h_rule():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background-color: {BORDER}; border: none;")
    return f


def _base_layout(dialog, title_text):
    """Build the common title + rule layout; return the root QVBoxLayout."""
    root = QVBoxLayout(dialog)
    root.setContentsMargins(24, 20, 24, 20)
    root.setSpacing(12)

    title = QLabel(title_text)
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
    title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
    root.addWidget(title)
    root.addWidget(_h_rule())

    return root


def _body_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont("Helvetica Neue", 10))
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
    return lbl


def _cancel_style():
    return f"""
        QPushButton           {{ background-color: {BG_BTN}; color: {TEXT_MAIN};
                                 border: none; border-radius: 4px; padding: 5px 16px; }}
        QPushButton:hover     {{ background-color: {BG_BTN_H}; }}
        QPushButton:pressed   {{ background-color: {BG_BTN_P}; }}
    """


# ── Generic styled error dialog ──────────────────────────────────────────────
class StyledErrorDialog(QDialog):
    """Single-button error/warning dialog that always applies explicit styling."""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(title)
        self.setMinimumWidth(340)
        self.setStyleSheet(f"background-color: {BG};")

        root = _base_layout(self, title)
        root.addWidget(_body_label(message))
        root.addWidget(_h_rule())

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(36)
        ok_btn.setFont(QFont("Helvetica Neue", 9))
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton         { background-color: #4CAF50; color: #FFFFFF;
                                  border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:hover   { background-color: #43A047; }
            QPushButton:pressed { background-color: #388E3C; }
        """)
        ok_btn.clicked.connect(self.accept)
        root.addWidget(ok_btn)


# ── Dialog 1 : Invalid username (code 220) ────────────────────────────────────
class InvalidUsernameDialog(QDialog):
    """
    Shown when the server returns code 220 — username not recognised.
    User dismisses and tries a different username.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Login Failed")
        self.setMinimumWidth(340)
        self.setStyleSheet(f"background-color: {BG};")

        root = _base_layout(self, "Username Not Recognised")

        root.addWidget(_body_label(
            "Your username could not be validated by the server.\n\n"
            "Please check your username and try again."
        ))

        root.addWidget(_h_rule())

        ok_btn = QPushButton("Try Again")
        ok_btn.setMinimumHeight(36)
        ok_btn.setFont(QFont("Helvetica Neue", 9))
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton         { background-color: #4CAF50; color: #FFFFFF;
                                  border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:hover   { background-color: #43A047; }
            QPushButton:pressed { background-color: #388E3C; }
        """)
        ok_btn.clicked.connect(self.accept)
        root.addWidget(ok_btn)


# ── Dialog 2 : Server offline (code 110) ─────────────────────────────────────
class ServerOfflineDialog(QDialog):
    """
    Shown when the server cannot be reached during login (code 110).

    Call exec() then check accepted() to decide whether to enter offline mode:
        dialog = ServerOfflineDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # proceed offline
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Server Unavailable")
        self.setMinimumWidth(360)
        self.setStyleSheet(f"background-color: {BG};")

        root = _base_layout(self, "Server Could Not Connect")

        root.addWidget(_body_label(
            "The server could not be reached and your login could not be verified.\n\n"
            "You can continue in offline mode to take samples without logging in, "
            "or cancel and try again later."
        ))

        root.addWidget(_h_rule())

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setFont(QFont("Helvetica Neue", 9))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(_cancel_style())
        cancel_btn.clicked.connect(self.reject)

        offline_btn = QPushButton("Continue Offline")
        offline_btn.setMinimumHeight(36)
        offline_btn.setFont(QFont("Helvetica Neue", 9))
        offline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        offline_btn.setStyleSheet("""
            QPushButton         { background-color: #E07040; color: #FFFFFF;
                                  border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:hover   { background-color: #D06030; }
            QPushButton:pressed { background-color: #C05020; }
        """)
        offline_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(offline_btn)
        root.addLayout(btn_row)
