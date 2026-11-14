# chartgrab

**Turn web charts into a programmable data source.**

For dashboards without a suitable structured export, chartgrab extracts bar-chart data from browser Canvas elements or images. Recover horizontal positions, signed values and measurement-error estimates, then export **CSV or JSON** for your analysis pipeline.

**让网页图表成为可计算的数据源。**

面向缺乏结构化导出接口的仪表盘，直接从浏览器 Canvas 或图表图片批量提取柱状数据，恢复横轴位置、正负数值与误差估计，输出 CSV／JSON。

支持 Safari、Chrome 及 Python 集成，本地处理，无需逐柱悬停或云端视觉模型；原始快照可保存、复查和离线重算。

```text
Browser chart → Pixels + axis labels → Values ± error → Your analysis pipeline
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

**v0.1 scope:** vertical bars and linear axes. Canvas-painted labels need explicit calibration or a separate OCR workflow. Cross-frame tracking belongs to the integrating application.

[MIT License](LICENSE) · Use only data you are authorised to access and process.
