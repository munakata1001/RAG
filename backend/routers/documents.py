import os
from typing import Optional

# PDF抽出用
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# DOCX抽出用
try:
    import docx
except ImportError:
    docx = None


def extract_text(file_path: str, ext: Optional[str] = None) -> str:
    """
    PDF / DOCX / TXT からテキスト抽出
    ext を渡さない場合はファイル名から自動判定
    """
    if not ext:
        ext = os.path.splitext(file_path)[1][1:].lower()

    text = ""
    if ext == "pdf":
        if not fitz:
            raise ImportError("PyMuPDF がインストールされていません")
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])
    elif ext in ["docx", "doc"]:
        if not docx:
            raise ImportError("python-docx がインストールされていません")
        doc = docx.Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    elif ext == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise ValueError(f"未対応のファイル形式: {ext}")

    return text
