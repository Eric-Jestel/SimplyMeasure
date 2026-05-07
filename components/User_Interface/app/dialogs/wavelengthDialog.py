"""
Wavelength Range Dialog — Setup Page
Chemistry Instrumentation — Jack of all Spades

Lets the user configure the start/end wavelength captured by the instrument.
Updates instrumentParams in memory; values are applied on the next scan/blank.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
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

WAVE_MIN = 190
WAVE_MAX = 1100


def _h_rule():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background-color: {BORDER}; border: none;")
    return f


class WavelengthDialog(QDialog):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self._app = app
        self.setModal(True)
        self.setWindowTitle("Set Wavelength")
        self.setMinimumWidth(340)
        self.setStyleSheet(f"background-color: {BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        # Title
        title = QLabel("Set Wavelength Range")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
        root.addWidget(title)
        root.addWidget(_h_rule())

        # Pull current values from instrumentParams if available
        start_default, stop_default = 900, 300
        if app:
            params = app.controller.InstController.instrumentParams
            try:
                start_default = int(params.get("WavelengthStart", WAVE_MAX))
                stop_default  = int(params.get("WavelengthStop",  WAVE_MIN))
            except (ValueError, TypeError):
                pass

        spin_style = f"""
            QSpinBox {{
                background-color: #DCDCDC;
                border: 1px solid {BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                color: {TEXT_MAIN};
            }}
        """

        # Start row
        start_row = QHBoxLayout()
        start_lbl = QLabel("Start (nm)")
        start_lbl.setFont(QFont("Helvetica Neue", 10))
        start_lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
        self.start_spin = QSpinBox()
        self.start_spin.setRange(WAVE_MIN, WAVE_MAX)
        self.start_spin.setSingleStep(1)
        self.start_spin.setValue(start_default)
        self.start_spin.setFixedWidth(120)
        self.start_spin.setFont(QFont("Helvetica Neue", 10))
        self.start_spin.setStyleSheet(spin_style)
        start_row.addWidget(start_lbl)
        start_row.addStretch()
        start_row.addWidget(self.start_spin)
        root.addLayout(start_row)

        # End row
        end_row = QHBoxLayout()
        end_lbl = QLabel("End (nm)")
        end_lbl.setFont(QFont("Helvetica Neue", 10))
        end_lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
        self.end_spin = QSpinBox()
        self.end_spin.setRange(WAVE_MIN, WAVE_MAX)
        self.end_spin.setSingleStep(1)
        self.end_spin.setValue(stop_default)
        self.end_spin.setFixedWidth(120)
        self.end_spin.setFont(QFont("Helvetica Neue", 10))
        self.end_spin.setStyleSheet(spin_style)
        end_row.addWidget(end_lbl)
        end_row.addStretch()
        end_row.addWidget(self.end_spin)
        root.addLayout(end_row)

        # Info label
        info = QLabel(f"Start must be greater than End. Range: {WAVE_MIN}–{WAVE_MAX} nm")
        info.setFont(QFont("Helvetica Neue", 8))
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; border: none;")
        root.addWidget(info)

        # Inline error label (hidden until validation fails)
        self._error_lbl = QLabel("")
        self._error_lbl.setFont(QFont("Helvetica Neue", 9))
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_lbl.setStyleSheet("color: #B04040; background: transparent; border: none;")
        self._error_lbl.setVisible(False)
        root.addWidget(self._error_lbl)

        root.addWidget(_h_rule())

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setFont(QFont("Helvetica Neue", 9))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton           {{ background-color: {BG_BTN}; color: {TEXT_MAIN};
                                     border: none; border-radius: 4px; padding: 5px 16px; }}
            QPushButton:hover     {{ background-color: {BG_BTN_H}; }}
            QPushButton:pressed   {{ background-color: {BG_BTN_P}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        apply_btn = QPushButton("Apply")
        apply_btn.setMinimumHeight(36)
        apply_btn.setFont(QFont("Helvetica Neue", 9))
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet("""
            QPushButton         { background-color: #4CAF50; color: #FFFFFF;
                                  border: none; border-radius: 4px; padding: 5px 16px; }
            QPushButton:hover   { background-color: #43A047; }
            QPushButton:pressed { background-color: #388E3C; }
        """)
        apply_btn.clicked.connect(self._on_apply)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(apply_btn)
        root.addLayout(btn_row)

    def _on_apply(self):
        start = self.start_spin.value()
        end   = self.end_spin.value()

        if start <= end:
            self._error_lbl.setText("Start must be greater than End.")
            self._error_lbl.setVisible(True)
            return

        if self._app:
            self._app.controller.InstController.changeSettings(
                waveStart=start, waveStop=end
            )
            instrument_page = self._app.pages.get("session")
            if instrument_page is not None:
                instrument_page.data_viewer.set_x_range(end, start)

        self.accept()
