"""End-to-end in a real browser: canvas bar chart with HTML axis labels."""
from pathlib import Path

import pytest

from chartgrab.axis import LinearAxis  # noqa: F401
from chartgrab.bars import ColorClass, parse_color
from chartgrab.digitize import auto_axes, digitize_bars
from chartgrab.snapshot import Snapshot, collector_expression

DEMO = Path(__file__).resolve().parents[1] / "examples" / "demo_chart.html"


def test_collect_and_digitize_demo_page():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # browser not installed
            pytest.skip(str(e))
        page = browser.new_page(viewport={"width": 900, "height": 600}, device_scale_factor=2)
        page.goto(DEMO.as_uri())
        page.wait_for_function("window.__demoReady === true")
        expected = page.evaluate("window.__demoValues")
        data = page.evaluate(collector_expression())
        browser.close()
    snap = Snapshot.from_dict(data)
    assert len(snap.canvases) == 1 and snap.canvases[0].title == "Net Gamma Exposure By Strike - DEMO"
    c = snap.canvases[0]
    classes = [ColorClass("positive", parse_color("#22c55e"), +1), ColorClass("negative", parse_color("#ef4444"), -1)]
    y, x = auto_axes(c.rgba, c.texts, classes)
    assert y is not None and x is not None
    rows = {r.x_label: r for r in digitize_bars(c.rgba, classes, y, x, x_step=5)}
    for strike, value in expected.items():
        k = float(strike)
        if value == 0:
            continue
        assert k in rows, k
        assert abs(rows[k].value - value) <= rows[k].error, (k, rows[k].value, value)
