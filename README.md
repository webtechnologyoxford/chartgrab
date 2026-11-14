# chartgrab

**Beyond screenshot recognition. Turn web charts into a programmable data source.**

Extract vertical bar-chart data directly from browser Canvas pixels and visible page text. Recover horizontal positions, signed values and measurement-error estimates, then export **CSV or JSON**—locally, without per-bar hovering, a vendor data API or cloud vision calls.

## The breakthrough

Screenshot/OCR and standalone OpenCV experiments had not completed the original project's dashboard-to-data workflow. **The breakthrough was changing the acquisition layer—not merely switching recognition algorithms:** read the chart where it is rendered, then calibrate and measure it in its own pixel coordinates.

chartgrab packages that approach into a reusable **browser → measurement → structured data** tool, with saved inputs for offline reprocessing.

**关键突破：从“识别整屏截图”转向“直接读取图表画布”。**

此前，截图识别、OCR 和 OpenCV 局部试验未能打通项目的取数链路。chartgrab 将浏览器原生采集、坐标标定、批量测量与结构化输出整合为可调用工具，让网页图表真正成为可计算的数据源。

支持 Safari、Chrome、Python 及图表图片；本地处理，无需逐柱悬停或云端视觉模型，原始快照可保存、复查和离线重算。

```text
Browser Canvas + visible text → Calibrated bar measurements → CSV / JSON
                  ↓
             Saved snapshot → Offline reprocessing
```

## Features

- **Browser-native capture** — read multiple 2D canvases and visible text from existing Safari or Chrome tabs, or fresh pages via Playwright.
- **Batch measurement** — recover numerical positions and positive/negative bar values through linear-axis calibration, with measurement-error estimates.
- **Developer integration** — command-line and Python interfaces, with CSV and JSON output for downstream analysis.
- **Replayable snapshots** — preserve sampled pixels, text coordinates and capture metadata for inspection and offline reprocessing.

## Quick start

```bash
git clone https://github.com/webtechnologyoxford/chartgrab.git
cd chartgrab
python -m pip install -e ".[browser]"
python -m playwright install chromium

# Run the bundled demo
chartgrab url "file://$PWD/examples/demo_chart.html" \
  --pos "#22c55e" --neg "#ef4444" --x-step 5 --format json
```

Python 3.9+. The core uses NumPy and Pillow; browser capture and image OCR are optional.

## Example output

Illustrative values; units follow the source chart.

| Horizontal label | Value | Estimated error |
| ---: | ---: | ---: |
| 185 | +60.00 M | ±1.29 M |
| 190 | −39.35 M | ±1.29 M |

## Documentation

[Safari, Chrome & image usage](docs/GUIDE.md#capture-modes) · [Calibration & limits](docs/GUIDE.md#calibration-and-limits) · [中文指南](docs/GUIDE.md#中文说明)

**v0.1 scope:** vertical bars and linear axes. Canvas-painted labels need explicit calibration or a separate OCR workflow. Cross-frame tracking belongs to the integrating application. The breakthrough above describes the originating project's workflow, not a universal accuracy benchmark or a claim that other tools cannot implement it.

[MIT License](LICENSE) · Use only data you are authorised to access and process.
