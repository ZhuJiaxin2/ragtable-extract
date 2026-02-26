"""可配置参数，用于控制表格提取行为。"""

from dataclasses import dataclass, field
from statistics import median
from typing import Dict, FrozenSet, Optional, Tuple


def _median(values, default: float = 10.0) -> float:
    """安全中位数，空列表返回 default。"""
    if not values:
        return default
    return float(median(values))


def compute_page_metrics(page) -> dict:
    """
    从 PDF 页面提取字符尺寸，用于自适应配置。

    使用 p25 作为 char_height，因表格正文通常小于页眉/标题，中位数易被大字号拉高。
    """
    chars = getattr(page, "chars", None)
    if not chars:
        return {"char_height": 10.0, "char_width": 10.0}
    heights = sorted(
        c["bottom"] - c["top"]
        for c in chars
        if c.get("bottom", 0) > c.get("top", 0) and 4 < (c["bottom"] - c["top"]) < 50
    )
    widths = [c["x1"] - c["x0"] for c in chars if c.get("x1", 0) > c.get("x0", 0)]
    h = heights[len(heights) // 4] if heights else 10.0
    return {
        "char_height": max(h, 6.0),
        "char_width": max(_median(widths), 6.0),
    }


# 自适应系数：由实例文档回推，使 char_height≈10.3pt 时得到当前默认值
_ADAPTIVE_COEF = {
    "multiline_cell_top_range": 2.0,
    "multiline_y_tolerance": 0.4,
    "fangzheng_y_tolerance": 1.2,
    "default_y_tolerance": 0.2,
    "multiline_top_span": 1.0,
    "char_spacing_tolerance": 0.3,
    "cross_cell_expand": 1.2,
}


@dataclass
class Config:
    """
    表格提取配置，所有参数均有默认值。

    使用示例:
        >>> config = Config(multiline_cell_top_range=25)
        >>> tables = ragtable_extract.extract("doc.pdf", config=config)
    """

    # --- 符号重排 ---
    # 需按坐标插入的运算符前缀（单独成行时）
    prefix_operator_symbols: FrozenSet[str] = field(
        default_factory=lambda: frozenset("≥≤≧≦")
    )
    # 跨单元格扩展 bbox 的符号（仅这些符号会向下扩展 12pt）
    cross_cell_symbols: FrozenSet[str] = field(
        default_factory=lambda: frozenset("≥≤≧≦")
    )

    # --- 行内排序 ---
    # 簇内 top 跨度超过此值时，检查是否按 (top,x0) 排序
    multiline_top_span: float = 10.0
    # 字符间距超过此值时插入空格 (pt)
    char_spacing_tolerance: float = 3.0

    # --- 多行单元格 ---
    # 单元格内字符 top 跨度超过此值时，视为多行布局
    multiline_cell_top_range: float = 20.0
    # 多行单元格使用的 y 聚类容差
    multiline_y_tolerance: float = 4.0

    # --- 跨格符号 bbox 扩展 ---
    # ≥≤ 等符号向下扩展的 pt 数
    cross_cell_expand: float = 12.0

    # --- 方正字体 ---
    # 方正字体 fontname 匹配模式
    fangzheng_font_patterns: Tuple[str, ...] = ("PK7483", "FZ", "FZSS", "FZHT")
    # 检测到方正字体时的 y 聚类容差
    fangzheng_y_tolerance: float = 12.0
    # 默认（非方正）y 聚类容差
    default_y_tolerance: float = 2.0

    # --- 特殊符号映射：PUA/乱码 → 正确字符 ---
    special_symbol_map: Dict[str, str] = field(
        default_factory=lambda: {
            "\uE010": ".",
            "\uE011": ".",
            "\u00B7": ".",
        }
    )

    @classmethod
    def from_page(cls, page, base: Optional["Config"] = None) -> "Config":
        """
        根据页面字符尺寸生成自适应配置。

        公式由实例文档回推：char_height≈10.3pt 时，各参数等于当前默认值。
        """
        base = base or cls()
        metrics = compute_page_metrics(page)
        h = metrics["char_height"]
        return cls(
            prefix_operator_symbols=base.prefix_operator_symbols,
            cross_cell_symbols=base.cross_cell_symbols,
            fangzheng_font_patterns=base.fangzheng_font_patterns,
            special_symbol_map=dict(base.special_symbol_map),
            multiline_top_span=_ADAPTIVE_COEF["multiline_top_span"] * h,
            char_spacing_tolerance=_ADAPTIVE_COEF["char_spacing_tolerance"] * h,
            multiline_cell_top_range=_ADAPTIVE_COEF["multiline_cell_top_range"] * h,
            multiline_y_tolerance=_ADAPTIVE_COEF["multiline_y_tolerance"] * h,
            cross_cell_expand=_ADAPTIVE_COEF["cross_cell_expand"] * h,
            fangzheng_y_tolerance=_ADAPTIVE_COEF["fangzheng_y_tolerance"] * h,
            default_y_tolerance=_ADAPTIVE_COEF["default_y_tolerance"] * h,
        )

    @classmethod
    def from_metrics(cls, char_height: float, base: Optional["Config"] = None) -> "Config":
        """根据给定字符高度生成自适应配置。"""
        return cls.from_page(_MetricsPage(char_height), base)


class _MetricsPage:
    """用于 from_metrics 的虚拟 page，仅提供 char_height。"""

    def __init__(self, char_height: float):
        self._char_height = max(char_height, 6.0)

    @property
    def chars(self):
        return [{"top": 0, "bottom": self._char_height, "x0": 0, "x1": self._char_height}]


# 默认配置实例
DEFAULT_CONFIG = Config()
