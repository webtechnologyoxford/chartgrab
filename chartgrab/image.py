"""Load chart screenshots / images, and optional OCR of tick labels."""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from .snapshot import TextItem


def load_image(path: str) -> np.ndarray:
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGBA"))


def ocr_texts(rgba: np.ndarray, region: Optional[Tuple[int, int, int, int]] = None,
              scale: int = 3) -> List[TextItem]:
    """OCR numeric tick labels with Tesseract (optional dependency: pytesseract + tesseract).

    Returns [] if OCR is unavailable, so callers can fall back to manual calibration.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return []
    x0, y0, x1, y1 = region or (0, 0, rgba.shape[1], rgba.shape[0])
    img = Image.fromarray(rgba[y0:y1, x0:x1]).convert("L")
    img = img.resize((img.width * scale, img.height * scale))
    data = pytesseract.image_to_data(
        img, config="--psm 11 -c tessedit_char_whitelist=0123456789.,-$KMB%()",
        output_type=pytesseract.Output.DICT)
    out = []
    for text, left, top, w, h, conf in zip(data["text"], data["left"], data["top"],
                                           data["width"], data["height"], data["conf"]):
        if text.strip() and float(conf) > 50:
            out.append(TextItem(text.strip(), x0 + (left + w / 2) / scale, y0 + (top + h / 2) / scale))
    return out
