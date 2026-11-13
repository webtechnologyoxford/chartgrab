"""End-to-end: RGBA image (+ optional text anchors) -> list of bar values."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .axis import LinearAxis, anchors_from_texts
from .bars import Bar, ColorClass, estimate_baseline, find_bars


@dataclass
class BarValue:
    x_label: Optional[float]   # e.g. strike price, from the x axis (None if uncalibrated)
    value: float               # signed data value
    error: float               # +/- half-width of uncertainty (value units)
    color: str
    x_pixel: float
    top: int
    bottom: int

    def to_dict(self) -> dict:
        return asdict(self)


def digitize_bars(rgba: np.ndarray, classes: Sequence[ColorClass], y_axis: LinearAxis,
                  x_axis: Optional[LinearAxis] = None, x_step: Optional[float] = None,
                  roi: Optional[Tuple[int, int, int, int]] = None, **find_kwargs) -> List[BarValue]:
    """Measure every bar against a calibrated y axis.

    The bar's value is the axis distance between its baseline end and its far end, so a
    small offset in the y calibration cancels out. Uncertainty = 1 pixel at each end plus
    the calibration residual. If an x axis is given, bar centres are mapped to labels and
    optionally snapped to the nearest multiple of x_step (e.g. 2.5 for option strikes).
    """
    bars = find_bars(rgba, list(classes), roi=roi, **find_kwargs)
    baseline = estimate_baseline(bars)
    out: List[BarValue] = []
    for b in bars:
        far = b.top - 0.5 if b.sign > 0 else b.bottom + 0.5
        near = baseline if baseline is not None else (b.bottom + 0.5 if b.sign > 0 else b.top - 0.5)
        magnitude = abs(y_axis.value(far) - y_axis.value(near))
        err = 2 * y_axis.units_per_pixel + y_axis.residual
        label = None
        if x_axis is not None:
            label = x_axis.value(b.xc)
            if x_step:
                label = round(label / x_step) * x_step
        out.append(BarValue(label, b.sign * magnitude, err, b.color, b.xc, b.top, b.bottom))
    return out


def plot_box_from_bars(bars: List[Bar], pad: int = 4) -> Optional[Tuple[int, int, int, int]]:
    if not bars:
        return None
    return (min(b.x0 for b in bars) - pad, min(b.top for b in bars) - pad,
            max(b.x1 for b in bars) + pad, max(b.bottom for b in bars) + pad)


def auto_axes(rgba: np.ndarray, texts, classes: Sequence[ColorClass], **find_kwargs):
    """Infer y/x axes from numeric text labels around the bars (DOM text or OCR output)."""
    bars = find_bars(rgba, list(classes), **find_kwargs)
    box = plot_box_from_bars(bars)
    if box is None:
        return None, None
    return anchors_from_texts(texts, "y", box), anchors_from_texts(texts, "x", box)
