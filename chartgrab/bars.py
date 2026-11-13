"""Detect vertical bars of given colours in an RGBA image."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


def parse_color(spec: str) -> Tuple[int, int, int]:
    s = spec.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"colour must be #rgb or #rrggbb, got {spec!r}")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


@dataclass
class ColorClass:
    name: str
    rgb: Tuple[int, int, int]
    sign: int = 1            # +1 bars grow up from the baseline, -1 grow down
    tolerance: int = 40      # max Euclidean RGB distance

    def mask(self, rgba: np.ndarray) -> np.ndarray:
        diff = rgba[..., :3].astype(np.int32) - np.array(self.rgb, dtype=np.int32)
        dist2 = (diff * diff).sum(axis=-1)
        return (dist2 <= self.tolerance ** 2) & (rgba[..., 3] > 0)


@dataclass
class Bar:
    color: str
    sign: int
    x0: int
    x1: int          # inclusive
    top: int
    bottom: int      # inclusive

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1


def find_bars(rgba: np.ndarray, classes: List[ColorClass], min_height: int = 2,
              min_width: int = 2, max_width: Optional[int] = None,
              roi: Optional[Tuple[int, int, int, int]] = None) -> List[Bar]:
    """Find vertical bars: runs of adjacent columns containing enough pixels of one colour.

    roi = (x0, y0, x1, y1) restricts the search to the plot area (exclusive end). Legend
    swatches and text in the bar colour are rejected by min_width/min_height/max_width.
    """
    h, w = rgba.shape[:2]
    x_off, y_off, x_end, y_end = roi if roi else (0, 0, w, h)
    sub = rgba[y_off:y_end, x_off:x_end]
    bars: List[Bar] = []
    for cls in classes:
        m = cls.mask(sub)
        col = m.sum(axis=0)
        x = 0
        while x < col.size:
            if col[x] < min_height:
                x += 1
                continue
            start = x
            while x < col.size and col[x] >= min_height:
                x += 1
            end = x - 1
            width = end - start + 1
            if width < min_width or (max_width and width > max_width):
                continue
            # use the central 60% of columns to avoid anti-aliased edges
            c0 = start + int(width * 0.2)
            c1 = max(c0, end - int(width * 0.2))
            rows = np.where(m[:, c0:c1 + 1].any(axis=1))[0]
            if rows.size < min_height:
                continue
            bars.append(Bar(cls.name, cls.sign, start + x_off, end + x_off,
                            int(rows.min()) + y_off, int(rows.max()) + y_off))
    bars.sort(key=lambda b: b.xc)
    return bars


def estimate_baseline(bars: List[Bar]) -> Optional[float]:
    """Pixel row of the zero line: where positive bars end and negative bars start."""
    pos = [b.bottom + 0.5 for b in bars if b.sign > 0]
    neg = [b.top - 0.5 for b in bars if b.sign < 0]
    edges = pos + neg
    return float(np.median(edges)) if edges else None
