# chartgrab

Read the numbers behind bar charts — straight from a web page's `<canvas>` pixels, or from a chart screenshot.

Many financial dashboards (options gamma/delta exposure by strike, volume profiles, flow histograms) draw their bars on an HTML `<canvas>`. The values exist only as pixels. **chartgrab** reads those pixels in place, finds the bars by colour, calibrates the axes from the tick labels, and gives you a table: `x label (e.g. strike) → value ± error`.

```
source,x_label,value,error,color
canvas0:Net Gamma Exposure By Strike - DEMO,185.0,60000000.0,1290322.6,positive
canvas0:Net Gamma Exposure By Strike - DEMO,190.0,-39354838.7,1290322.6,negative
```

## How it works

1. **Collect (read-only, in the page).** A small JavaScript collector (`chartgrab/collector/canvas_collector.js`) runs inside the page: for every visible 2D canvas it calls `getImageData` and returns the RGBA pixels (run-length encoded), plus every visible text node with its coordinates (titles, tick labels). It never clicks, types, scrolls, navigates or makes network requests.
2. **Find bars.** Pixels are classified by colour (`--pos` / `--neg` with a tolerance). Adjacent columns of one colour form a bar; its top/bottom rows are measured on the bar's central columns to avoid anti-aliasing. Grid lines, legend swatches and text are rejected by size.
3. **Calibrate axes.** Numeric labels beside the plot (`50M`, `-25M`, `$212.5`, `(3.2K)`, `1.5B`) become `pixel → value` anchors; a least-squares line is fitted and outliers (a stray price legend, say) are dropped. You can also give the calibration by hand, or use OCR for images.
4. **Measure.** Each bar's value is the axis distance between the zero line and its far end, so a constant calibration offset cancels out. Every value carries an uncertainty of ±1 px at each end plus the calibration residual. Bar centres map to x labels (e.g. option strikes), optionally snapped to a step (`--x-step 2.5`).

## Install

```bash
pip install -e .            # core: numpy + Pillow
pip install -e ".[browser]" # Playwright capture (then: playwright install chromium)
pip install -e ".[ocr]"     # optional Tesseract OCR for screenshots
```

## Use

```bash
# A chart image / screenshot, manual calibration (pixel:value pairs)
chartgrab image chart.png --pos "#22c55e" --neg "#ef4444" \
    --y-cal "40:100M,340:-50M" --x-cal "60:150,940:250" --x-step 2.5

# A web page in a fresh headless browser (axes from the page's tick labels)
chartgrab url https://example.com/dashboard --pos "#22c55e" --neg "#ef4444" --format json

# A tab already open in Safari on macOS (Develop > Allow JavaScript from Apple Events)
chartgrab safari "example.com/dashboard" --pos "#22c55e" --neg "#ef4444" --save-snapshot snap.json

# Re-digitize a saved snapshot offline
chartgrab snapshot snap.json --pos "#22c55e" --neg "#ef4444"
```

Python:

```python
from chartgrab import Snapshot, ColorClass, parse_color, auto_axes, digitize_bars
from chartgrab.browser.playwright_runner import capture_cdp   # attach to your running Chrome

snap = Snapshot.from_dict(capture_cdp("http://localhost:9222", "dashboard"))
classes = [ColorClass("pos", parse_color("#22c55e"), +1), ColorClass("neg", parse_color("#ef4444"), -1)]
for c in snap.canvases:
    y, x = auto_axes(c.rgba, c.texts, classes)
    if y:
        print(c.title, [(r.x_label, r.value, r.error) for r in digitize_bars(c.rgba, classes, y, x, x_step=2.5)])
```

Try it on the bundled demo: `chartgrab url "file://$PWD/examples/demo_chart.html" --pos "#22c55e" --neg "#ef4444" --x-step 5`.

## Limits

- Vertical bar charts only (v0.1). Line charts and horizontal bars are not handled yet.
- Only what is drawn: bars outside the visible range or hidden behind a zoom do not exist for chartgrab.
- Labels drawn *inside* the canvas are invisible to the DOM collector — use `--y-cal/--x-cal` or OCR.
- Cross-origin ("tainted") canvases and WebGL canvases cannot be read; they are reported with an error.
- Values are pixel measurements of a picture: always use the reported `error`.

## Responsible use

chartgrab reads what your own browser is already displaying to you. It does not bypass logins, paywalls or rate limits. Many data vendors' terms of service restrict automated extraction, storage or redistribution of their data — **check the terms of the site you use it on**, and do not publish or resell data you are not licensed to share. This project ships no vendor-specific selectors, templates or data.

## 中文说明

chartgrab 用来读取网页 `<canvas>` 柱状图（或图表截图）背后的数值。浏览器里的只读脚本读取画布像素和页面上的刻度文字；按颜色找出柱子，用刻度数字校准坐标轴，输出"横轴标签（如行权价）→ 数值 ± 误差"。支持无头浏览器（Playwright）、已打开的 Chrome（CDP）、macOS Safari 已打开的标签页，以及图片文件（手动校准或可选 OCR）。

请只在你有权查看的数据上使用，并遵守数据网站的服务条款，不要公开传播或转售未经授权的数据。本项目不包含任何特定网站的选择器、模板或数据。

## License

MIT
