#!/usr/bin/env python3
"""
ragtable-extract 命令行 Demo

  python demo.py [pdf路径] [输出html路径]
  python demo.py  # 默认 test.pdf → output.html
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import ragtable_extract


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "test.pdf"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output.html"

    if not os.path.exists(pdf_path):
        print(f"错误: 文件不存在: {pdf_path}")
        sys.exit(1)

    print(f"正在处理: {pdf_path}")
    _, tables = ragtable_extract.convert(input_path=pdf_path, output_path=output_path)
    print(f"已保存到: {output_path}")
    print(f"共提取 {len(tables)} 个表格")


if __name__ == "__main__":
    main()
