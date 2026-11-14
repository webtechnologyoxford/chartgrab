# chartgrab — Usage guide

[← Project overview](../README.md)

chartgrab is a local extraction and measurement library for vertical bar charts. It reads Canvas pixels or image files, calibrates linear axes, and exports numerical observations. It does not require a cloud vision model or a vendor data API.

## Installation

Python 3.9 or later is required. Install from a local checkout:

```bash
git clone https://github.com/webtechnologyoxford/chartgrab.git
cd chartgrab
python -m pip install -e .
```

The core uses NumPy and Pillow. Optional dependencies:

```bash
# Browser capture
python -m pip install -e ".[browser]"
python -m playwright install chromium

# Image OCR; install the Tesseract executable separately
python -m pip install -e ".[ocr]"
```

## Capture modes

### Existing Safari tab

On macOS, enable Safari's developer features and **Develop → Allow JavaScript from Apple Events**. Open the intended page and supply a URL substring that identifies its tab unambiguously.

```bash
chartgrab safari "example.com/dashboard" \
  --pos "#22c55e" --neg "#ef4444" \
  --save-snapshot snap.json --format json
```

The collector reads eligible 2D Canvas pixels and visible DOM text. It does not click, type, scroll, navigate, inspect hidden application state or intercept network requests. The Safari adapter uses the existing browser session.

For multiple or stacked canvases, inspect the snapshot and select the intended layer with `--canvas N`. Automatic layer composition is not implemented.

### Fresh browser page

```bash
chartgrab url https://example.com/dashboard \
  --pos "#22c55e" --neg "#ef4444" --format json
```

This starts a fresh Chromium browser through Playwright. It does not inherit your normal browser login. The Python `capture_url` helper also accepts a caller-supplied Playwright storage state; keep authentication files private. The runner loads the page normally and waits a fixed interval by default—it does not verify chart freshness.

Try the bundled synthetic demo:

```bash
chartgrab url "file://$PWD/examples/demo_chart.html" \
  --pos "#22c55e" --neg "#ef4444" --x-step 5 --format json
```

The demo has known values and HTML axis labels. Its horizontal step of 5 is known from the demo's construction.

### Existing Chrome tab

Use the Python CDP helper with an already-configured local Chrome debugging endpoint. Do not expose that endpoint publicly.

```python
from chartgrab import Snapshot, ColorClass, parse_color, auto_axes, digitize_bars
from chartgrab.browser.playwright_runner import capture_cdp

snap = Snapshot.from_dict(capture_cdp("http://localhost:9222", "dashboard"))
classes = [
    ColorClass("positive", parse_color("#22c55e"), +1),
    ColorClass("negative", parse_color("#ef4444"), -1),
]
for canvas in snap.canvases:
    if canvas.rgba is None:
        continue
    y_axis, x_axis = auto_axes(canvas.rgba, canvas.texts, classes)
    if y_axis is None:
        continue
    rows = digitize_bars(canvas.rgba, classes, y_axis, x_axis)
    print(canvas.title, [(r.x_label, r.value, r.error) for r in rows])
```

### Image file

```bash
chartgrab image chart.png --pos "#22c55e" --neg "#ef4444" \
  --y-cal "40:100M,340:-50M" --x-cal "60:150,940:250" --format json
```

Calibration pairs are `pixel coordinate:numeric value`. These coordinates and colours are examples, not defaults suitable for every chart. Image mode can use optional Tesseract OCR when manual y calibration is not supplied.

### Saved snapshot

```bash
chartgrab snapshot snap.json \
  --pos "#22c55e" --neg "#ef4444" --format json
```

Snapshots retain sampled RGBA pixels, visible text coordinates, page URL/title, collection time, canvas dimensions and device-pixel ratio. They can be reprocessed without contacting the page again, including with different colour-classification settings.

## Calibration and limits

Numeric anchors map pixels to linear axis values. They can come from nearby DOM text, explicit calibration or the separate image/OCR workflow. Supported notation includes `$212.5`, `50M`, `(3.2K)` and `1.5B`.

**Labels painted inside Canvas are not DOM text.** Browser and snapshot CLI modes do not automatically OCR those pixels. Supply `--x-cal` and `--y-cal` in canvas backing-pixel coordinates, or use a separate image/OCR workflow. No site-specific glyph templates are included.

The current release supports colour-separated vertical bars and linear numeric axes. Line charts, horizontal bars, logarithmic axes and general stacked/grouped charts are not implemented as complete chart types. Dense bars, overlays, clipping, transparency and theme changes require checking on the target chart.

Only rendered information can be measured. Off-range or undetected bars must not be interpreted as zero. Cross-origin-tainted canvases and canvases without a 2D context are reported as errors, not bypassed.

## Output and measurement

CSV is the default; use `--format json` for JSON. Records contain the source, estimated horizontal label, signed value, error estimate, colour class and pixel geometry.

`x_label` is an axis-derived numerical position, not a verified option strike or persistent node identity. It can be `None` when the horizontal axis is unavailable. `--x-step 2.5` rounds positions to a caller-specified grid; it does not prove that grid is correct. Leave it unset when the correspondence is unproven. Category axes need a separate mapping.

`--pos` and `--neg` assign signs to colour classes. Confirm their meaning and the zero baseline on the target chart.

The value-error estimate is **two pixel units of the fitted y scale plus its calibration residual**. It is a measurement allowance, not a statistical confidence interval or a guarantee covering incorrect labels, segmentation, missing bars, x-position errors or supplier calculations.

## Continuous monitoring

Scheduling, scope validation, freshness checks, cross-frame identity and change detection belong to the integrating application. This release supplies individual observations and saved inputs, not a complete monitoring or trading system.

For comparisons over time, preserve the asset, series, units, date/expiry, filters and observed range. Recalibrate when scales or layouts change. A canvas index or nearby title is not sufficient as a persistent financial identity.

Keep collection time separate from chart-selected time and provider update time. A page clock may advance while the chart remains on an older selection. Sequential canvas reads are not guaranteed to be an atomic market snapshot.

Regional analysis should compare fixed numerical intervals with appropriate boundary and measurement uncertainty. Exact per-strike changes additionally require proven correspondence between observations. Do not confuse movement of the market price with movement of the measured structure.

## Validation

The repository includes [known-value synthetic tests](../tests/test_digitize.py) and a [Chromium integration test](../tests/test_browser.py) using the bundled demo.

```bash
python -m pip install -e ".[dev]"
python -m playwright install chromium
python -m pytest tests/test_digitize.py tests/test_browser.py
```

The browser test can be skipped if its dependencies are unavailable. These tests do not establish general accuracy across arbitrary live dashboards. Validate both measurements and missing/merged bars against permitted same-source references. A different vendor's numbers are a separate comparison, not ground truth for the image.

## Responsible use

Use only pages and data you are authorised to access and process. Respect source terms and data licences. chartgrab does not bypass login, paywalls or browser security. Keep snapshots private when they contain licensed data, account information or sensitive URLs.

The [MIT licence](../LICENSE) covers this project's code, not the data it reads. No vendor-specific selectors, templates, market data, strategy rules or trading execution are included.

## 中文说明

**chartgrab 将网页 Canvas 柱状图转换为结构化数值。** 它读取浏览器画布或图像，按颜色识别柱体、标定坐标轴，输出横轴位置、正负数值和误差估计。

支持已有 Safari 标签页、通过 Python/CDP 连接的 Chrome、Playwright 新页面、图片文件，以及快照离线重读。核心在本地运行，不依赖云端视觉模型。

当前版本面向竖向柱图和线性坐标轴。Canvas 内绘制的刻度不能由 DOM 直接读取，需要手动标定或另行使用图片/OCR流程。`--x-step` 是使用者指定的步长取整，不证明唯一行权价；误差估计也不覆盖所有识别或数据源错误。

公开版提供采集与测量核心，不包含特定网站适配、跨帧节点跟踪、行情新鲜度校验或交易策略。连续分析需由上层应用核对时间、范围和身份，不能把缺失数据当作零。
