# ragtable-extract

[English](README.md) | [中文](README_zh.md)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**PDF Parsing for RAG** — extracting tables precisely. Convert to HTML. Fast, local, no GPU.

A lightweight Python library that extracts tables from PDFs and converts them to clean HTML, designed for RAG pipelines and LLM retrieval. Runs entirely on CPU with no external APIs or GPU dependencies.

## Features

- **Precise extraction** — Character-level coordinate extraction for accurate cell boundaries
- **≥/≤ symbols** — Correctly repositioned by coordinates (avoids pdfplumber's line-end placement bug)
- **Merged cells** — Proper `rowspan` / `colspan` output for multi-column tables
- **Line-wrapped text** — Auto-segments and concatenates text across line breaks within cells (no symbol/text serialization)
- **Fangzheng font** — Handles full-width character ordering and decimal point encoding issues
- **Adaptive config** — Per-page tuning based on character metrics
- **Fast & local** — Pure Python, pdfplumber-based, no GPU required

## Requirements

- Python 3.8+
- pdfplumber >= 0.10.0

## Installation

```bash
pip install ragtable-extract
```

Or from source:

```bash
git clone https://github.com/ZhuJiaxin2/ragtable-extract.git
cd ragtable-extract
pip install -e .
```

## Quick Start

```python
import ragtable_extract

# Convert PDF tables to HTML file
ragtable_extract.convert(
    input_path="document.pdf",
    output_path="tables.html",
)

# Or extract as structured data
tables = ragtable_extract.extract(input_path="document.pdf")
for t in tables:
    print(f"Page {t['page']}: {t['html'][:80]}...")
```

## CLI

```bash
python -m ragtable_extract document.pdf output.html
```

## API

| Function | Description |
|----------|-------------|
| `convert(input_path, output_path, pages?, config?, use_adaptive_config=True)` | Convert PDF tables to HTML file |
| `extract(input_path, pages?, config?, use_adaptive_config=True)` | Extract tables as list of dicts with `page`, `html`, `bbox`, `raw` |
| `build_full_html(pdf_filename, tables)` | Build full HTML document from extracted tables |
| `Config` | Dataclass for tuning extraction (multiline thresholds, font tolerance, etc.) |

## Configuration

```python
import ragtable_extract

# Custom config
config = ragtable_extract.Config(
    multiline_cell_top_range=25,
    multiline_y_tolerance=4,
)
tables = ragtable_extract.extract("doc.pdf", config=config)

# Adaptive config (default) — infers parameters from page character metrics
tables = ragtable_extract.extract("doc.pdf")  # use_adaptive_config=True by default
```

## Project Structure

```
ragtable-extract/
├── ragtable_extract/     # Core library
│   ├── __init__.py       # convert(), extract()
│   ├── _core.py          # Table extraction logic
│   ├── _config.py        # Config & adaptive metrics
│   ├── _font.py          # Special font handling
│   └── _html.py          # HTML template
├── pyproject.toml
├── demo.py               # CLI demo
└── app.py                # Optional Flask web API
```

## How It Works

```
PDF → pdfplumber.find_tables()
  → Filter chars by bbox, cluster by top (y)
  → Reorder ≥/≤ symbols, fix Fangzheng font
  → Output <table> HTML
```

## Comparison Report

We compare ragtable-extract with [opendataloader-pdf](https://pypi.org/project/opendataloader-pdf/) on real government PDF tables. Our extraction:

- **Multi-column tables** — Correctly recognizes complex layouts with merged cells
- **Line-wrapped text** — Automatically segments and concatenates text across line breaks within cells
- **No serialization** — Symbols and text stay in correct cells (e.g. no `１ ２` or `万人 ％` wrongly merged)

Run `python test_comparison.py` to generate the report, then open [comparison_report.html](comparison_report.html) for side-by-side results.

## License

MIT
