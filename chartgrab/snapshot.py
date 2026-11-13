"""Snapshot model: canvases (RGBA) and visible text produced by the in-page collector."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np

COLLECTOR_JS = (Path(__file__).parent / "collector" / "canvas_collector.js").read_text()


def collector_expression(options: Optional[dict] = None) -> str:
    """JavaScript expression that runs the collector and returns its snapshot object."""
    return "(" + COLLECTOR_JS.strip().rstrip(";") + ")(" + json.dumps(options or {}) + ")"


def decode_rle(rle: List[int], width: int, height: int) -> np.ndarray:
    """Decode [r,g,b,a,count,...] into an (height, width, 4) uint8 array."""
    arr = np.asarray(rle, dtype=np.int64).reshape(-1, 5)
    pixels = np.repeat(arr[:, :4], arr[:, 4], axis=0).astype(np.uint8)
    if pixels.shape[0] != width * height:
        raise ValueError(f"RLE length {pixels.shape[0]} != {width}x{height}")
    return pixels.reshape(height, width, 4)


@dataclass
class TextItem:
    text: str
    x: float          # canvas pixel coordinates (centre)
    y: float


@dataclass
class Canvas:
    index: int
    rgba: Optional[np.ndarray]
    css: dict
    error: Optional[str] = None
    texts: List[TextItem] = field(default_factory=list)   # texts near this canvas, in canvas px
    title: Optional[str] = None


@dataclass
class Snapshot:
    url: str
    captured_at: str
    canvases: List[Canvas]
    raw_texts: list

    @classmethod
    def from_dict(cls, data: dict, margin_css: float = 60.0) -> "Snapshot":
        canvases = []
        for c in data.get("canvases", []):
            rgba = decode_rle(c["rgba_rle"], c["width"], c["height"]) if c.get("rgba_rle") else None
            canvas = Canvas(index=c["index"], rgba=rgba, css=c["css"], error=c.get("error"))
            canvas.texts, canvas.title = _texts_for_canvas(data.get("texts", []), c, margin_css)
            canvases.append(canvas)
        return cls(url=data.get("url", ""), captured_at=data.get("captured_at", ""),
                   canvases=canvases, raw_texts=data.get("texts", []))

    @classmethod
    def load(cls, path: str | Path) -> "Snapshot":
        return cls.from_dict(json.loads(Path(path).read_text()))


def _texts_for_canvas(texts: Iterable[dict], c: dict, margin: float):
    """Texts within `margin` CSS px of the canvas, converted to canvas pixel coordinates.

    Many chart libraries draw axis labels as DOM text (SVG/HTML) around the canvas; those
    are what we use as calibration anchors. The nearest text block above the canvas is
    returned as a probable title.
    """
    css = c["css"]
    sx = c["width"] / css["width"] if css["width"] else 1.0
    sy = c["height"] / css["height"] if css["height"] else 1.0
    near, title, title_gap = [], None, 1e9
    for t in texts:
        cx, cy = t["x"] + t["width"] / 2, t["y"] + t["height"] / 2
        inside_x = css["x"] - margin <= cx <= css["x"] + css["width"] + margin
        inside_y = css["y"] - margin <= cy <= css["y"] + css["height"] + margin
        if inside_x and inside_y:
            near.append(TextItem(t["text"], (cx - css["x"]) * sx, (cy - css["y"]) * sy))
        gap = css["y"] - (t["y"] + t["height"])
        if 0 <= gap < 3 * margin and inside_x and gap < title_gap and re.search(r"[A-Za-z]{3}", t["text"]):
            title, title_gap = t["text"], gap
    return near, title
