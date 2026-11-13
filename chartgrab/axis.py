"""Axis calibration: map pixel coordinates to data values from >= 2 anchors."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

_SUFFIX = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
_NUM = re.compile(r"^\(?\s*([-+−–]?)\s*\$?\s*([0-9]+(?:[.,][0-9]+)*)\s*([KMBTkmbt]?)\s*%?\s*\)?$")


def parse_number(text: str) -> Optional[float]:
    """Parse chart tick text such as '1.5B', '-500 M', '$212.5', '(3.2K)', '−1,200', '15%'."""
    t = text.strip().replace(" ", " ")
    m = _NUM.match(t)
    if not m:
        return None
    sign, digits, suffix = m.groups()
    digits = digits.replace(",", "")
    try:
        value = float(digits) * _SUFFIX[suffix.upper()]
    except ValueError:
        return None
    negative = bool(sign) and sign in "-−–"
    if negative or (t.startswith("(") and t.endswith(")")):
        value = -value
    return value


@dataclass
class LinearAxis:
    """value = slope * pixel + intercept, with RMS residual of the anchor fit (value units)."""
    slope: float
    intercept: float
    residual: float
    anchors: List[Tuple[float, float]]

    def value(self, pixel: float) -> float:
        return self.slope * pixel + self.intercept

    def pixel(self, value: float) -> float:
        return (value - self.intercept) / self.slope

    @property
    def units_per_pixel(self) -> float:
        return abs(self.slope)

    @classmethod
    def fit(cls, anchors: Sequence[Tuple[float, float]]) -> "LinearAxis":
        pts = sorted({(float(p), float(v)) for p, v in anchors})
        if len({p for p, _ in pts}) < 2:
            raise ValueError("need at least two anchors at different pixel positions")
        px = np.array([p for p, _ in pts])
        val = np.array([v for _, v in pts])
        slope, intercept = np.polyfit(px, val, 1)
        if slope == 0:
            raise ValueError("degenerate axis (zero slope)")
        res = float(np.sqrt(np.mean((slope * px + intercept - val) ** 2)))
        return cls(float(slope), float(intercept), res, list(pts))

    @classmethod
    def parse(cls, spec: str) -> "LinearAxis":
        """Parse a manual calibration like '120:100,420:-50' (pixel:value pairs)."""
        pairs = []
        for part in spec.split(","):
            p, v = part.split(":")
            pairs.append((float(p), parse_number(v) if parse_number(v) is not None else float(v)))
        return cls.fit(pairs)


def anchors_from_texts(texts: Iterable, axis: str, plot_box: Tuple[int, int, int, int],
                       min_anchors: int = 2) -> Optional[LinearAxis]:
    """Build an axis from numeric labels placed beside (y) or below (x) the plot box.

    plot_box = (x0, y0, x1, y1) in canvas pixels. For the y axis we take numeric labels
    whose x is left or right of the plot and whose y lies within the plot's vertical span;
    for the x axis, labels below the plot within its horizontal span. Outliers that do not
    fit a straight line are dropped (robust to stray numbers such as a price legend).
    """
    x0, y0, x1, y1 = plot_box
    cand = []
    for t in texts:
        v = parse_number(t.text)
        if v is None:
            continue
        if axis == "y" and (t.x < x0 or t.x > x1) and y0 - 5 <= t.y <= y1 + 5:
            cand.append((t.y, v))
        elif axis == "x" and t.y > y1 - 2 and x0 - 5 <= t.x <= x1 + 5:
            cand.append((t.x, v))
    if len(cand) < min_anchors:
        return None
    best = LinearAxis.fit(cand)
    while len(best.anchors) > min_anchors and best.residual > 0.02 * _span(best):
        worst = max(best.anchors, key=lambda a: abs(best.value(a[0]) - a[1]))
        best = LinearAxis.fit([a for a in best.anchors if a != worst])
    return best


def _span(axis: LinearAxis) -> float:
    vals = [v for _, v in axis.anchors]
    return (max(vals) - min(vals)) or 1.0
