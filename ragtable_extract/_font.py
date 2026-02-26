"""Special font (e.g. Fangzheng) adaptation."""

from ._config import Config


def detect_fangzheng_font(page, config: Config) -> bool:
    chars = getattr(page, "chars", None)
    if not chars:
        return False
    for c in chars:
        fontname = c.get("fontname") or ""
        if any(p in fontname for p in config.fangzheng_font_patterns):
            return True
    return False


def fix_special_symbols(text: str, config: Config) -> str:
    for bad, good in config.special_symbol_map.items():
        text = text.replace(bad, good)
    return text


def get_special_font_y_tolerance(page, config: Config) -> float:
    return (
        config.fangzheng_y_tolerance
        if detect_fangzheng_font(page, config)
        else config.default_y_tolerance
    )
