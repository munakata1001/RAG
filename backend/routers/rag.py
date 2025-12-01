# routers/rag.py
"""
S3VectorsベースのRAG（Retrieval-Augmented Generation）エンドポイント
検索と生成を統合したRAGシステム
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import boto3
import json
import os
import logging

from services.s3vectors_store import search_by_text
from services import activity_log

router = APIRouter()
logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
# デフォルトモデルID: 標準版を使用（28k版は別の形式の可能性があるため）
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

bedrock = None
try:
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    logger.info(f"Bedrockクライアントを初期化しました（リージョン: {AWS_REGION}, モデル: {MODEL_ID}）")
except Exception as e:
    logger.warning(f"Bedrockクライアントの初期化に失敗しました: {e}")
    logger.info("Bedrockを使用するには、AWS認証情報とモデルアクセスの設定が必要です。詳細は BEDROCK_SETUP.md を参照してください。")


# ====== リクエスト定義 ======
class RAGRequest(BaseModel):
    query: str
    top_k: int = 5
    max_tokens: int = 2000  # より長い回答を生成できるように増加
    temperature: float = 0.3  # より一貫性のある回答を生成するために下げる


class ContextItem(BaseModel):
    text: str
    score: float
    filename: Optional[str] = None
    metadata: Optional[dict] = None


class RAGResponse(BaseModel):
    answer: str
    contexts: List[ContextItem]
    query: str


# ====== /rag エンドポイント ======
@router.post("/rag", response_model=RAGResponse)
async def rag_search_and_generate(body: RAGRequest):
    """
    S3Vectorsで検索して、検索結果をコンテキストとしてLLMで回答を生成
    """
    try:
        if not body.query:
            raise HTTPException(status_code=400, detail="query が空です")
        
        logger.info(f"RAG検索開始: query='{body.query}', top_k={body.top_k}")
        
        # 1. S3Vectorsで類似検索
        try:
            search_results = search_by_text(body.query, top_k=body.top_k)
            logger.info(f"検索結果: {len(search_results)}件")
            if search_results:
                logger.info(f"検索結果のサンプル: {search_results[0] if search_results else 'なし'}")
        except Exception as e:
            logger.error(f"検索エラー: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"検索に失敗しました: {str(e)}")
        
        if not search_results:
            logger.warning("検索結果が空です。ベクトルストアにデータが登録されているか確認してください。")
            # ベクトルストアの状態を確認
            from services.s3vectors_store import _load_all_vectors_from_s3
            all_vectors = _load_all_vectors_from_s3()
            logger.info(f"ベクトルストア内のベクトル数: {len(all_vectors)}件")
            raise HTTPException(
                status_code=404,
                detail=f"検索結果が見つかりませんでした。ベクトルストア内のベクトル数: {len(all_vectors)}件。ドキュメントをアップロードしてください。"
            )
        
        # 2. コンテキストを整形（重複を排除）
        contexts = []
        context_texts = []
        seen_texts = set()  # 重複チェック用
        
        for i, result in enumerate(search_results):
            try:
                metadata = result.get("metadata", {})
                text = metadata.get("text", "").strip()
                filename = metadata.get("filename", "")
                
                logger.debug(f"検索結果{i+1}: filename={filename}, text_length={len(text) if text else 0}, score={result.get('score', 0.0)}")
                
                if not text:
                    logger.warning(f"検索結果{i+1}のテキストが空です。metadata={metadata}")
                    continue
                
                # 重複チェック（テキストの最初の100文字で判定）
                text_key = text[:100] if len(text) > 100 else text
                if text_key in seen_texts:
                    logger.debug(f"検索結果{i+1}は重複のためスキップします")
                    continue
                seen_texts.add(text_key)
                
                contexts.append(ContextItem(
                    text=text,
                    score=result.get("score", 0.0),
                    filename=filename,
                    metadata=metadata
                ))
                # コンテキストテキストを追加（ファイル名情報は含めない）
                context_texts.append(text)
            except Exception as e:
                logger.warning(f"検索結果{i+1}の処理に失敗: {e}", exc_info=True)
                continue
        
        if not contexts:
            raise HTTPException(
                status_code=404,
                detail="有効なコンテキストが見つかりませんでした。"
            )
        
        # コンテキストを統合（区切り文字は最小限に）
        context_text = "\n\n".join(context_texts)
        logger.info(f"コンテキスト準備完了: {len(contexts)}件（重複除外後）")
        
        # 3. LLMで回答生成
        answer = ""
        if bedrock:
            try:
                # システムプロンプトで回答の品質を向上
                system_prompt = """あなたは専門的な知識を提供するアシスタントです。
ユーザーの質問に対して、提供されたコンテキスト情報を基に、自然で読みやすい文章形式で回答してください。

回答の要件:
1. 質問に対する直接的な回答を最初に明確に述べる
2. その後、必要に応じて詳細な説明を追加する
3. 自然な日本語で文章として回答する（箇条書きや断片的な情報の羅列は避ける）
4. 複数のコンテキストがある場合は、それらを統合して一貫性のある回答を作成する
5. コンテキストにない情報は推測せず、事実のみを述べる
6. 情報が見つからない場合は、「コンテキスト情報から該当する情報が見つかりませんでした」と明確に伝える
7. 回答は明確で分かりやすく、読み手が理解しやすい形式にする"""
                
                user_prompt = f"""以下のコンテキスト情報を基に、ユーザーの質問に回答してください。

## コンテキスト情報

{context_text}

## 質問

{body.query}

## 回答

質問に対する回答を、自然な日本語の文章形式で作成してください。まず質問に対する直接的な回答を述べ、その後必要に応じて詳細を説明してください。"""
                
                prompt = user_prompt
                
                # Claude 3のメッセージ形式を使用
                messages = [
                    {"role": "user", "content": prompt}
                ]
                
                # システムプロンプトを追加（Claude 3ではsystemパラメータを使用）
                payload = {
                    "modelId": MODEL_ID,
                    "contentType": "application/json",
                    "accept": "*/*",
                    "body": json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": body.max_tokens,
                        "temperature": min(body.temperature, 0.9),  # 温度を0.9以下に制限して一貫性を保つ
                        "system": system_prompt,
                        "messages": messages
                    })
                }
                
                logger.info(f"Bedrock呼び出し開始: model={MODEL_ID}")
                response = bedrock.invoke_model(**payload)
                response_body = response["body"].read()
                model_response = json.loads(response_body)
                
                # レスポンス形式の確認と処理
                if "content" in model_response and len(model_response["content"]) > 0:
                    answer = model_response["content"][0].get("text", "")
                elif "text" in model_response:
                    answer = model_response["text"]
                else:
                    logger.warning(f"予期しないレスポンス形式: {model_response}")
                    answer = _generate_simple_answer(body.query, context_texts)
                
                if not answer or len(answer.strip()) == 0:
                    logger.warning("Bedrockからの回答が空です。フォールバック回答を生成します。")
                    answer = _generate_simple_answer(body.query, context_texts)
                else:
                    logger.info(f"Bedrock回答生成完了: {len(answer)}文字")
            except Exception as e:
                error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
                error_message = getattr(e, "response", {}).get("Error", {}).get("Message", str(e))
                
                logger.error(f"LLM生成エラー: {error_code} - {error_message}", exc_info=True)
                
                # エラーの種類に応じた詳細なログ
                if error_code == "UnrecognizedClientException":
                    logger.error("認証情報が無効です。.envファイルまたはAWS認証情報を確認してください。")
                elif error_code == "AccessDeniedException":
                    logger.error("IAM権限が不足しています。AmazonBedrockFullAccessを付与してください。")
                    logger.error("または、初回使用時の使用目的提出が必要な可能性があります。")
                elif error_code == "ValidationException":
                    logger.error(f"モデルIDまたはリクエスト形式が不正です。モデルID: {MODEL_ID}, リージョン: {AWS_REGION}")
                
                # Bedrockエラー時は、検索結果から簡易的な回答を生成
                answer = _generate_simple_answer(body.query, context_texts)
        else:
            logger.info("Bedrockが利用できないため、検索結果から簡易的な回答を生成します")
            # Bedrockが利用できない場合、検索結果から簡易的な回答を生成
            answer = _generate_simple_answer(body.query, context_texts)
        
        # 4. ログ記録
        try:
            activity_log.append_log(
                "rag",
                {
                    "query": body.query,
                    "top_k": body.top_k,
                    "context_count": len(contexts),
                    "answer_length": len(answer),
                },
            )
        except Exception as e:
            logger.warning(f"ログ記録に失敗: {e}")
        
        return RAGResponse(
            answer=answer,
            contexts=contexts,
            query=body.query
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG処理で予期しないエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG処理に失敗しました: {str(e)}")


def _generate_simple_answer(query: str, context_texts: List[str]) -> str:
    """
    Bedrockが利用できない場合、検索結果から簡易的な回答を生成
    注意: この関数は簡易的な回答のみを生成します。より高品質な回答にはBedrockが必要です。
    """
    if not context_texts:
        return "検索結果が見つかりませんでした。ドキュメントをアップロードしてください。"
    
    # 質問に対する直接的な回答を抽出
    # 最初のコンテキストから質問に関連する情報を探す
    first_context = context_texts[0] if context_texts else ""
    
    # 質問のキーワードを抽出（簡単な方法）
    query_lower = query.lower()
    
    # 質問が「どこ」「出身」「場所」などを含む場合
    if any(keyword in query_lower for keyword in ["どこ", "出身", "場所", "所在地"]):
        # コンテキストから地名や場所を探す
        location_keywords = ["出身", "県", "市", "都", "道", "府", "区", "町", "村"]
        for context in context_texts:
            for keyword in location_keywords:
                if keyword in context:
                    # キーワード周辺のテキストを抽出
                    idx = context.find(keyword)
                    if idx >= 0:
                        start = max(0, idx - 50)
                        end = min(len(context), idx + 100)
                        relevant_text = context[start:end]
                        return f"質問「{query}」について、コンテキスト情報から以下の情報が見つかりました：\n\n{relevant_text}\n\n※ より詳細な回答には、Bedrockの設定が必要です。"
    
    # デフォルトの回答
    return f"質問「{query}」について、コンテキスト情報から関連する情報が見つかりましたが、より自然な回答を生成するにはBedrockの設定が必要です。\n\n関連情報:\n{first_context[:500]}..."


# ====== /rag/search エンドポイント（検索のみ） ======
@router.post("/rag/search")
async def rag_search_only(body: RAGRequest):
    """
    S3Vectorsで検索のみを実行（生成なし）
    """
    if not body.query:
        raise HTTPException(status_code=400, detail="query が空です")
    
    try:
        search_results = search_by_text(body.query, top_k=body.top_k)
    except Exception as e:
        logger.error(f"検索エラー: {e}")
        raise HTTPException(status_code=500, detail=f"検索に失敗しました: {str(e)}")
    
    contexts = []
    for result in search_results:
        metadata = result.get("metadata", {})
        contexts.append(ContextItem(
            text=metadata.get("text", ""),
            score=result.get("score", 0.0),
            filename=metadata.get("filename", ""),
            metadata=metadata
        ))
    
    return {
        "query": body.query,
        "contexts": contexts
    }

