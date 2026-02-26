"""Core PDF table extraction logic."""

import html
from operator import itemgetter
from typing import List, Optional, Tuple, Dict, Any

import pdfplumber
from pdfplumber.utils import extract_text
from pdfplumber.utils.clustering import cluster_objects

from ._font import fix_special_symbols, get_special_font_y_tolerance
from ._config import Config, DEFAULT_CONFIG


def _compute_y_tolerance(
    top_range: float, base_tolerance: float, config: Config
) -> float:
    """
    计算单元格内字符聚类的 y 容差。
    - top_range > multiline_cell_top_range：明确多行，用 multiline_y_tolerance
    - base 过大且 top_range 中等：避免误合并（如长沙「200」变「2面0积0平」），改用 multiline
    """
    if top_range > config.multiline_cell_top_range:
        return config.multiline_y_tolerance
    if top_range > 10 and base_tolerance > top_range * 0.9:
        return config.multiline_y_tolerance
    return base_tolerance


def _chars_to_line(chars: List[dict], config: Config, x_tol: Optional[float] = None) -> str:
    x_tol = x_tol if x_tol is not None else config.char_spacing_tolerance
    tops = [c["top"] for c in chars]
    top_span = max(tops) - min(tops) if tops else 0
    use_top_first = False
    if top_span > config.multiline_top_span:
        mid = (min(tops) + max(tops)) / 2
        upper = [c for c in chars if c["top"] <= mid]
        lower = [c for c in chars if c["top"] > mid]
        # 仅当「下行」有字符延伸到「上行」左侧时，才按 (top,x0) 排序
        # 否则按 x0 排序，以正确处理括号内角标（如ＰＭ２.５、Ｒ＆Ｄ）
        if upper and lower and min(c["x0"] for c in lower) < min(c["x0"] for c in upper):
            use_top_first = True
    if use_top_first:
        sorted_chars = sorted(chars, key=lambda c: (c["top"], c["x0"]))
    else:
        sorted_chars = sorted(chars, key=itemgetter("x0"))
    parts, last_x1 = [], None
    for c in sorted_chars:
        if last_x1 is not None and c["x0"] > last_x1 + x_tol:
            parts.append(" ")
        parts.append(c["text"])
        last_x1 = c["x1"]
    return "".join(parts)


def _reorder_chars_with_symbols(
    lines_chars: List[List[dict]], config: Config
) -> List[List[dict]]:
    result = []
    pending_symbols = []
    prefix_symbols = config.prefix_operator_symbols

    def insert_symbol(sym_char, target_chars):
        sym_x0 = sym_char["x0"]
        candidates = [c for c in target_chars if c["x0"] > sym_x0]
        if candidates:
            target = min(candidates, key=lambda c: c["x0"])
            target_chars.insert(target_chars.index(target), sym_char)
        else:
            target_chars.append(sym_char)

    for line_chars in lines_chars:
        if all(c["text"] in prefix_symbols for c in line_chars):
            pending_symbols.extend(line_chars)
            continue

        line_top = min(c["top"] for c in line_chars)
        current_line = list(line_chars)

        for sym_char in pending_symbols:
            sym_top = sym_char["top"]
            prev_line_top = min(c["top"] for c in result[-1]) if result else None
            if result and (
                sym_top > line_top
                or (prev_line_top and prev_line_top < sym_top < line_top)
            ):
                insert_symbol(sym_char, result[-1])
            else:
                insert_symbol(sym_char, current_line)

        pending_symbols.clear()
        result.append(current_line)

    if pending_symbols and result:
        for sym_char in pending_symbols:
            insert_symbol(sym_char, result[-1])

    return result


def extract_cell_text_by_chars(
    page,
    cell_bbox: Tuple[float, float, float, float],
    prev_cell_bottom: Optional[float] = None,
    config: Optional[Config] = None,
) -> str:
    config = config or DEFAULT_CONFIG
    cx0, ctop, cx1, cbottom = cell_bbox
    chars = page.chars
    expand = config.cross_cell_expand
    cross_symbols = config.cross_cell_symbols

    def char_in_bbox(char):
        v_mid = (char["top"] + char["bottom"]) / 2
        h_mid = (char["x0"] + char["x1"]) / 2
        if not (cx0 <= h_mid < cx1):
            return False
        if char["text"] in cross_symbols:
            v_ok = ctop <= v_mid < cbottom + expand
            if (
                prev_cell_bottom is not None
                and prev_cell_bottom < v_mid <= prev_cell_bottom + expand
            ):
                v_ok = False
            return v_ok
        return ctop <= v_mid < cbottom

    cell_chars = [c for c in chars if char_in_bbox(c)]
    if not cell_chars:
        return ""

    tops = [c["top"] for c in cell_chars]
    top_range = max(tops) - min(tops) if tops else 0
    base_tolerance = get_special_font_y_tolerance(page, config)
    y_tolerance = _compute_y_tolerance(top_range, base_tolerance, config)
    lines_chars = cluster_objects(cell_chars, itemgetter("top"), y_tolerance)
    lines_chars = _reorder_chars_with_symbols(lines_chars, config)
    lines = [_chars_to_line(lc, config) for lc in lines_chars]

    text = "\n".join(lines)
    return fix_special_symbols(text, config)


def compute_cell_spans(table) -> List[List[Optional[Dict]]]:
    rows = table.rows
    if not rows:
        return []

    nrows = len(rows)
    ncols = len(rows[0].cells)
    row_tops = [r.bbox[1] for r in rows]
    result = [[None] * ncols for _ in range(nrows)]

    for i in range(nrows):
        for j in range(ncols):
            cell = rows[i].cells[j] if j < len(rows[i].cells) else None
            if cell is None:
                continue
            x0, top, x1, bottom = cell

            rowspan = 1
            for ii in range(i + 1, nrows):
                if row_tops[ii] < bottom:
                    rowspan += 1
                else:
                    break

            colspan = 1
            for jj in range(j + 1, ncols):
                if jj < len(rows[i].cells) and rows[i].cells[jj] is None:
                    colspan += 1
                else:
                    break

            result[i][j] = {"bbox": cell, "rowspan": rowspan, "colspan": colspan}

    return result


def _get_prev_cell_bottom(
    span_grid: List[List], row: int, col: int
) -> Optional[float]:
    if row <= 0:
        return None
    for ri in range(row):
        for cj in range(len(span_grid[ri])):
            info = span_grid[ri][cj]
            if info is None:
                continue
            rs, cs = info["rowspan"], info["colspan"]
            if ri <= row - 1 < ri + rs and cj <= col < cj + cs:
                return info["bbox"][3]
    return None


def table_to_html(
    page,
    table,
    use_char_extraction: bool = True,
    config: Optional[Config] = None,
) -> str:
    config = config or DEFAULT_CONFIG
    span_grid = compute_cell_spans(table)

    html_parts = [
        '<table border="1" cellpadding="4" cellspacing="0" style="border-collapse: collapse;">'
    ]
    used = set()

    for i, row in enumerate(table.rows):
        html_parts.append("<tr>")
        for j, cell_info in enumerate(span_grid[i]):
            if (i, j) in used:
                continue
            if cell_info is None:
                continue

            bbox = cell_info["bbox"]
            rowspan = cell_info["rowspan"]
            colspan = cell_info["colspan"]

            if use_char_extraction:
                prev_bottom = _get_prev_cell_bottom(span_grid, i, j)
                text = extract_cell_text_by_chars(
                    page, bbox, prev_cell_bottom=prev_bottom, config=config
                )
            else:
                cell_chars = [
                    c
                    for c in page.chars
                    if (bbox[0] <= (c["x0"] + c["x1"]) / 2 < bbox[2])
                    and (bbox[1] <= (c["top"] + c["bottom"]) / 2 < bbox[3])
                ]
                text = extract_text(cell_chars, layout=True) if cell_chars else ""

            text = html.escape(text).replace("\n", "")

            rs = f' rowspan="{rowspan}"' if rowspan > 1 else ""
            cs = f' colspan="{colspan}"' if colspan > 1 else ""
            html_parts.append(f"<td{rs}{cs}>{text}</td>")

            for ii in range(i, i + rowspan):
                for jj in range(j, j + colspan):
                    used.add((ii, jj))

        html_parts.append("</tr>")

    html_parts.append("</table>")
    return "\n".join(html_parts)


def extract_tables_from_pdf(
    pdf_path: str,
    page_numbers: Optional[List[int]] = None,
    config: Optional[Config] = None,
    use_adaptive_config: bool = True,
) -> List[Dict[str, Any]]:
    result = []
    with pdfplumber.open(pdf_path) as pdf:
        base_config = config or DEFAULT_CONFIG
        pages = page_numbers if page_numbers else range(len(pdf.pages))
        for pnum in pages:
            page = pdf.pages[pnum]
            tables = page.find_tables()
            page_config = (
                Config.from_page(page, base=base_config)
                if use_adaptive_config and config is None
                else base_config
            )
            for t in tables:
                html_table = table_to_html(page, t, config=page_config)
                result.append(
                    {
                        "page": pnum + 1,
                        "bbox": t.bbox,
                        "html": html_table,
                        "raw": t.extract(),
                    }
                )
    return result
