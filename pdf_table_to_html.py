#!/usr/bin/env python3
"""
PDF 表格转 HTML 工具（基于 ragtable_extract）

解决 pdfplumber 的已知问题：
1. ≥/≤ 等符号错误放置 - 通过字符位置重排修复
2. 合并单元格导致最后分行错误 - 通过基于字符坐标的精确提取修复
3. 输出正确的 rowspan/colspan HTML 表格
"""

import sys

import ragtable_extract


def extract_tables_from_pdf(pdf_path: str, page_numbers=None):
    """从 PDF 提取所有表格。兼容旧接口。"""
    return ragtable_extract.extract(
        pdf_path,
        pages=page_numbers,
        use_adaptive_config=True,
    )


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "test.pdf"
    tables = extract_tables_from_pdf(path)
    for i, t in enumerate(tables):
        print(f"\n<!-- Table {i + 1} (Page {t['page']}) -->")
        print(t["html"])
