"""HTML output template."""


def build_full_html(pdf_filename: str, tables: list) -> str:
    count = len(tables)
    parts = [
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PDF 表格提取结果 - """
        + pdf_filename
        + """</title>
  <style>
    body { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; margin: 24px; background: #f5f5f5; }
    h1 { color: #333; margin-bottom: 8px; }
    .meta { color: #666; font-size: 14px; margin-bottom: 24px; }
    .table-wrap { background: #fff; padding: 16px; margin-bottom: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow-x: auto; }
    .table-wrap h2 { color: #444; font-size: 16px; margin: 0 0 12px 0; }
    table { border-collapse: collapse; width: 100%; font-size: 13px; }
    td, th { border: 1px solid #ccc; padding: 8px 10px; text-align: left; vertical-align: top; }
    td { background: #fafafa; }
    tr:nth-child(even) td { background: #f5f5f5; }
  </style>
</head>
<body>
  <h1>PDF 表格提取结果</h1>
  <div class="meta">源文件: """
        + pdf_filename
        + """ | 共 """
        + str(count)
        + """ 个表格</div>
"""
    ]
    for i, t in enumerate(tables):
        parts.append(
            f'  <div class="table-wrap"><h2>表格 {i + 1}（第 {t["page"]} 页）</h2>\n{t["html"]}\n  </div>\n'
        )
    parts.append("</body>\n</html>")
    return "".join(parts)
