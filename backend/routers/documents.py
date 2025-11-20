from fastapi import APIRouter, UploadFile, File, HTTPException
import pdfplumber  # pyright: ignore[reportMissingImports]
import docx  # pyright: ignore[reportMissingImports]
import os

router = APIRouter()

UPLOAD_DIR = "./data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    文書ファイルをアップロードし、テキスト抽出まで行う
    """

    # ① 拡張子チェック
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="ファイル名が不正です")

    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "docx", "txt"]:
        raise HTTPException(status_code=400, detail="対応していない形式です（pdf/docx/txt）")

    # ② ファイル保存
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())

    # ③ テキスト抽出処理
    extracted_text = extract_text(save_path, ext)

    return {
        "filename": filename,
        "text_length": len(extracted_text),
        "preview": extracted_text[:300]  # 最初の300文字だけ返す
    }


def extract_text(path: str, ext: str) -> str:
    """拡張子に応じたテキスト抽出"""

    # PDF
    if ext == "pdf":
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    # Word
    if ext == "docx":
        doc = docx.Document(path)
        return "\n".join([para.text for para in doc.paragraphs])

    # TXT
    if ext == "txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    return ""
