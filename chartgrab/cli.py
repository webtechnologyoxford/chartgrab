"""chartgrab command line.

  chartgrab image chart.png --pos "#22c55e" --neg "#ef4444" --y-cal "40:100,340:-50" [--x-cal "60:150,940:250" --x-step 2.5]
  chartgrab url https://example.com/chart --pos ... --neg ... [--canvas 0]
  chartgrab safari "example.com/page" --pos ... --neg ...       (macOS)
  chartgrab snapshot snap.json --pos ... --neg ...                (offline, from a saved snapshot)

Axes are taken from --y-cal/--x-cal when given, otherwise inferred from numeric labels
(DOM text around the canvas, or OCR for images when pytesseract is installed).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

from .axis import LinearAxis
from .bars import ColorClass, parse_color
from .digitize import auto_axes, digitize_bars
from .snapshot import Snapshot


def _classes(a) -> list:
    out = []
    if a.pos:
        out.append(ColorClass("positive", parse_color(a.pos), +1, a.tolerance))
    if a.neg:
        out.append(ColorClass("negative", parse_color(a.neg), -1, a.tolerance))
    if not out:
        sys.exit("give at least one of --pos / --neg bar colours")
    return out


def _run(rgba, texts, a, label: str) -> list:
    classes = _classes(a)
    y_axis = LinearAxis.parse(a.y_cal) if a.y_cal else None
    x_axis = LinearAxis.parse(a.x_cal) if a.x_cal else None
    if y_axis is None or (x_axis is None and not a.no_x):
        ay, ax = auto_axes(rgba, texts, classes)
        y_axis = y_axis or ay
        x_axis = x_axis or (None if a.no_x else ax)
    if y_axis is None:
        sys.exit(f"{label}: could not calibrate the y axis; pass --y-cal 'pixel:value,pixel:value'")
    rows = digitize_bars(rgba, classes, y_axis, x_axis, a.x_step)
    return [dict(source=label, **r.to_dict()) for r in rows]


def _emit(rows, a):
    if a.format == "json":
        json.dump(rows, sys.stdout, indent=1)
        print()
    else:
        w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()) if rows else ["source"])
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    p = argparse.ArgumentParser(prog="chartgrab", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["image", "url", "safari", "snapshot"])
    p.add_argument("target")
    p.add_argument("--pos", help="colour of positive bars, e.g. #22c55e")
    p.add_argument("--neg", help="colour of negative bars, e.g. #ef4444")
    p.add_argument("--tolerance", type=int, default=40)
    p.add_argument("--y-cal")
    p.add_argument("--x-cal")
    p.add_argument("--x-step", type=float)
    p.add_argument("--no-x", action="store_true", help="do not map bars to x labels")
    p.add_argument("--canvas", type=int, help="only this canvas index")
    p.add_argument("--save-snapshot", help="also write the raw snapshot JSON here")
    p.add_argument("--format", choices=["csv", "json"], default="csv")
    a = p.parse_args(argv)

    rows = []
    if a.mode == "image":
        from .image import load_image, ocr_texts
        rgba = load_image(a.target)
        rows = _run(rgba, [] if a.y_cal else ocr_texts(rgba), a, a.target)
    else:
        if a.mode == "url":
            from .browser.playwright_runner import capture_url
            data = capture_url(a.target)
        elif a.mode == "safari":
            from .browser.safari import capture_safari
            data = capture_safari(a.target)
        else:
            data = json.loads(open(a.target).read())
        if a.save_snapshot:
            with open(a.save_snapshot, "w") as f:
                json.dump(data, f)
        snap = Snapshot.from_dict(data)
        for c in snap.canvases:
            if c.rgba is None or (a.canvas is not None and c.index != a.canvas):
                continue
            label = f"canvas{c.index}" + (f":{c.title}" if c.title else "")
            try:
                rows += _run(c.rgba, c.texts, a, label)
            except SystemExit as e:
                print(f"skip {label}: {e}", file=sys.stderr)
    _emit(rows, a)


if __name__ == "__main__":
    main()
