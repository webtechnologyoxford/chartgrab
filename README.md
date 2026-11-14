# chartgrab

**Turn rendered browser bar charts into reproducible numerical observations.**

Read a web page's `<canvas>` pixels and surrounding DOM text, calibrate the axes, and export a table of **horizontal position → signed bar value ± measurement error**. Works with an existing Safari tab, Chrome through CDP, a fresh Chromium browser, saved snapshots, and chart images. No vendor data API or cloud vision model is required by the extraction core.

[Why this exists](#why-this-exists) · [Current capabilities](#current-capabilities-v010) · [Quick start](#quick-start) · [Measurement and identity](#measurement-is-not-identity) · [中文说明](#中文说明)

## Why this exists

The practical problem is not simply “can an OCR tool read a chart?” It is:

> How do you turn bars on a dashboard you can view into repeatable numerical observations, when there is no suitable structured export for your workflow?

chartgrab grew out of work on financial dashboards containing positive and negative exposure-by-strike charts. The reusable part is useful beyond finance: acquiring a rendered bar chart, separating its bars, mapping pixels into numerical coordinates, and retaining the input for later inspection.

**A permitted, affordable, sufficiently complete structured API is preferable when one is available.** chartgrab addresses the remaining case: the rendered chart is accessible, but a suitable data integration is not. It does not intercept private network endpoints, inspect hidden application state, or bypass access controls. It is a measurement tool, not an alternative data licence.

Reading a total in the legend is not the same as reading every visible bar. Reading one frame is not the same as proving that a bar represents the same thing in the next frame. The distinction matters:

| Real-world difficulty | Why a simple answer is incomplete |
| --- | --- |
| Bars and tick labels may be drawn inside a canvas | There may be no per-bar DOM element or text value to select. Reading pixels does not expose the vendor's original numerical array. |
| Dense bars, small values, overlays and anti-aliasing | A reader can miss a small bar, merge neighbours, or count one fragmented bar twice. |
| Resizing and automatic axis scaling | The same pixel position or height can represent a different numerical value in another frame. |
| Changing dates, expiry selections, filters and visible ranges | Two visually similar charts may represent different datasets. A hidden bar is not a zero-valued bar. |
| Comparing values over time | Stable chart meaning, valid horizontal correspondence, observation time and measurement uncertainty are needed in addition to single-frame extraction. |

**This repository is the extraction and measurement core, not the entire monitoring or trading system that motivated it.** It does not claim to solve all of the difficulties above automatically, and it makes no “world first” or universal-accuracy claim.

## How it works

```text
Existing browser tab / fresh page / saved image
                       |
          Canvas RGBA + visible DOM text
          (or image + manual/OCR anchors)
                       |
        Colour-based bar detection + linear axes
                       |
       x position + signed value + error estimate
                       |
             CSV / JSON / Python objects

Saved browser snapshot -> offline re-digitization
```

1. **Collect in the page.** The [JavaScript collector](chartgrab/collector/canvas_collector.js) reads eligible 2D canvases using `getImageData`, retains RGBA pixels with run-length encoding, and collects nearby text coordinates. It records page URL/title, capture time, canvas dimensions and device-pixel ratio. The collector itself does not click, type, scroll, mutate the page or make network requests. The separate `url` runner opens and loads a page normally.
2. **Find bars.** [Colour classes](chartgrab/bars.py), configurable through `--pos`, `--neg` and `--tolerance`, identify candidate bars. Geometry and size checks filter candidates; endpoint measurement uses central columns to reduce edge effects. Unfamiliar layouts still need checking.
3. **Calibrate.** [Linear axes](chartgrab/axis.py) map pixel coordinates to numeric values. Anchors can come from DOM text, manual calibration, or optional image OCR. Numeric notation includes `$212.5`, `50M`, `(3.2K)` and `1.5B`. Automatic label selection and outlier rejection are heuristics, not proof that a particular chart was interpreted correctly.
4. **Measure and export.** [The digitizer](chartgrab/digitize.py) measures bar magnitude relative to its baseline, applies the configured sign, and emits numerical observations. An optional horizontal step can round estimated positions to a user-specified grid; see the identity warning below.
5. **Keep the input.** `--save-snapshot` stores the collected pixels and metadata for offline inspection and re-digitization. Unlike a colour-class map alone, the RGBA snapshot retains the original sampled colours for trying a different classification later.

## Current capabilities (v0.1.0)

| Capability | Current scope |
| --- | --- |
| Browser acquisition | macOS Safari via JXA; fresh Chromium via Playwright; existing Chrome via the Python CDP helper |
| Image acquisition | Image files with manual calibration or optional Tesseract OCR |
| Bar measurement | Colour-separated vertical bars with positive/negative values and linear numeric axes |
| Output | CSV, JSON and Python objects with numerical x position, value, error estimate and pixel geometry |
| Reproducibility | Save a browser snapshot and re-digitize it offline |
| Continuous monitoring | Scheduling, stable cross-frame identity, scope/freshness validation and change detection belong to the integrating application; they are not provided by this release |

The public package contains **no vendor-specific selectors, glyph templates, market data, strategy rules or trading execution**. Results from a private dashboard integration are not a benchmark for this generic release.

## Quick start

Install from this repository:

```bash
git clone https://github.com/webtechnologyoxford/chartgrab.git
cd chartgrab
python -m pip install -e .             # core: NumPy + Pillow

# Browser support and the bundled demo
python -m pip install -e ".[browser]"
python -m playwright install chromium
chartgrab url "file://$PWD/examples/demo_chart.html" \
  --pos "#22c55e" --neg "#ef4444" --x-step 5 --format json

# Optional image OCR; the Tesseract executable must also be installed separately
python -m pip install -e ".[ocr]"
```

The demo uses known synthetic values and HTML axis labels. Its `--x-step 5` is known from the demo's construction, not inferred proof about an external financial chart. Example colours and calibration points below are illustrative; use the actual chart's values.

### Chart image with explicit calibration

```bash
# Calibration pairs are image pixel coordinate:numeric value.
chartgrab image chart.png --pos "#22c55e" --neg "#ef4444" \
  --y-cal "40:100M,340:-50M" --x-cal "60:150,940:250" --format json
```

### Web page with accessible DOM axis labels

```bash
chartgrab url https://example.com/dashboard \
  --pos "#22c55e" --neg "#ef4444" --format json
```

`url` starts a fresh browser; it does not inherit your normal Safari or Chrome login session. Use an existing-tab method for an already-authenticated page. The Python `capture_url` helper also accepts a caller-supplied Playwright storage state; keep such files private.

### Existing Safari tab on macOS

Enable Safari's developer features and **Develop → Allow JavaScript from Apple Events**. Keep the intended page open and use a URL substring that identifies it unambiguously.

```bash
chartgrab safari "example.com/dashboard" \
  --pos "#22c55e" --neg "#ef4444" --save-snapshot snap.json --format json

# Reuse the same captured pixels without contacting the page again.
chartgrab snapshot snap.json \
  --pos "#22c55e" --neg "#ef4444" --format json
```

For stacked or multiple canvases, inspect the snapshot and use `--canvas N` to select the intended layer. Automatic multi-layer composition is not implemented. If axes cannot be read from DOM text, supply `--x-cal` and `--y-cal` in canvas backing-pixel coordinates.

### Existing Chrome tab from Python

Requires a Chrome instance already configured with an accessible local CDP endpoint. Do not expose its debugging endpoint publicly.

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

## Measurement is not identity

`x_label` is a numerical position estimated from the horizontal axis. It is **not automatically a verified category, option strike or persistent node ID**. If the x axis is unavailable, it can be `None`.

`--x-step 2.5` rounds that estimate to the nearest multiple of 2.5. It is a caller-supplied assumption, not evidence that 2.5 is the correct spacing or that no alternative mapping exists. Leave it unset when the spacing or correspondence is unproven. Category axes and irregularly spaced categories require an appropriate mapping that this release does not infer.

Likewise, `--pos` and `--neg` assign signs to colour classes. Green and red are not universal financial semantics: confirm the series and zero baseline before interpreting the output.

The current value-error estimate is **two pixel units of the fitted y scale plus its calibration residual**. It is a measurement allowance, not a statistical confidence interval, an x-position error bound, or a guarantee covering wrong labels, wrong bar segmentation, missing bars or supplier calculation errors. Inspect representative examples before relying on it.

### Building a time-series application on top

The following are integration requirements, **not features already implemented by chartgrab**:

- Preserve the chart's meaning: asset, series, unit, date/expiry, active filters and aggregation. A canvas index or nearby title alone is not a stable financial identity.
- Retain capture time separately from the chart's selected time and provider update time. Snapshot `captured_at` is a browser collection timestamp, not proof of current market data. A page clock can advance while the chart remains on an old selection.
- Recalibrate after layout or scale changes, compare only adequately observed common ranges, and treat off-screen, missing or unreadable data as missing rather than zero. Multiple canvases collected in sequence are not guaranteed to be one atomic market snapshot.
- For regional analysis, compare fixed price intervals and carry measurement/boundary uncertainty. For exact per-strike changes, establish that both observations refer to the same strike and scope. Keep price movement relative to a region separate from movement of the region itself.

An extraction tool can supply the observations for these tasks; it cannot establish those meanings merely by producing a neat table.

## Validation

The repository includes [synthetic known-value tests](tests/test_digitize.py) and a [Chromium demo integration test](tests/test_browser.py). They cover numerical parsing, calibrated bar recovery, snapshot encoding and a browser chart with DOM labels. They do **not** establish general accuracy across arbitrary live dashboards, font changes, dense-bar layouts or continuous financial-node tracking.

```bash
python -m pip install -e ".[dev]"
python -m playwright install chromium
python -m pytest tests/test_digitize.py tests/test_browser.py
```

The browser test can be skipped if Playwright or its browser is unavailable; a skipped browser test is not browser validation. For a new site, check both recovered values and missing/merged bars against permitted same-source references. Agreement with a different data vendor is a separate comparison, not proof that the original chart was read correctly.

## Limits

- Vertical, colour-separable bars and linear numeric calibration only. Line charts, horizontal bars, logarithmic axes and general stacked/grouped charts are not supported as complete chart types.
- Dense neighbouring bars, overlays, clipping, transparency and colour/theme changes may break detection or affect its error estimate. Canvas access alone does not solve these interpretation problems.
- Labels painted inside a canvas are not DOM text. Browser/snapshot CLI modes do not automatically OCR those canvas pixels: use explicit calibration or a separate image/OCR workflow. No dashboard-specific glyph recognizer is bundled.
- A fresh `url` capture waits a fixed interval by default; it does not verify that every chart has finished loading or refreshed. Applications must check readiness and freshness themselves.
- Cross-origin-tainted canvases and canvases without a 2D context are reported as errors; their pixels cannot be read by this collector. Ordinary screenshots remain a separate supported input, not a way to claim missing data is present.
- Only rendered data can be measured. Hidden/off-range bars, complete market coverage and supplier-native precision cannot be recovered from pixels that do not contain them.

## Responsible use

Use chartgrab only on pages and data you are authorised to access and process. It does not bypass logins, paywalls, browser security or rate limits. Access to a page does not itself grant permission for automated extraction, retention or redistribution: check the site's terms and your data licence.

Keep captured snapshots private when they contain licensed data, account-related text or sensitive URLs. The MIT licence applies to this project's code, not to a vendor's data. No vendor-specific selectors, templates or data are shipped here.

## 中文说明

### 解决的不是“看见柱子”，而是把网页图表变成可复算的数值

chartgrab 源于实际金融仪表盘取数工作，面向这样的场景：**用户能正常查看网页图表，但没有适合当前工作流的结构化导出方式，希望在本地批量取得数值，而不是逐柱悬停或每轮调用云端视觉模型。**

“调用API”是有合适权限、成本和字段覆盖时应优先考虑的办法；但它不能代替对实际可用性的核查。“浏览器抓包”则是另一条数据接入路线，并不是本项目采用的方法。chartgrab 读取已经渲染的Canvas像素及页面公开文字，不抓取私有网络接口，也不绕过访问限制。

难点并不只是认出一个数字：密集柱可能粘连或漏读，坐标轴会自动缩放，多面板的日期、到期范围和筛选状态可能不同，同一个屏幕位置下一帧也可能代表不同价格。**读到图例总量、读出一张图的各根柱、证明前后是同一个金融节点，是三项不同的能力。**

### 公开版已经提供什么

当前 v0.1.0 提供浏览器Canvas采集、页面文字坐标、颜色分柱、线性轴标定、带误差估计的数值输出，以及保存快照后的离线重读。入口包括已有Safari标签页、Python/CDP连接的Chrome、Playwright新页面和图片文件；核心使用NumPy与Pillow，不依赖云端视觉模型。

这是从实际工程中抽出的**通用采集与测量核心**，不是完整QTS1/QTS2系统。公开包没有供应商专用字形模板、有效过滤状态校验、逐节点跨帧跟踪、金融数据新鲜度判断、策略闸门或自动交易能力。不能把私有系统的全部运行成果算作这个公开版本已经具备的功能。

### 使用时需要理解的边界

`x_label` 是根据坐标轴换算的位置；`--x-step` 只是使用者指定的步长取整，不是唯一行权价证明。`--pos/--neg` 的颜色与正负含义也需要按目标图核对。金额 `error` 是像素与拟合残差形成的估计，不覆盖所有识别、分柱或供应商计算错误。

轴刻度如果画在Canvas内部，DOM无法读到；浏览器与快照命令目前不会自动对它们做OCR，需要显式标定或另外走图片/OCR流程。字体、颜色和布局变化都需要重新验证。

若在上层做连续观察，应保存实际业务范围、图表时间和覆盖区间：比较同一价格区间的变化，不能把缩放当增长、把看不到当零、把页面采集时间当行情更新时间。精确逐strike变化还需额外确认前后节点归属；区域分析可以按固定价格区间比较，但也须处理边界歧义和漏读。

项目的价值是把**浏览器采集 → 可保存的原始像素 → 坐标标定 → 批量测量 → 结构化输出**组合成可编程、可复查的工具，而不是宣称发明了图表数字化，或未经证实地宣传“全球首个”“适用于所有网站”。现有测试针对已知值合成图与浏览器示例，不代表所有真实金融图表都已验收。

请遵守网站条款和数据许可；代码开源不意味着可以公开传播采集到的商业数据。

## License

[MIT](LICENSE)
