# chartgrab

**From browser charts to structured data.**

Extract values from Canvas bar charts and chart images. Export horizontal positions, signed values and measurement-error estimates as **CSV or JSON**—locally, without cloud AI.

**将网页柱状图转换为结构化数据。** 读取画布像素、标定坐标轴、批量提取柱值，支持误差估计与快照离线重读。

```text
Browser chart → Pixels + axis labels → Values ± error → CSV / JSON
```

## Features

- **Browser-native capture** — existing Safari and Chrome tabs, or fresh pages via Playwright.
- **Batch measurement** — positive and negative vertical bars with linear-axis calibration.
- **Reproducible results** — save snapshots and reprocess them offline.

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
