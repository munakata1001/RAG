# services/vector_store.py
from typing import List, Dict, Any
import uuid
import json
import os
import logging
from services import embedding
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

VECTOR_BUCKET = os.getenv("VECTOR_BUCKET", "your-s3-bucket-name")  # S3バケット名（環境変数から取得可能）
UPLOAD_DIR = "./data/vector_store"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# S3クライアント（エラー時はNoneになる）
try:
    s3 = boto3.client("s3")
    # 接続テスト（実際の接続は行わない）
    _s3_available = True
except Exception as e:
    logger.warning(f"S3クライアントの初期化に失敗しました。ローカルモードで動作します: {e}")
    s3 = None
    _s3_available = False

# 文書登録
def add_kb_texts(texts: List[str], metadatas: List[Dict[str, Any]]):
    vectors = embedding.embed_chunks(texts)
    return add_kb_vectors(texts, vectors, metadatas)

def add_kb_vectors(chunks: List[str], vectors: List[List[float]], metadatas: List[Dict[str, Any]]):
    docs = []
    s3_upload_success = 0
    s3_upload_failed = 0
    
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        doc_id = str(uuid.uuid4())
        doc = {
            "id": doc_id,
            "vector": vector,
            "metadata": {"text": chunk, **metadatas[i]}
        }
        docs.append(doc)

        # JSONとしてローカル保存
        path = os.path.join(UPLOAD_DIR, f"{doc_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
        
        # S3にアップロード（オプション、失敗しても続行）
        if s3 and _s3_available:
            try:
                s3.upload_file(path, VECTOR_BUCKET, f"vectors/{doc_id}.json")
                s3_upload_success += 1
            except (ClientError, NoCredentialsError, Exception) as e:
                s3_upload_failed += 1
                logger.warning(f"S3へのアップロードに失敗しました（{doc_id}）。ローカル保存のみで続行します: {e}")
        else:
            s3_upload_failed += 1

    message = "登録完了"
    if s3_upload_failed > 0 and s3_upload_success == 0:
        message = "登録完了（ローカル保存のみ、S3は使用していません）"
    elif s3_upload_failed > 0:
        message = f"登録完了（{s3_upload_success}件をS3に保存、{s3_upload_failed}件はローカルのみ）"
    
    return {"message": message, "count": len(docs)}

# S3上のすべてのベクトルを取得（検索用、S3が使えない場合はローカルから読み込み）
def load_all_vectors() -> List[Dict[str, Any]]:
    docs = []
    
    # S3から読み込みを試行
    if s3 and _s3_available:
        try:
            objects = s3.list_objects_v2(Bucket=VECTOR_BUCKET, Prefix="vectors/")
            for obj in objects.get("Contents", []):
                key = obj["Key"]
                resp = s3.get_object(Bucket=VECTOR_BUCKET, Key=key)
                doc = json.loads(resp["Body"].read().decode("utf-8"))
                docs.append(doc)
            logger.info(f"S3から{len(docs)}件のベクトルを読み込みました")
            return docs
        except (ClientError, NoCredentialsError, Exception) as e:
            logger.warning(f"S3からの読み込みに失敗しました。ローカルファイルから読み込みます: {e}")
    
    # ローカルファイルから読み込み
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            if filename.endswith(".json"):
                path = os.path.join(UPLOAD_DIR, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        doc = json.load(f)
                        docs.append(doc)
                except Exception as e:
                    logger.warning(f"ローカルファイルの読み込みに失敗しました（{filename}）: {e}")
    
    logger.info(f"ローカルから{len(docs)}件のベクトルを読み込みました")
    return docs

# 簡易ベクトル検索
def search_kb(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    query_vector = embedding.embed_text(query)
    docs = load_all_vectors()
    
    # コサイン類似度でスコア計算
    def cosine_sim(v1, v2):
        import numpy as np
        v1, v2 = np.array(v1), np.array(v2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10))
    
    scored_docs = [{"id": d["id"], "score": cosine_sim(query_vector, d["vector"]), "metadata": d["metadata"]} for d in docs]
    scored_docs.sort(key=lambda x: x["score"], reverse=True)
    return scored_docs[:top_k]
