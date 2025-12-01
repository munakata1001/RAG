# routers/usage_logs.py
"""
使用ログ取得エンドポイント
"""
from fastapi import APIRouter
from services import activity_log

router = APIRouter()


@router.get("/usage_logs")
async def get_usage_logs(limit: int = 200):
    """
    使用ログを取得
    """
    logs = activity_log.read_logs(limit=limit)
    return {"logs": logs}

