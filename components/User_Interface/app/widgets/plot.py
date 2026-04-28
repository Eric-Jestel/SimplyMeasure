"""
Reusable spectrum plot widget — PyQt6 / pyqtgraph
Chemistry Instrumentation — Jack of all Spades

Two modes:
  • BlankPlot   — single curve (setup page / blank reference)
  • SamplePlot  — multi-curve with persistent blank overlay (instrument page)

Both share the same SpectrumPlotWidget base.
"""

import csv

import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QFrame, QSizePolicy, QMessageBox
from PyQt6.QtCore import Qt

# ── Palette (mirrors the rest of the UI) ─────────────────────────────────────
BG = "#E4E4E4"
BG_INSET = "#DCDCDC"
BORDER = "#CACACA"
TEXT_MAIN = "#484848"
TEXT_MUTED = "#909090"

# Curve colours
COLOUR_BLANK = "#606060"  # dark-grey dashed — blank / reference
COLOUR_CYCLE = [  # sample curves, assigned in order
    "#4A90D9",  # blue
    "#E07040",  # orange
    "#50A060",  # green
    "#9060B0",  # purple
    "#C04040",  # red
]


# ── Base widget ───────────────────────────────────────────────────────────────
class SpectrumPlotWidget(QFrame):
    """
    A self-contained pyqtgraph plot embedded in a QFrame.

    Parameters
    ----------
    title       : str   — plot title shown at top
    x_label     : str   — x-axis label
    y_label     : str   — y-axis label
    placeholder : str   — grey text shown when no data is loaded
    x_range     : tuple — initial (min, max) for x axis
    y_range     : tuple — initial (min, max) for y axis
    """

    def __init__(
        self,
        title: str = "Spectrum",
        x_label: str = "Wavelength (nm)",
        y_label: str = "Absorbance (AU)",
        placeholder: str = "No data loaded",
        x_range: tuple = (300, 900),
        y_range: tuple = (0, 1.1),
        parent=None,
    ):
        super().__init__(parent)
        self.setStyleSheet("border: none;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        pg.setConfigOptions(antialias=True, background=BG_INSET, foreground=TEXT_MAIN)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.plot_widget.setStyleSheet("border: none; border-radius: 3px;")

        pi = self.plot_widget.getPlotItem()
        pi.showGrid(x=True, y=True, alpha=0.3)

        self.plot_widget.setLabel("bottom", x_label, color=TEXT_MAIN)
        self.plot_widget.setLabel("left", y_label, color=TEXT_MAIN)
        self.plot_widget.setTitle(title, color=TEXT_MAIN, size="11pt")

        self.plot_widget.setXRange(*x_range, padding=0)
        self.plot_widget.setYRange(*y_range, padding=0)
        self.plot_widget.setLimits(
            xMin=x_range[0],
            xMax=x_range[1],
            yMin=y_range[0],
            yMax=y_range[1],
        )
        self.plot_widget.setMouseEnabled(x=False, y=False)

        axis_pen = pg.mkPen(color=BORDER, width=1)
        for axis in ["bottom", "left", "top", "right"]:
            pi.getAxis(axis).setPen(axis_pen)
            pi.getAxis(axis).setTextPen(TEXT_MAIN)

        # Placeholder text — centred in data-coordinate space
        self._x_mid = (x_range[0] + x_range[1]) / 2
        self._y_mid = (y_range[0] + y_range[1]) / 2
        self._placeholder = pg.TextItem(
            text=placeholder,
            color=TEXT_MUTED,
            anchor=(0.5, 0.5),
        )
        self.plot_widget.addItem(self._placeholder)
        self._placeholder.setPos(self._x_mid, self._y_mid)
        self._placeholder_visible = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)

    # ── internal helpers ──────────────────────────────────────────────────────
    def _hide_placeholder(self):
        if self._placeholder_visible:
            self.plot_widget.removeItem(self._placeholder)
            self._placeholder_visible = False

    def _show_placeholder(self):
        if not self._placeholder_visible:
            self.plot_widget.addItem(self._placeholder)
            self._placeholder.setPos(self._x_mid, self._y_mid)
            self._placeholder_visible = True

    @staticmethod
    def _read_csv(filepath: str):
        """
        Parse a two-column CSV (wavelength, absorbance).
        Returns (x, y, header_row).  Raises ValueError on bad files.
        """
        x, y, header = [], [], []
        with open(filepath, newline="") as f:
            reader = csv.reader(f)
            first = next(reader, None)
            if first:
                try:
                    x.append(float(first[0]))
                    y.append(float(first[1]))
                except (ValueError, IndexError):
                    header = first  # first row is a text header
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
        return x, y, header


# ── Setup-page variant: single blank curve ────────────────────────────────────
class BlankPlot(SpectrumPlotWidget):
    """
    Used on the Setup page.
    Displays a single blank / reference spectrum loaded from a CSV file.
    """

    def __init__(self, parent=None):
        super().__init__(
            title="",
            placeholder="No data loaded — use 'Load Blank from File' or 'Capture Blank'",
            parent=parent,
        )
        self._curve = None

    # ── public API ────────────────────────────────────────────────────────────
    def load_csv(self, filepath: str):
        """Read a two-column CSV (wavelength, absorbance) and plot it."""
        try:
            x, y, header = self._read_csv(filepath)
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load spectrum:\n{e}")
            return

        self._hide_placeholder()

        if self._curve is not None:
            self.plot_widget.removeItem(self._curve)

        self._curve = self.plot_widget.plot(
            x,
            y,
            pen=pg.mkPen(color=COLOUR_BLANK, width=1.5),
        )

        # Use CSV header as axis labels if present
        if header and len(header) >= 2:
            self.plot_widget.setLabel("bottom", header[0], color=TEXT_MAIN)
            self.plot_widget.setLabel("left", header[1], color=TEXT_MAIN)

    def clear_plot(self):
        """Remove curve and restore placeholder."""
        if self._curve is not None:
            self.plot_widget.removeItem(self._curve)
            self._curve = None
        self._show_placeholder()


# ── Instrument-page variant: blank overlay + multiple sample curves ────────────
class SamplePlot(SpectrumPlotWidget):
    """
    Used on the Instrument page.

    Private API
    ----------
    load_blank(filepath)          — load reference curve from CSV
    add_sample(name, x, y)        — add a named sample curve from data lists
    clear_samples()               — remove sample curves; blank is kept
    clear_all()                   — remove everything including blank
    """

    def __init__(self, parent=None):
        super().__init__(
            title="",
            placeholder="No samples taken yet — use 'Take sample' to begin",
            parent=parent,
        )
        self._blank_curve = None
        self._sample_curves: dict = {}
        self._colour_index = 0

        # Legend appears automatically once curves are named
        self._legend = self.plot_widget.addLegend(offset=(10, 10))

    def _next_colour(self) -> str:
        c = COLOUR_CYCLE[self._colour_index % len(COLOUR_CYCLE)]
        self._colour_index += 1
        return c

    # ── public API ────────────────────────────────────────────────────────────
    def load_blank(self, filepath: str):
        """
        Load the blank/reference curve from a CSV file.
        Shown as a dark-grey dashed line behind all sample curves.
        Safe to call again — replaces any existing blank.
        """
        try:
            x, y, _ = self._read_csv(filepath)
        except Exception as e:
            QMessageBox.warning(self, "Blank Error", f"Could not load blank:\n{e}")
            return

        self._hide_placeholder()

        if self._blank_curve is not None:
            self.plot_widget.removeItem(self._blank_curve)

        self._blank_curve = self.plot_widget.plot(
            x,
            y,
            name="Blank",
            pen=pg.mkPen(
                color=COLOUR_BLANK,
                width=1.5,
                style=Qt.PenStyle.DashLine,
            ),
        )

    def add_sample_csv(self, name: str, filepath: str):
        """
        Load a sample curve directly from a CSV file path.
        Convenience wrapper around add_sample() for data coming
        straight off the instrument (as returned by runLabMachine()).
        """
        try:
            x, y, _ = self._read_csv(filepath)
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load sample:\n{e}")
            return
        self.add_sample(name, x, y)

    def add_sample(self, name: str, x: list, y: list):
        """
        Plot a new sample curve.
        If a curve with the same name already exists it is replaced.
        """
        self._hide_placeholder()

        if name in self._sample_curves:
            self.plot_widget.removeItem(self._sample_curves[name])

        curve = self.plot_widget.plot(
            x,
            y,
            name=name,
            pen=pg.mkPen(color=self._next_colour(), width=1.5),
        )
        self._sample_curves[name] = curve

    def clear_samples(self):
        """Remove all sample curves; blank reference is kept."""
        for curve in self._sample_curves.values():
            self.plot_widget.removeItem(curve)
        self._sample_curves.clear()
        self._colour_index = 0
        if self._blank_curve is None:
            self._show_placeholder()

    def clear_blank(self):
        """Remove only the blank/reference curve; sample curves are kept."""
        if self._blank_curve is not None:
            self.plot_widget.removeItem(self._blank_curve)
            self._blank_curve = None
        if not self._sample_curves:
            self._show_placeholder()

    def clear_all(self):
        """Remove all curves including the blank."""
        self.clear_samples()
        if self._blank_curve is not None:
            self.plot_widget.removeItem(self._blank_curve)
            self._blank_curve = None
        self._show_placeholder()
