"""
デバッグ用エンドポイント
ベクトルストアの状態を確認する
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging

from services.s3vectors_store import _load_all_vectors_from_s3

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/debug/endpoints")
async def get_endpoints() -> Dict[str, Any]:
    """
    登録されているエンドポイント一覧を返す
    """
    from fastapi import Request
    from fastapi.routing import APIRoute
    
    # リクエストオブジェクトからappを取得
    # 注意: この方法は動作しない可能性があるため、別の方法を検討する
    
    return {
        "message": "エンドポイント一覧を取得するには、http://localhost:8000/docs にアクセスしてください",
        "expected_endpoints": [
            "POST /api/rag",
            "POST /api/rag/search",
            "POST /api/search",
            "POST /api/generate",
            "GET /api/debug/vectors",
            "GET /api/debug/endpoints",
            "GET /health"
        ]
    }


@router.get("/debug/vectors")
async def get_vector_store_status() -> Dict[str, Any]:
    """
    ベクトルストアの状態を確認
    """
    try:
        all_vectors = _load_all_vectors_from_s3()
        
        # ファイル名ごとのベクトル数を集計
        filename_counts = {}
        total_text_length = 0
        for doc in all_vectors:
            metadata = doc.get("metadata", {})
            filename = metadata.get("filename", "unknown")
            text = metadata.get("text", "")
            filename_counts[filename] = filename_counts.get(filename, 0) + 1
            total_text_length += len(text)
        
        return {
            "total_vectors": len(all_vectors),
            "unique_files": len(filename_counts),
            "vectors_by_file": filename_counts,
            "total_text_length": total_text_length,
            "sample_metadata": all_vectors[0].get("metadata", {}) if all_vectors else None
        }
    except Exception as e:
        logger.error(f"ベクトルストアの状態取得に失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "total_vectors": 0
        }

