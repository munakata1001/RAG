# routers/bedrock_kb.py
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
router = APIRouter()

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
KB_ID = os.getenv("KB_ID")

# Bedrock runtime client for retrieve_and_generate
bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

class KBQuery(BaseModel):
    question: str
    session_id: str | None = None  # optional: reuse for multi-turn

@router.post("/api/kb/query")
def query_kb(q: KBQuery):
    if not KB_ID:
        raise HTTPException(status_code=500, detail="KB_ID not configured")

    payload = {
        "knowledgeBaseId": KB_ID,
        "input": {"text": q.question}
    }
    if q.session_id:
        payload["sessionId"] = q.session_id

    try:
        resp = bedrock_runtime.retrieve_and_generate(**payload)
        # 典型レスポンスの構造から抜き出し（必要に応じて調整）
        output = resp.get("output", {})
        text = output.get("text") or output.get("results", [{}])[0].get("text")
        session_id = resp.get("sessionId")
        return {"answer": text, "session_id": session_id, "raw": resp}
    except ClientError as e:
        logger.exception("retrieve_and_generate failed")
        raise HTTPException(status_code=500, detail=f"KB query failed: {e}")
