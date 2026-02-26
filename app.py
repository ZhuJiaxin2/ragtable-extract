#!/usr/bin/env python3
"""PDF 表格提取 Web 服务：上传 PDF，返回表格 HTML，支持下载。"""

import os
import tempfile

from flask import Flask, request, jsonify, render_template

import ragtable_extract

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB
ALLOWED = {"pdf"}


def allowed_file(name):
    return name and name.lower().endswith(".pdf")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "未选择文件"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "未选择文件"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "仅支持 PDF 文件"}), 400

    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            path = tmp.name
            f.save(path)
        tables = ragtable_extract.extract(input_path=path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if path and os.path.exists(path):
            os.unlink(path)

    out = [{"page": t["page"], "html": t["html"]} for t in tables]
    full_html = ragtable_extract.build_full_html(f.filename, tables)
    return jsonify({"tables": out, "fullHtml": full_html, "filename": f.filename})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1965, debug=True)
