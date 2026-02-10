# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2025/8/5 11:59
# @Software  : PyCharm
# @FileName  : loader.py
# -----------------------------
"""处理上传的文件和图片"""
import os
import subprocess
import tempfile

import docx
import fitz
from cnocr import CnOcr

from core.logs import logger

ocr = CnOcr()


def load_text(file_path: str) -> str:
    """统一提取文本"""
    suffix = os.path.splitext(file_path)[1].lower()
    try:
        if suffix in {".png", ".jpg", ".jpeg"}:
            result = ocr.ocr(file_path)
            return "".join(i['text'] for i in result)
        if suffix == ".pdf":
            return "\n".join(page.get_text() for page in fitz.open(file_path))
        if suffix == ".docx":
            return "\n".join(p.text for p in docx.Document(file_path).paragraphs)
        if suffix == ".doc":
            # 简单方案：先转 docx
            with tempfile.TemporaryDirectory() as td:
                tmp = os.path.join(td, "tmp.docx")
                subprocess.run(["libreoffice", "--headless", "--convert-to", "docx", file_path, "--outdir", td],
                               check=True)
                return load_text(tmp)
        if suffix == ".md":
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        if suffix == ".txt":
            with open(file_path, encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.error(f"解析文件失败: {e}")
        raise RuntimeError(f"解析文件失败: {e}")
    raise ValueError("不支持的文件格式")


if __name__ == '__main__':
    print(load_text(r"E:\develop\aicases\dl.png"))
