from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QFrame
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
    """Shown after a sample has been successfully captured."""

    def __init__(self, sample_name: str, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Sample Captured")
        self.setMinimumWidth(340)
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

        from PyQt6.QtWidgets import QLabel
        title = QLabel("Sample Captured Successfully")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
        root.addWidget(title)

        root.addWidget(_h_rule())

        body = QLabel(f"The following sample has been saved:\n\n{sample_name}")
        body.setFont(QFont("Helvetica Neue", 10))
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        body.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
        root.addWidget(body)

        root.addWidget(_h_rule())

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(36)
        ok_btn.setFont(QFont("Helvetica Neue", 9))
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton         {{ background-color: {BG_BTN}; color: {TEXT_MAIN};
                                   border: none; border-radius: 4px; padding: 5px 16px; }}
            QPushButton:hover   {{ background-color: {BG_BTN_H}; }}
            QPushButton:pressed {{ background-color: {BG_BTN_P}; }}
        """)
        ok_btn.clicked.connect(self.accept)
        root.addWidget(ok_btn)
