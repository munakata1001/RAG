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
import time
from botocore.exceptions import ClientError

from services.s3vectors_store import search_by_text
from services import activity_log

router = APIRouter()
logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
# デフォルトモデルID: Claude 3.5 Sonnetを使用（on-demand対応）
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")

# 人物名リスト（コンテキストフィルタリングと識別用）
CHARACTER_NAMES = ["乙骨憂太", "五条悟", "虎杖悠仁", "伏黒恵", "釘崎野薔薇", ]

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
    max_tokens: int = 3000  # より詳細な回答を生成できるように増加
    temperature: float = 0.2  # より一貫性と正確性を重視（0.2-0.3が最適）


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
        
        # 質問に含まれる人物名を抽出（コンテキストフィルタリング用）
        query_characters = [char for char in CHARACTER_NAMES if char in body.query]
        
        # コンテキストをスコア順にソート（高スコアが先頭）
        contexts_with_scores = list(zip(contexts, context_texts))
        contexts_with_scores.sort(key=lambda x: x[0].score, reverse=True)
        
        # 質問に人物名が含まれている場合、その人物を含むコンテキストを優先
        if query_characters:
            def context_priority(ctx_text_pair):
                ctx, text = ctx_text_pair
                # 質問に含まれる人物名がコンテキストに含まれている場合、優先度を上げる
                priority = ctx.score
                for char in query_characters:
                    if char in text:
                        priority += 0.1  # 人物名が含まれるコンテキストにボーナス
                return priority
            
            # 優先度順に再ソート
            contexts_with_scores.sort(key=context_priority, reverse=True)
            logger.info(f"質問に含まれる人物名（{', '.join(query_characters)}）に基づいてコンテキストを優先順位付けしました")
        
        # スコアの分布を確認
        if contexts_with_scores:
            scores = [ctx.score for ctx, _ in contexts_with_scores]
            max_score = max(scores)
            min_score = min(scores)
            avg_score = sum(scores) / len(scores)
            logger.info(f"コンテキストスコア分布: 最大={max_score:.3f}, 最小={min_score:.3f}, 平均={avg_score:.3f}, 件数={len(scores)}")
        
        # 低スコアのコンテキストをフィルタリング（動的閾値を使用）
        # スコアが非常に低い場合（平均が0.3未満）は、閾値を下げる
        if contexts_with_scores:
            scores = [ctx.score for ctx, _ in contexts_with_scores]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # 動的閾値: 平均スコアが低い場合は、より低い閾値を使用
            if avg_score < 0.3:
                # 平均スコアが低い場合、最小スコアの50%を閾値として使用
                min_score_threshold = min(0.15, min(scores) * 0.5) if scores else 0.1
                logger.info(f"平均スコアが低いため、動的閾値を使用: {min_score_threshold:.3f}")
            else:
                # 通常の閾値
                min_score_threshold = 0.2
        else:
            min_score_threshold = 0.2
        
        filtered_contexts = [(ctx, text) for ctx, text in contexts_with_scores if ctx.score >= min_score_threshold]
        
        if not filtered_contexts:
            # フィルタリング後にコンテキストがなくなった場合は、上位N件を使用
            # スコアに関係なく、上位5件を使用
            top_n = min(5, len(contexts_with_scores))
            filtered_contexts = contexts_with_scores[:top_n]
            logger.warning(f"スコアフィルタリング後にコンテキストがなくなったため、上位{top_n}件のコンテキストを使用します")
            if contexts_with_scores:
                logger.info(f"使用するコンテキストのスコア範囲: {min([ctx.score for ctx, _ in filtered_contexts]):.3f} ～ {max([ctx.score for ctx, _ in filtered_contexts]):.3f}")
        else:
            removed_count = len(contexts_with_scores) - len(filtered_contexts)
            if removed_count > 0:
                logger.info(f"低スコアコンテキスト{removed_count}件を除外しました（閾値: {min_score_threshold:.3f}）")
            logger.info(f"使用するコンテキスト: {len(filtered_contexts)}件（スコア範囲: {min([ctx.score for ctx, _ in filtered_contexts]):.3f} ～ {max([ctx.score for ctx, _ in filtered_contexts]):.3f}）")
        
        # コンテキストが存在することを確認
        if not filtered_contexts:
            logger.error("フィルタリング後にコンテキストが存在しません")
            raise HTTPException(
                status_code=404,
                detail="検索結果が見つかりませんでした。ドキュメントをアップロードしてください。"
            )
        
        # コンテキストを構造化して統合（スコア情報と番号を付与、人物名を検出）
        context_parts = []
        for idx, (ctx, text) in enumerate(filtered_contexts, 1):
            # スコアが高いコンテキストを強調
            relevance_note = ""
            if ctx.score > 0.8:
                relevance_note = "【高関連度】"
            elif ctx.score > 0.6:
                relevance_note = "【中関連度】"
            
            # コンテキスト内に含まれる人物名を検出
            mentioned_in_context = []
            for char_name in CHARACTER_NAMES:
                if char_name in text:
                    mentioned_in_context.append(char_name)
            
            character_note = ""
            if mentioned_in_context:
                character_note = f"【関連人物: {', '.join(mentioned_in_context)}】"
            
            filename_note = f"（出典: {ctx.filename}）" if ctx.filename else ""
            # スコア情報も含める（デバッグ用、必要に応じて削除可能）
            score_note = f"（関連度スコア: {ctx.score:.2f}）"
            
            context_header = f"[コンテキスト{idx}] {relevance_note} {score_note}"
            if character_note:
                context_header += f" {character_note}"
            
            context_parts.append(f"{context_header}\n{text}\n{filename_note}")
        
        context_text = "\n\n".join(context_parts)
        logger.info(f"コンテキスト準備完了: {len(filtered_contexts)}件（重複除外後、スコア順、フィルタリング済み）")
        
        # 3. LLMで回答生成
        answer = ""
        if bedrock:
            try:
                # 改善されたシステムプロンプト（人物情報の正確な識別を重視）
                system_prompt = """あなたは専門的な知識を提供するアシスタントです。ユーザーの質問に対して、提供されたコンテキスト情報を基に、高品質で自然な回答を生成してください。

## 回答の品質要件

### 1. 回答の構造
- **結論を最初に**: 質問に対する直接的な回答を最初の1-2文で明確に述べる
- **詳細説明**: その後、コンテキスト情報を基に詳細な説明を追加する
- **補足情報**: 必要に応じて、関連する重要な情報を補足する

### 2. 情報の扱い方（重要）
- **必ず回答を生成**: コンテキスト情報が提供されている場合は、必ずその情報を基に回答を生成してください。コンテキストが存在する限り、必ず回答を提供してください
- **禁止表現**: 以下のような表現は絶対に使用しないでください：
  - 「情報が見つかりませんでした」
  - 「情報がありません」
  - 「見当たりません」
  - 「明確ではありません」
  - 「確認できません」
  - 「具体的な記述が見当たりません」
  - 「関連しているかどうかは明確ではありません」
  - 「可能性が高い」
  - 「推測できます」
  - 「かもしれない」
  - 「可能性があります」
  - 「推測すると」
  - 「おそらく」
  - 「〜と推測されます」
- **事実のみを使用**: コンテキストに記載されている事実のみを使用してください。推測、憶測、可能性の話は一切含めないでください
- **積極的な情報抽出**: コンテキストに記載されている情報を積極的に抽出し、質問に関連する情報があれば必ず回答に含めてください
- **関連情報の活用**: コンテキストに質問の人物名やキーワードが含まれていなくても、関連する情報（術式、式神、能力、世界観など）がコンテキストに記載されていれば、それを基に回答を生成してください
- **事実ベース**: コンテキストに記載されている事実のみを使用して回答します。コンテキストに記載されていない情報は含めないでください
- **複数コンテキストの統合**: 複数のコンテキストがある場合、それらを矛盾なく統合して一貫性のある回答を作成する
- **関連度の考慮**: 【高関連度】とマークされたコンテキストを優先的に参照するが、すべてのコンテキストから有用な情報を抽出してください

### 3. 人物情報の正確な識別と区別（重要）
- **人物名の明確な識別**: 質問に複数の人物名が含まれる場合、各人物についての情報を明確に区別して回答する
- **コンテキストとの照合**: 各コンテキストがどの人物についての情報かを正確に識別し、人物を混同しない
- **情報の分離**: 異なる人物の情報を混同したり、一人の人物の情報を別の人物に帰属させたりしない
- **人物ごとの整理**: 複数の人物について質問された場合、各人物についての情報を明確に分けて記述する
- **積極的な情報抽出**: コンテキストに人物名や関連情報が含まれている場合は、積極的にその情報を抽出して回答に含めてください

### 4. 文章の品質
- **自然な日本語**: 読みやすく、自然な日本語で文章として記述する（箇条書きの羅列は避ける）
- **明確性**: 専門用語を使う場合は、必要に応じて簡潔な説明を加える
- **簡潔性**: 冗長な表現を避け、要点を明確に伝える
- **論理性**: 回答の流れが論理的で、読み手が理解しやすい構造にする

### 5. 出典の扱い
- コンテキストにファイル名が含まれている場合は、必要に応じて参照元を示すことができるが、回答の自然さを優先する"""
                
                # 質問に含まれる人物名を抽出（簡易的な方法）
                mentioned_characters = [char for char in CHARACTER_NAMES if char in body.query]
                
                character_instruction = ""
                if len(mentioned_characters) > 1:
                    character_instruction = f"""

## 重要な注意事項
質問には以下の人物が含まれています: {', '.join(mentioned_characters)}
- 各人物についての情報を**明確に区別**して回答してください
- 一人の人物の情報を別の人物に帰属させないでください
- 各コンテキストがどの人物についての情報かを正確に識別してください
- 複数の人物について質問されている場合、各人物ごとに情報を整理して回答してください
"""
                elif len(mentioned_characters) == 1:
                    character_instruction = f"""

## 重要な注意事項
質問は「{mentioned_characters[0]}」についてのものです。
- この人物についての情報を積極的に抽出してください
- この人物名が直接記載されていなくても、関連する情報（術式、式神、能力など）があれば、それを基に回答を生成してください
- 他の人物の情報と混同しないでください
- コンテキストに記載されている情報を最大限活用して回答してください
"""
                
                user_prompt = f"""以下のコンテキスト情報を基に、ユーザーの質問に回答してください。

## コンテキスト情報

{context_text}
{character_instruction}
## 質問

{body.query}

## 重要な指示（必須遵守）

**コンテキスト情報が提供されているため、必ずその情報を基に回答を生成してください。**

### 禁止事項（絶対に使用しないでください）
以下のような表現や回答は絶対に使用しないでください：
- 「情報が見つかりませんでした」
- 「情報がありません」
- 「見当たりません」
- 「明確ではありません」
- 「確認できません」
- 「具体的な記述が見当たりません」
- 「関連しているかどうかは明確ではありません」
- 「コンテキストからは確認できません」
- 「可能性が高い」
- 「推測できます」
- 「かもしれない」
- 「可能性があります」
- 「推測すると」
- 「おそらく」
- 「〜と推測されます」
- 「〜の可能性が高いと推測できます」

### 必須事項
- **事実のみを使用**: コンテキストに記載されている事実のみを使用してください。推測、憶測、可能性の話は一切含めないでください
- コンテキストに記載されている情報を積極的に抽出し、質問に関連する情報があれば必ず回答に含めてください
- 質問の人物名やキーワードがコンテキストに直接含まれていなくても、関連する情報（術式、式神、能力、世界観など）がコンテキストに記載されていれば、それを基に回答を生成してください
- コンテキストに記載されている内容から、質問に関連する情報を抽出して回答してください
- コンテキストが提供されている限り、必ず何らかの回答を提供してください
- 「情報が不足している」というような言い訳はせず、利用可能な情報を最大限活用して回答してください
- **推測は禁止**: コンテキストに記載されていない情報を推測したり、可能性の話をしたりしないでください

## 回答

上記のコンテキスト情報を基に、以下の形式で回答を作成してください：

1. **結論**: 質問に対する直接的な回答（1-2文）
   - コンテキストから抽出した情報を基に、明確に回答してください
   - 禁止表現は絶対に使用しないでください
   - 推測や可能性の話は一切含めないでください
2. **詳細説明**: コンテキスト情報を基にした詳細な説明
   - 複数の人物について質問されている場合、各人物ごとに明確に分けて記述してください
   - 各人物の情報を混同しないよう、注意深くコンテキストを参照してください
   - コンテキストに記載されている情報を積極的に活用してください
   - 関連する情報（術式、式神、能力など）がコンテキストに記載されていれば、それを基に回答を生成してください
   - **重要**: コンテキストに記載されている事実のみを使用してください。推測、憶測、可能性の話は一切含めないでください
3. **補足情報**: 関連する重要な情報があれば追加
   - コンテキストに記載されている情報のみを使用してください

回答は自然な日本語の文章形式で、読みやすく明確に記述してください。
**特に、コンテキスト情報を積極的に活用し、必ず回答を提供してください。禁止表現は絶対に使用しないでください。推測や可能性の話は一切含めないでください。コンテキストに記載されている事実のみを使用してください。**"""
                
                prompt = user_prompt
                
                # Claude 3のメッセージ形式を使用
                messages = [
                    {"role": "user", "content": prompt}
                ]
                
                # コンテキストの長さを適切に制限（トークン数の目安: 1文字 ≈ 0.25トークン）
                # 長すぎるコンテキストは最初の部分を優先
                max_context_length = 8000  # 約2000トークン分のコンテキスト
                if len(context_text) > max_context_length:
                    logger.warning(f"コンテキストが長すぎるため、最初の{max_context_length}文字を使用します")
                    context_text = context_text[:max_context_length] + "\n\n[注: コンテキストが長いため、最初の部分のみを使用しています]"
                    # user_promptを再構築（同じ指示を含める）
                    user_prompt = f"""以下のコンテキスト情報を基に、ユーザーの質問に回答してください。

## コンテキスト情報

{context_text}
{character_instruction}
## 質問

{body.query}

## 重要な指示（必須遵守）

**コンテキスト情報が提供されているため、必ずその情報を基に回答を生成してください。**

### 禁止事項（絶対に使用しないでください）
以下のような表現や回答は絶対に使用しないでください：
- 「情報が見つかりませんでした」
- 「情報がありません」
- 「見当たりません」
- 「明確ではありません」
- 「確認できません」
- 「具体的な記述が見当たりません」
- 「関連しているかどうかは明確ではありません」
- 「コンテキストからは確認できません」
- 「可能性が高い」
- 「推測できます」
- 「かもしれない」
- 「可能性があります」
- 「推測すると」
- 「おそらく」
- 「〜と推測されます」
- 「〜の可能性が高いと推測できます」

### 必須事項
- **事実のみを使用**: コンテキストに記載されている事実のみを使用してください。推測、憶測、可能性の話は一切含めないでください
- コンテキストに記載されている情報を積極的に抽出し、質問に関連する情報があれば必ず回答に含めてください
- 質問の人物名やキーワードがコンテキストに直接含まれていなくても、関連する情報（術式、式神、能力、世界観など）がコンテキストに記載されていれば、それを基に回答を生成してください
- コンテキストに記載されている内容から、質問に関連する情報を抽出して回答してください
- コンテキストが提供されている限り、必ず何らかの回答を提供してください
- 「情報が不足している」というような言い訳はせず、利用可能な情報を最大限活用して回答してください
- **推測は禁止**: コンテキストに記載されていない情報を推測したり、可能性の話をしたりしないでください

## 回答

上記のコンテキスト情報を基に、以下の形式で回答を作成してください：

1. **結論**: 質問に対する直接的な回答（1-2文）
   - コンテキストから抽出した情報を基に、明確に回答してください
   - 禁止表現は絶対に使用しないでください
   - 推測や可能性の話は一切含めないでください
2. **詳細説明**: コンテキスト情報を基にした詳細な説明
   - 複数の人物について質問されている場合、各人物ごとに明確に分けて記述してください
   - 各人物の情報を混同しないよう、注意深くコンテキストを参照してください
   - コンテキストに記載されている情報を積極的に活用してください
   - 関連する情報（術式、式神、能力など）がコンテキストに記載されていれば、それを基に回答を生成してください
   - **重要**: コンテキストに記載されている事実のみを使用してください。推測、憶測、可能性の話は一切含めないでください
3. **補足情報**: 関連する重要な情報があれば追加
   - コンテキストに記載されている情報のみを使用してください

回答は自然な日本語の文章形式で、読みやすく明確に記述してください。
**特に、コンテキスト情報を積極的に活用し、必ず回答を提供してください。禁止表現は絶対に使用しないでください。推測や可能性の話は一切含めないでください。コンテキストに記載されている事実のみを使用してください。**"""
                    messages = [
                        {"role": "user", "content": user_prompt}
                    ]
                
                # 温度パラメータを最適化（0.1-0.3の範囲で一貫性と正確性を重視）
                optimized_temperature = max(0.1, min(body.temperature, 0.5))
                
                # システムプロンプトを追加（Claude 3ではsystemパラメータを使用）
                payload = {
                    "modelId": MODEL_ID,
                    "contentType": "application/json",
                    "accept": "*/*",
                    "body": json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": min(body.max_tokens, 4000),  # 最大4000トークンに制限
                        "temperature": optimized_temperature,
                        "system": system_prompt,
                        "messages": messages
                    })
                }
                
                logger.info(f"Bedrock呼び出し開始: model={MODEL_ID}")
                
                # リトライロジック（指数バックオフ）
                max_retries = 5
                base_delay = 1  # 初期待機時間（秒）
                max_delay = 60  # 最大待機時間（秒）
                
                response = None
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        response = bedrock.invoke_model(**payload)
                        if attempt > 0:
                            logger.info(f"リトライ成功（試行{attempt + 1}/{max_retries}）")
                        break  # 成功したらループを抜ける
                    except ClientError as e:
                        error_code = e.response.get("Error", {}).get("Code", "Unknown")
                        error_message = e.response.get("Error", {}).get("Message", str(e))
                        last_error = e
                        
                        # ThrottlingExceptionとServiceUnavailableExceptionの場合はリトライ
                        if error_code in ["ThrottlingException", "ServiceUnavailableException"]:
                            if attempt < max_retries - 1:
                                # 指数バックオフ: 2^attempt * base_delay秒待機
                                delay = min(base_delay * (2 ** attempt), max_delay)
                                logger.warning(f"{error_code}発生（試行{attempt + 1}/{max_retries}）。{delay}秒待機してリトライします...")
                                time.sleep(delay)
                                continue
                            else:
                                # 最大リトライ回数に達した場合
                                logger.error(f"{error_code}: 最大リトライ回数（{max_retries}回）に達しました。しばらく待ってから再度お試しください。")
                                raise
                        else:
                            # リトライ対象外のエラーはそのまま再スロー
                            raise
                    except Exception as e:
                        # ClientError以外のエラーはそのまま再スロー
                        last_error = e
                        raise
                
                if response is None:
                    raise last_error if last_error else Exception("Bedrock呼び出しに失敗しました")
                
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
                if error_code == "ThrottlingException":
                    logger.error("レート制限に達しました。しばらく待ってから再度お試しください。")
                    logger.error("複数のリクエストを短時間に送信している可能性があります。")
                elif error_code == "ServiceUnavailableException":
                    logger.error("Bedrockサービスが一時的に利用できません。しばらく待ってから再度お試しください。")
                    logger.error("サービスが復旧するまで、自動的にリトライされます。")
                elif error_code == "UnrecognizedClientException":
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
    注意: この関数は簡易的な回答のみを生成します。
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
                        return f"質問「{query}」について、コンテキスト情報から以下の情報が見つかりました：\n\n{relevant_text}"
    
    # デフォルトの回答
    return f"質問「{query}」について、コンテキスト情報から関連する情報が見つかりました。\n\n関連情報:\n{first_context[:500]}..."


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

