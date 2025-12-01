# routers/pipeline.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import os
from services.chunking import split_into_chunks
from services.embedding import embed_chunks
from services.s3vectors_store import add_vectors_to_s3vectors
from services import document_registry
from routers.documents import extract_text  # PDF/DOCX/TXT からテキスト抽出用

router = APIRouter()

UPLOAD_DIR = "./data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload_and_register")
async def upload_and_register(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    project: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="ファイル名が不正です")

    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "docx", "txt"]:
        raise HTTPException(status_code=400, detail="未対応の形式です")

    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())

    # テキスト抽出（extはオプションなのでファイルパスのみを渡す）
    text = extract_text(save_path)
    if not text:
        raise HTTPException(status_code=400, detail="テキスト抽出に失敗しました")

    # チャンク化
    chunks = split_into_chunks(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="チャンク生成に失敗しました")

    # メタデータ作成
    metadata_list = [{"filename": filename} for _ in chunks]

    # ベクトル化
    vectors = embed_chunks(chunks)
    
    # S3Vectors に登録
    result = add_vectors_to_s3vectors(chunks, vectors, metadata_list)

    # ドキュメントレジストリに登録
    doc_metadata = {
        "title": title or filename,
        "category": category or "",
        "project": project or "",
        "notes": notes or "",
        "file_type": ext,
    }
    document_registry.upsert_document(filename, doc_metadata)

    return {
        "message": "アップロード〜ベクトル登録完了",
        "filename": filename,
        "chunks": len(chunks),
        "registered": result["count"]
    }
