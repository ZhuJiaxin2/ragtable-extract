#!/usr/bin/env python3
"""测试自适应配置：逐页推算，遍历所有表格所在页面。"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import ragtable_extract


# 自适应测试用例：(PDF路径, 输出文件名, 显示名, [(断言子串, 失败消息), ...])
_ADAPTIVE_TEST_CASES = [
    (
        "test/example/zhejiang.pdf",
        "test_adaptive_zhejiang",
        "浙江",
        [
            ("细颗粒物（ＰＭ２.５）", "细颗粒物（ＰＭ２.５）未正确提取"),
            ("微克／立方米", "微克／立方米未正确提取"),
            ("地区生产总值（ＧＤＰ）增长", "地区生产总值（ＧＤＰ）增长未正确提取"),
        ],
    ),
    (
        "test/example/changsha.pdf",
        "test_adaptive_changsha",
        "长沙",
        [
            ("服务半径≤300米", "幼儿园 服务半径≤300米 未正确提取"),
            ("超过12班≥12.7平方米/生", "4班1800 超过12班≥12.7 未正确提取"),
            ("超过12班≥8.9平方米/生", "4班1200 超过12班≥8.9 未正确提取"),
            ("200平方米用地面积且≥6.7平方米用地面积/百户", "最后一页 200平方米用地面积/百户 未正确提取"),
        ],
    ),
    (
        "test/example/shaanxi.pdf",
        "test_adaptive_shaanxi",
        "陕西",
        [
            ("陕西科技大学", "陕西科技大学 未正确提取"),
            ("陕西财经职业技术学院", "陕西财经职业技术学院 未正确提取"),
            ("陕西中医药大学", "陕西中医药大学 未正确提取"),
        ],
    ),
    (
        "test/example/tongbao.pdf",
        "test_adaptive_tongbao",
        "通报",
        [
            ("部门/地区", "部门/地区 未正确提取"),
            ("运行网站总数", "运行网站总数 未正确提取"),
            ("公司总部", "公司总部 未正确提取"),
            ("省级分公司", "省级分公司 未正确提取"),
        ],
    ),
]


def _resolve_path(path: str) -> str:
    """将相对路径解析为基于脚本目录的绝对路径。"""
    return str(Path(__file__).parent / path) if not os.path.isabs(path) else path


def _run_adaptive_test(path: str, assertions: list, name: str) -> bool:
    """执行单个 PDF 的自适应测试。"""
    full_path = _resolve_path(path)
    if not os.path.exists(full_path):
        print(f"跳过: {path} 不存在")
        return True
    tables = ragtable_extract.extract(full_path, use_adaptive_config=True)
    html = "".join(t["html"] for t in tables)
    for sub, msg in assertions:
        assert sub in html, msg
    print(f"✓ {name} 自适应测试通过")
    return True


def test_adaptive_zhejiang():
    """浙江 PDF：细颗粒物、微克／立方米、ＧＤＰ 等应正确提取。"""
    path, _, name, assertions = _ADAPTIVE_TEST_CASES[0]
    return _run_adaptive_test(path, assertions, f"{name} PDF")


def test_adaptive_changsha():
    """长沙 PDF：幼儿园、4班1800 等多行单元格应正确提取。"""
    path, _, name, assertions = _ADAPTIVE_TEST_CASES[1]
    return _run_adaptive_test(path, assertions, f"{name} PDF")


def test_adaptive_shaanxi():
    """陕西 PDF：教育厅科研计划项目申报通知，高校名单等应正确提取。"""
    path, _, name, assertions = _ADAPTIVE_TEST_CASES[2]
    return _run_adaptive_test(path, assertions, f"{name} PDF")


def test_adaptive_tongbao():
    """通报 PDF：第四季度外网网站和新媒体抽查，部门/地区、检查数据等应正确提取。"""
    path, _, name, assertions = _ADAPTIVE_TEST_CASES[3]
    return _run_adaptive_test(path, assertions, f"{name} PDF")


def test_config_from_page():
    """Config.from_page 应返回基于页面字符尺寸的配置。"""
    path = _resolve_path(_ADAPTIVE_TEST_CASES[0][0])
    if not os.path.exists(path):
        print("跳过 Config.from_page 测试: PDF 不存在")
        return True
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        cfg = ragtable_extract.Config.from_page(pdf.pages[13])
    assert cfg.multiline_cell_top_range > 0
    assert cfg.multiline_y_tolerance > 0
    print(f"  from_page: multiline_cell_top_range={cfg.multiline_cell_top_range:.1f}")
    print("✓ Config.from_page 测试通过")
    return True


def test_config_from_metrics():
    """Config.from_metrics 应返回 char_height 对应的配置。"""
    cfg = ragtable_extract.Config.from_metrics(10.3)
    assert 19 < cfg.multiline_cell_top_range < 22
    assert 3.5 < cfg.multiline_y_tolerance < 5
    print(f"  from_metrics(10.3): multiline_cell_top_range={cfg.multiline_cell_top_range:.1f}")
    print("✓ Config.from_metrics 测试通过")
    return True


def test_per_page_adaptive():
    """验证逐页自适应：不同页应有不同配置。"""
    path = _resolve_path(_ADAPTIVE_TEST_CASES[0][0])
    if not os.path.exists(path):
        print("跳过逐页自适应测试: PDF 不存在")
        return True
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        cfg0 = ragtable_extract.Config.from_page(pdf.pages[0])
        cfg13 = ragtable_extract.Config.from_page(pdf.pages[13])
    print(f"  页1: multiline_cell_top_range={cfg0.multiline_cell_top_range:.1f}")
    print(f"  页14: multiline_cell_top_range={cfg13.multiline_cell_top_range:.1f}")
    print("✓ 逐页自适应测试通过")
    return True


def test_per_page_adaptive_output():
    """逐页自适应：提取并输出完整 HTML，便于检查结果。"""
    output_dir = Path(__file__).parent / "test" / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for path, out_name, display_name, _ in _ADAPTIVE_TEST_CASES:
        full_path = _resolve_path(path)
        if os.path.exists(full_path):
            tables = ragtable_extract.extract(full_path, use_adaptive_config=True)
            out_path = output_dir / f"{out_name}.html"
            html = ragtable_extract.build_full_html(os.path.basename(full_path), tables)
            out_path.write_text(html, encoding="utf-8")
            outputs.append(str(out_path))
            print(f"  {display_name}: {len(tables)} 表 → {out_path.name}")
    if outputs:
        print(f"\n  输出文件: {', '.join(outputs)}")
        print("✓ 逐页自适应 output 已生成")
    return True


def main():
    print("=== 自适应配置测试 ===\n")
    ok = True
    ok &= test_config_from_metrics()
    ok &= test_config_from_page()
    ok &= test_per_page_adaptive()
    ok &= test_adaptive_zhejiang()
    ok &= test_adaptive_changsha()
    ok &= test_adaptive_shaanxi()
    ok &= test_adaptive_tongbao()
    print()
    ok &= test_per_page_adaptive_output()
    print("\n" + ("全部通过" if ok else "存在失败"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
