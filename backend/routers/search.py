from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.vector_store import search_kb

# サービス層
from services.vector_store import search_kb  # 関数名を KB 用に変更
from services import activity_log

router = APIRouter()

# ====== リクエスト定義 ======
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

# ====== レスポンス定義 ======
class SearchResult(BaseModel):
    id: str
    score: float
    text: str
    filename: str
    chunk_id: int

# ====== /search API ======
@router.post("/search", response_model=List[SearchResult])
async def search_docs(body: SearchRequest):
    """
    KB検索: 質問テキスト → S3 Vectors へ検索 → 最も近いチャンクを返す
    """
    if not body.query:
        raise HTTPException(status_code=400, detail="query が空です")

    # S3 Vectors でテキスト検索
    results = search_kb(body.query, top_k=body.top_k)


    # 整形して返す
    response_items = []
    for hit in results:
        meta = hit.get("metadata", {})
        response_items.append(SearchResult(
            id=hit.get("id"),
            score=hit.get("score"),
            text=meta.get("text", ""),
            filename=meta.get("filename", ""),
            chunk_id=meta.get("chunk_id", -1)
        ))

    # ログ記録
    activity_log.append_log(
        "search",
        {
            "query": body.query,
            "top_k": body.top_k,
            "result_count": len(response_items),
        },
    )

    return response_items
