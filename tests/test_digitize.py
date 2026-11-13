"""Synthetic charts with known values: the digitizer must recover them within its error bar."""
import numpy as np
import pytest
from PIL import Image, ImageDraw

from chartgrab.axis import LinearAxis, parse_number
from chartgrab.bars import ColorClass, parse_color
from chartgrab.digitize import digitize_bars
from chartgrab.snapshot import TextItem, decode_rle

GREEN, RED = "#22c55e", "#ef4444"
# chart geometry: zero line at y=300, 1 pixel = 0.5e6, strikes 150..250 step 2.5 at x = 60 + 20*i
ZERO_Y, UNITS_PER_PX = 300, 0.5e6
VALUES = {150 + 2.5 * i: v for i, v in enumerate(
    [12e6, -8e6, 40e6, 0, 95e6, -30e6, 5e6, 61.5e6, -2e6, 18e6])}


def strike_x(k):
    return 60 + 20 * (k - 150) / 2.5


def make_chart():
    img = Image.new("RGBA", (400, 500), (17, 24, 39, 255))
    d = ImageDraw.Draw(img)
    for y in range(100, 500, 50):               # grid lines (must be ignored)
        d.line([(40, y), (390, y)], fill=(55, 65, 81, 255))
    for k, v in VALUES.items():
        if v == 0:
            continue
        h = round(abs(v) / UNITS_PER_PX)
        x = strike_x(k)
        if v > 0:
            d.rectangle([x - 6, ZERO_Y - h, x + 6, ZERO_Y - 1], fill=parse_color(GREEN) + (255,))
        else:
            d.rectangle([x - 6, ZERO_Y, x + 6, ZERO_Y + h - 1], fill=parse_color(RED) + (255,))
    d.rectangle([300, 20, 310, 30], fill=parse_color(GREEN) + (255,))   # legend swatch
    return np.asarray(img)


CLASSES = [ColorClass("positive", parse_color(GREEN), +1), ColorClass("negative", parse_color(RED), -1)]


def test_recovers_values_with_manual_calibration():
    rgba = make_chart()
    y = LinearAxis.fit([(ZERO_Y, 0), (ZERO_Y - 100, 100 * UNITS_PER_PX)])
    x = LinearAxis.fit([(strike_x(150), 150), (strike_x(172.5), 172.5)])
    rows = digitize_bars(rgba, CLASSES, y, x, x_step=2.5, roi=(40, 80, 390, 480))
    got = {r.x_label: r for r in rows}
    expected = {k: v for k, v in VALUES.items() if v != 0}
    assert set(got) == set(expected)
    for k, v in expected.items():
        assert abs(got[k].value - v) <= got[k].error, (k, got[k].value, v)


def test_auto_axis_from_text_labels():
    from chartgrab.axis import anchors_from_texts
    texts = [TextItem("50M", 20, ZERO_Y - 100), TextItem("0", 20, ZERO_Y), TextItem("-25M", 20, ZERO_Y + 50),
             TextItem("$150", strike_x(150), 470), TextItem("$170", strike_x(170), 470),
             TextItem("213.14", 395, 10)]          # stray price text must not break the fit
    y = anchors_from_texts(texts, "y", (40, 80, 390, 460))
    x = anchors_from_texts(texts, "x", (40, 80, 390, 460))
    assert abs(y.value(ZERO_Y - 40) - 20e6) < 1e3
    assert abs(x.value(strike_x(165)) - 165) < 1e-6


@pytest.mark.parametrize("text,val", [("1.5B", 1.5e9), ("-500 M", -5e8), ("$212.5", 212.5),
                                      ("(3.2K)", -3200), ("−1,200", -1200), ("15%", 15), ("abc", None)])
def test_parse_number(text, val):
    assert parse_number(text) == val


def test_rle_roundtrip():
    rgba = make_chart()[:10, :10]
    flat = rgba.reshape(-1, 4)
    rle, prev, n = [], None, 0
    for px in map(tuple, flat):
        if px == prev:
            n += 1
            continue
        if prev is not None:
            rle += list(prev) + [n]
        prev, n = px, 1
    rle += list(prev) + [n]
    assert (decode_rle(rle, 10, 10) == rgba).all()
