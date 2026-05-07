from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# ── Palette (mirrors the rest of the UI) ─────────────────────────────────────
BG        = "#E4E4E4"
BG_BTN    = "#C8C8C8"
BG_BTN_H  = "#BEBEBE"
BG_BTN_P  = "#B0B0B0"
BORDER    = "#CACACA"
TEXT_MAIN = "#484848"


def _h_rule():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background-color: {BORDER}; border: none;")
    return f


class SampleSuccessDialog(QDialog):
    """
    Shown after a sample capture attempt.

    Parameters
    ----------
    sample_name     : str  — filename of the captured sample
    sent_to_server  : bool — True if the sample was successfully uploaded
    on_reset        : callable | None — called when the user chooses to reset
                      for the next user (same as LoginPanel._on_reset)
    """

    def __init__(
        self,
        sample_name: str,
        sent_to_server: bool,
        on_reset=None,
        parent=None,
    ):
        super().__init__(parent)
        self._on_reset_cb = on_reset
        self.setModal(True)
        self.setWindowTitle("Sample Captured")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"background-color: {BG};")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        # Title
        title = QLabel("Sample Captured Successfully")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
        root.addWidget(title)

        root.addWidget(_h_rule())

        # Filename
        file_label = QLabel(f"File saved:\n{sample_name}")
        file_label.setFont(QFont("Helvetica Neue", 10))
        file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_label.setWordWrap(True)
        file_label.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
        root.addWidget(file_label)

        # Server status
        if sent_to_server:
            server_text = "Sample successfully sent to server."
            server_color = "#4CAF50"
        else:
            server_text = (
                "Server connection could not be established.\n"
                "Sample will be sent once server connection is reestablished."
            )
            server_color = "#E07040"

        server_label = QLabel(server_text)
        server_label.setFont(QFont("Helvetica Neue", 9))
        server_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        server_label.setWordWrap(True)
        server_label.setStyleSheet(
            f"color: {server_color}; background: transparent; border: none;"
        )
        root.addWidget(server_label)

        root.addWidget(_h_rule())

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        take_btn = QPushButton("Continue Session")
        take_btn.setMinimumHeight(36)
        take_btn.setFont(QFont("Helvetica Neue", 9))
        take_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        take_btn.setStyleSheet(f"""
            QPushButton         {{ background-color: {BG_BTN}; color: {TEXT_MAIN};
                                   border: none; border-radius: 4px; padding: 5px 16px; }}
            QPushButton:hover   {{ background-color: {BG_BTN_H}; }}
            QPushButton:pressed {{ background-color: {BG_BTN_P}; }}
        """)
        take_btn.clicked.connect(self.accept)

        reset_btn = QPushButton("Reset for Next User")
        reset_btn.setMinimumHeight(36)
        reset_btn.setFont(QFont("Helvetica Neue", 9))
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet("""
            QPushButton         { background-color: #E07040; color: #FFFFFF;
                                  border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:hover   { background-color: #D06030; }
            QPushButton:pressed { background-color: #C05020; }
        """)
        reset_btn.clicked.connect(self._do_reset)

        btn_row.addStretch()
        btn_row.addWidget(take_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

    def _do_reset(self):
        if self._on_reset_cb:
            self._on_reset_cb()
        self.reject()
