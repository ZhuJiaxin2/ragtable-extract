"""
ragtable-extract — PDF Parsing for RAG

Extracting tables precisely. Convert to HTML. Fast, local, no GPU.
"""

import os
from typing import List, Optional

from ._config import Config, DEFAULT_CONFIG, compute_page_metrics
from ._core import extract_tables_from_pdf
from ._html import build_full_html

__version__ = "0.1.0"
__all__ = [
    "convert",
    "extract",
    "extract_tables_from_pdf",
    "build_full_html",
    "Config",
    "compute_page_metrics",
]


def convert(
    input_path: str,
    output_path: str,
    pages: Optional[List[int]] = None,
    config: Optional[Config] = None,
    use_adaptive_config: bool = True,
):
    """
    Convert PDF tables to HTML file.

    Args:
        input_path: Path to PDF file
        output_path: Path to output HTML file
        pages: Optional list of 1-based page numbers to process (default: all)
        config: Optional config; if None and use_adaptive_config=True, 从首页推算
        use_adaptive_config: 当 config 为 None 时，是否根据页面字符尺寸自适应

    Returns:
        (output_path, tables) — path and list of extracted tables

    Example:
        >>> import ragtable_extract
        >>> path, tables = ragtable_extract.convert(input_path="document.pdf", output_path="tables.html")
        >>> config = ragtable_extract.Config(multiline_cell_top_range=25)
        >>> path, tables = ragtable_extract.convert("doc.pdf", "out.html", config=config)
    """
    tables = extract_tables_from_pdf(
        input_path, page_numbers=pages, config=config, use_adaptive_config=use_adaptive_config
    )
    html = build_full_html(os.path.basename(input_path), tables)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path, tables


def extract(
    input_path: str,
    pages: Optional[List[int]] = None,
    config: Optional[Config] = None,
    use_adaptive_config: bool = True,
) -> List[dict]:
    """
    Extract tables from PDF as structured data.

    Args:
        input_path: Path to PDF file
        pages: Optional list of 1-based page numbers (default: all)
        config: Optional config; if None and use_adaptive_config=True, 从首页推算
        use_adaptive_config: 当 config 为 None 时，是否根据页面字符尺寸自适应

    Returns:
        List of dicts with keys: page, html, bbox, raw

    Example:
        >>> import ragtable_extract
        >>> tables = ragtable_extract.extract(input_path="document.pdf")
        >>> config = ragtable_extract.Config(multiline_cell_top_range=25)
        >>> tables = ragtable_extract.extract("doc.pdf", config=config)
    """
    return extract_tables_from_pdf(
        input_path,
        page_numbers=pages,
        config=config,
        use_adaptive_config=use_adaptive_config,
    )
