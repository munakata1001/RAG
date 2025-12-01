from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import boto3  # pyright: ignore[reportMissingImports]
import json
import os

from services import activity_log

router = APIRouter()

AWS_REGION = "ap-northeast-1"
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"   # Claude 3 Sonnet 例

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


# ====== リクエスト定義 ======
class ContextItem(BaseModel):
    text: str
    score: float = None
    filename: str = None
    chunk_id: int = None


class GenerateRequest(BaseModel):
    query: str
    contexts: List[ContextItem]


# ====== レスポンス定義 ======
class GenerateResponse(BaseModel):
    answer: str


# ====== /generate ======
@router.post("/generate", response_model=GenerateResponse)
async def generate_answer(body: GenerateRequest):
    """
    RAG で検索したチャンク（contexts）と質問（query）をもとに
    LLM で回答を生成する
    """

    if not body.query:
        raise HTTPException(status_code=400, detail="query が空です")

    if not body.contexts:
        raise HTTPException(status_code=400, detail="contexts が空です")

    # --- ① プロンプト組み立て ---
    context_text = "\n\n".join(
        [f"[{i+1}] {c.text}" for i, c in enumerate(body.contexts)]
    )

    prompt = f"""
あなたはユーザーの質問に対して、以下のコンテキスト（情報）を基に正確に回答する RAG アシスタントです。

### コンテキスト
{context_text}

### 質問
{body.query}

### 回答ルール
- コンテキストに基づいてのみ回答してください
- コンテキストにない情報は推測しない
- 事実のみ簡潔に説明する

### 回答
"""

    # --- ② LLM に投げる ---
    payload = {
        "modelId": MODEL_ID,
        "contentType": "application/json",
        "accept": "*/*",
        "body": json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    }

    response = bedrock.invoke_model(**payload)

    # --- ③ レスポンス抽出 ---
    model_response = json.loads(response["body"].read())
    answer = model_response["content"][0]["text"]

    activity_log.append_log(
        "generate",
        {
            "query": body.query,
            "context_count": len(body.contexts),
            "answer_length": len(answer),
        },
    )

    return GenerateResponse(answer=answer)
