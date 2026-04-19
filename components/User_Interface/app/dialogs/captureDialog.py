from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# ── Palette ─────────────────────
BG = "#E4E4E4"
BORDER = "#CACACA"
TEXT_MAIN = "#484848"
TEXT_MUTED = "#909090"


class CaptureDialog(QDialog):
    """
    Blocking progress dialog shown while a sample is being captured.
    The user cannot close or dismiss it — it closes programmatically
    once the capture completes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Capturing Sample")
        self.setModal(True)
        self.setFixedSize(340, 120)

        # Remove the close button from the title bar
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        self.setStyleSheet(f"background-color: {BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel("Please wait while the sample is being captured....")
        msg.setFont(QFont("Helvetica Neue", 10))
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f"color: {TEXT_MAIN}; background: transparent; border: none;"
        )
        layout.addWidget(msg)

    def closeEvent(self, event):
        """Prevent the user from closing the dialog manually."""
        event.ignore()

    def reject(self):
        """Prevent ESC key and clicking outside from closing the dialog."""
        pass
