# ragtable-extract

[English](README.md) | [中文](README_zh.md)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**面向 RAG 的 PDF 解析** — 精确提取表格并转为 HTML。轻量、本地、无需 GPU。

轻量级 Python 库，从 PDF 中提取表格并转换为干净的 HTML，适用于 RAG 流水线和 LLM 检索。纯 CPU 运行，无需外部 API 或 GPU。

## 特性

- **精确提取** — 字符级坐标提取，准确识别单元格边界
- **≥/≤ 符号** — 按坐标正确重排（避免 pdfplumber 行尾放置错误）
- **合并单元格** — 正确输出 `rowspan` / `colspan`，支持多列表格
- **换行文字** — 自动分段并拼接单元格内换行文本，避免符号、文字串行
- **方正字体** — 处理全角字符顺序和小数点编码问题
- **自适应配置** — 根据页面字符指标进行逐页调优
- **快速本地** — 纯 Python，基于 pdfplumber，无需 GPU

## 环境要求

- Python 3.8+
- pdfplumber >= 0.10.0

## 安装

```bash
pip install ragtable-extract
```

或从源码安装：

```bash
git clone https://github.com/ZhuJiaxin2/ragtable-extract.git
cd ragtable-extract
pip install -e .
```

## 快速开始

```python
import ragtable_extract

# 将 PDF 表格转换为 HTML 文件
ragtable_extract.convert(
    input_path="document.pdf",
    output_path="tables.html",
)

# 或提取为结构化数据
tables = ragtable_extract.extract(input_path="document.pdf")
for t in tables:
    print(f"第 {t['page']} 页: {t['html'][:80]}...")
```

## 命令行

```bash
python -m ragtable_extract document.pdf output.html
```

## 网页快速测试（app.py）

运行 Flask  Web 服务，在浏览器中上传 PDF 并预览提取结果：

```bash
pip install flask
python app.py
```

然后访问 http://localhost:1965 上传 PDF 并查看表格提取结果。

## 测试结果

运行 `python test.py` 生成提取结果。输出文件：

| 源文件 | 读取结果 |
|--------|----------|
| [test/example/zhejiang.pdf](test/example/zhejiang.pdf) | [test/result/test_adaptive_zhejiang.html](test/result/test_adaptive_zhejiang.html) |
| [test/example/changsha.pdf](test/example/changsha.pdf) | [test/result/test_adaptive_changsha.html](test/result/test_adaptive_changsha.html) |
| [test/example/shaanxi.pdf](test/example/shaanxi.pdf) | [test/result/test_adaptive_shaanxi.html](test/result/test_adaptive_shaanxi.html) |
| [test/example/tongbao.pdf](test/example/tongbao.pdf) | [test/result/test_adaptive_tongbao.html](test/result/test_adaptive_tongbao.html) |

## API

| 函数 | 说明 |
|------|------|
| `convert(input_path, output_path, pages?, config?, use_adaptive_config=True)` | 将 PDF 表格转换为 HTML 文件 |
| `extract(input_path, pages?, config?, use_adaptive_config=True)` | 提取表格为字典列表，含 `page`、`html`、`bbox`、`raw` |
| `build_full_html(pdf_filename, tables)` | 从提取结果构建完整 HTML 文档 |
| `Config` | 数据类，用于调优提取参数（多行阈值、字体容差等） |

## 配置

```python
import ragtable_extract

# 自定义配置
config = ragtable_extract.Config(
    multiline_cell_top_range=25,
    multiline_y_tolerance=4,
)
tables = ragtable_extract.extract("doc.pdf", config=config)

# 自适应配置（默认）— 根据页面字符指标推断参数
tables = ragtable_extract.extract("doc.pdf")  # 默认 use_adaptive_config=True
```

## 项目结构

```
ragtable-extract/
├── ragtable_extract/     # 核心库
│   ├── __init__.py       # convert(), extract()
│   ├── _core.py          # 表格提取逻辑
│   ├── _config.py        # 配置与自适应指标
│   ├── _font.py          # 特殊字体处理
│   └── _html.py          # HTML 模板
├── pyproject.toml
├── demo.py               # CLI 示例
└── app.py                # 可选 Flask Web API
```

## 工作原理

```
PDF → pdfplumber.find_tables()
  → 按 bbox 过滤字符，按 top (y) 聚类
  → 重排 ≥/≤ 符号，修复方正字体
  → 输出 <table> HTML
```

## 对比报告

我们在真实政府 PDF 表格上与 [opendataloader-pdf](https://pypi.org/project/opendataloader-pdf/) 进行对比。本库的提取效果：

- **多列表格** — 正确识别含合并单元格的复杂布局
- **换行文字** — 自动分段并拼接单元格内换行文本
- **无串行** — 符号和文字保持在正确单元格内（如不会出现 `１ ２`、`万人 ％` 等错误合并）

运行 `python test_comparison.py` 生成报告，然后打开 [comparison_report.html](comparison_report.html) 查看并排对比结果。

## 许可证

MIT
