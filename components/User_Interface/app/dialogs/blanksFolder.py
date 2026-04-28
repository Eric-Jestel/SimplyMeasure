from pathlib import Path

from PyQt6.QtWidgets import QMessageBox, QFileDialog

# ── Palette ─────────────────────
BG        = "#E4E4E4"
BORDER    = "#CACACA"
TEXT_MAIN = "#484848"
TEXT_MUTED = "#909090"


def get_blanks_folder(parent=None) -> Path:
    blanks = Path.home() / "Desktop" / "Blanks"
    if not blanks.exists():
        blanks.mkdir(parents=True)
        msg = QMessageBox(parent)
        msg.setWindowTitle("Blanks Folder Created")
        msg.setText(
            f"No 'Blanks' folder was found on your Desktop.\n\n"
            f"One has been created for you at:\n{blanks}"
        )
        msg.exec()
    return blanks


def open_blank_file(parent=None) -> "str | None":
    blanks = get_blanks_folder(parent)
    filepath, _ = QFileDialog.getOpenFileName(
        parent,
        "Load Blank Spectrum",
        str(blanks),
        "CSV Files (*.csv);;All Files (*)",
    )
    return filepath or None
