# services/s3vectors_store.py
"""
S3Vectorsベースのベクトルストアサービス
S3にベクトルデータを保存し、類似検索を実行する
"""
from typing import List, Dict, Any, Optional
import uuid
import json
import os
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import numpy as np

from services import embedding

logger = logging.getLogger(__name__)

# 環境変数から設定を取得
VECTOR_BUCKET = os.getenv("VECTOR_BUCKET", "your-s3-bucket-name")
VECTOR_INDEX = os.getenv("VECTOR_INDEX", "company-rag-embeddings-poc")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
UPLOAD_DIR = "./data/vector_store"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# S3クライアント
s3 = None
_s3_available = False

def _init_s3_client():
    """S3クライアントを初期化（リトライ可能）"""
    global s3, _s3_available
    try:
        # 環境変数から認証情報を取得（設定されていない場合はデフォルトの認証情報を使用）
        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            # 認証情報は環境変数またはデフォルトの認証情報チェーンから自動取得
        )
        # 接続テスト（バケットの存在確認は行わない、クライアントの初期化のみ）
        _s3_available = True
        logger.info(f"S3クライアントを初期化しました（リージョン: {AWS_REGION}）")
        return True
    except Exception as e:
        logger.warning(f"S3クライアントの初期化に失敗しました。ローカルモードで動作します: {e}")
        logger.info("S3を使用するには、AWS認証情報を設定してください（環境変数または~/.aws/credentials）")
        s3 = None
        _s3_available = False
        return False

# 初期化を実行
_init_s3_client()


def add_vectors_to_s3vectors(
    texts: List[str],
    vectors: List[List[float]],
    metadatas: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    S3Vectorsにベクトルを追加
    S3にベクトルデータを保存し、メタデータと共に管理する
    """
    global s3, _s3_available
    
    if len(texts) != len(vectors) or len(texts) != len(metadatas):
        raise ValueError("texts, vectors, metadatas の長さが一致しません")
    
    docs = []
    s3_upload_success = 0
    s3_upload_failed = 0
    
    for i, (text, vector, metadata) in enumerate(zip(texts, vectors, metadatas)):
        doc_id = str(uuid.uuid4())
        doc = {
            "id": doc_id,
            "vector": vector,
            "metadata": {
                "text": text,
                **metadata
            }
        }
        docs.append(doc)
        
        # ローカルに保存
        local_path = os.path.join(UPLOAD_DIR, f"{doc_id}.json")
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
        
        # S3にアップロード
        if s3 and _s3_available:
            try:
                s3_key = f"{VECTOR_INDEX}/{doc_id}.json"
                s3.upload_file(local_path, VECTOR_BUCKET, s3_key)
                s3_upload_success += 1
                logger.debug(f"S3にベクトルをアップロード: {s3_key}")
            except (ClientError, NoCredentialsError) as e:
                s3_upload_failed += 1
                error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
                if error_code == "InvalidAccessKeyId" or error_code == "SignatureDoesNotMatch":
                    logger.warning(f"S3認証エラー: AWS認証情報を確認してください")
                else:
                    logger.warning(f"S3へのアップロードに失敗しました（{doc_id}）: {e}")
                # 認証エラーの場合は、S3接続を無効化して再試行しない
                if error_code in ["InvalidAccessKeyId", "SignatureDoesNotMatch", "NoCredentialsError"]:
                    _s3_available = False
            except Exception as e:
                s3_upload_failed += 1
                logger.warning(f"S3へのアップロードに失敗しました（{doc_id}）: {e}")
        else:
            # S3が利用できない場合は、再初期化を試みる
            if not _s3_available:
                _init_s3_client()
                if s3 and _s3_available:
                    try:
                        s3_key = f"{VECTOR_INDEX}/{doc_id}.json"
                        s3.upload_file(local_path, VECTOR_BUCKET, s3_key)
                        s3_upload_success += 1
                        logger.info(f"S3接続が復旧し、ベクトルをアップロードしました: {s3_key}")
                    except Exception as e:
                        s3_upload_failed += 1
                        logger.warning(f"S3へのアップロードに失敗しました（{doc_id}）: {e}")
                else:
                    s3_upload_failed += 1
            else:
                s3_upload_failed += 1
    
    message = "登録完了"
    if s3_upload_failed > 0 and s3_upload_success == 0:
        message = "登録完了（ローカル保存のみ、S3は使用していません）"
    elif s3_upload_failed > 0:
        message = f"登録完了（{s3_upload_success}件をS3に保存、{s3_upload_failed}件はローカルのみ）"
    
    return {
        "message": message,
        "count": len(docs),
        "s3_uploaded": s3_upload_success,
        "local_only": s3_upload_failed
    }


def search_s3vectors(
    query_vector: List[float],
    top_k: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    S3Vectorsで類似ベクトルを検索
    コサイン類似度を使用して最も類似したベクトルを返す
    """
    try:
        if not query_vector:
            logger.error("クエリベクトルが空です")
            return []
        
        if not isinstance(query_vector, list):
            logger.error(f"クエリベクトルの型が不正です: {type(query_vector)}")
            return []
        
        all_docs = _load_all_vectors_from_s3()
        
        if not all_docs:
            logger.warning("検索対象のベクトルがありません")
            return []
        
        logger.info(f"検索対象: {len(all_docs)}件のベクトル")
        
        # コサイン類似度を計算
        try:
            query_vec = np.array(query_vector, dtype=np.float32)
        except Exception as e:
            logger.error(f"クエリベクトルの変換に失敗: {e}")
            return []
        
        if len(query_vec) == 0:
            logger.error("クエリベクトルの次元が0です")
            return []
        
        scored_docs = []
        
        for i, doc in enumerate(all_docs):
            try:
                # メタデータフィルタリング
                if filter_metadata:
                    doc_meta = doc.get("metadata", {})
                    if not all(doc_meta.get(k) == v for k, v in filter_metadata.items()):
                        continue
                
                # ベクトルの存在確認
                if "vector" not in doc:
                    logger.warning(f"ドキュメント{i+1}にベクトルがありません")
                    continue
                
                doc_vec = np.array(doc["vector"], dtype=np.float32)
                
                # 次元数の確認
                if len(doc_vec) != len(query_vec):
                    logger.warning(f"ドキュメント{i+1}のベクトル次元が不一致: {len(doc_vec)} != {len(query_vec)}")
                    continue
                
                # コサイン類似度計算
                dot_product = np.dot(query_vec, doc_vec)
                norm_query = np.linalg.norm(query_vec)
                norm_doc = np.linalg.norm(doc_vec)
                
                if norm_query == 0 or norm_doc == 0:
                    score = 0.0
                else:
                    score = float(dot_product / (norm_query * norm_doc))
                
                scored_docs.append({
                    "id": doc.get("id", f"doc_{i}"),
                    "score": score,
                    "metadata": doc.get("metadata", {})
                })
            except Exception as e:
                logger.warning(f"ドキュメント{i+1}の処理に失敗: {e}")
                continue
        
        # スコアでソート
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        
        result = scored_docs[:top_k]
        logger.info(f"検索完了: {len(result)}件の結果を返します")
        
        return result
    except Exception as e:
        logger.error(f"検索処理で予期しないエラー: {e}", exc_info=True)
        return []


def _load_all_vectors_from_s3() -> List[Dict[str, Any]]:
    """
    S3またはローカルからすべてのベクトルを読み込む
    """
    global s3, _s3_available
    
    docs = []
    
    # S3から読み込みを試行
    if s3 and _s3_available:
        try:
            prefix = f"{VECTOR_INDEX}/"
            paginator = s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=VECTOR_BUCKET, Prefix=prefix)
            
            for page in pages:
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if not key.endswith(".json"):
                        continue
                    
                    try:
                        resp = s3.get_object(Bucket=VECTOR_BUCKET, Key=key)
                        doc = json.loads(resp["Body"].read().decode("utf-8"))
                        docs.append(doc)
                    except Exception as e:
                        logger.warning(f"S3オブジェクトの読み込みに失敗しました（{key}）: {e}")
            
            if docs:
                logger.info(f"S3から{len(docs)}件のベクトルを読み込みました")
                return docs
        except (ClientError, NoCredentialsError) as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
            if error_code == "InvalidAccessKeyId" or error_code == "SignatureDoesNotMatch":
                logger.warning(f"S3認証エラー: AWS認証情報を確認してください")
                _s3_available = False
            else:
                logger.warning(f"S3からの読み込みに失敗しました。ローカルファイルから読み込みます: {e}")
        except Exception as e:
            logger.warning(f"S3からの読み込みに失敗しました。ローカルファイルから読み込みます: {e}")
    elif not _s3_available:
        # S3が利用できない場合は、再初期化を試みる
        _init_s3_client()
        if s3 and _s3_available:
            try:
                prefix = f"{VECTOR_INDEX}/"
                paginator = s3.get_paginator("list_objects_v2")
                pages = paginator.paginate(Bucket=VECTOR_BUCKET, Prefix=prefix)
                
                for page in pages:
                    for obj in page.get("Contents", []):
                        key = obj["Key"]
                        if not key.endswith(".json"):
                            continue
                        
                        try:
                            resp = s3.get_object(Bucket=VECTOR_BUCKET, Key=key)
                            doc = json.loads(resp["Body"].read().decode("utf-8"))
                            docs.append(doc)
                        except Exception as e:
                            logger.warning(f"S3オブジェクトの読み込みに失敗しました（{key}）: {e}")
                
                if docs:
                    logger.info(f"S3接続が復旧し、{len(docs)}件のベクトルを読み込みました")
                    return docs
            except Exception as e:
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
    
    if docs:
        logger.info(f"ローカルから{len(docs)}件のベクトルを読み込みました")
    
    return docs


def search_by_text(query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    テキストクエリからベクトル検索を実行
    """
    query_vector = embedding.embed_text(query_text)
    return search_s3vectors(query_vector, top_k=top_k)


def delete_vectors_by_filename(filename: str) -> int:
    """
    指定されたファイル名に関連するベクトルを削除
    戻り値: 削除されたベクトルの数
    """
    global s3, _s3_available
    
    deleted_count = 0
    
    # ローカルファイルから削除
    if os.path.exists(UPLOAD_DIR):
        for file_path in os.listdir(UPLOAD_DIR):
            if not file_path.endswith(".json"):
                continue
            
            full_path = os.path.join(UPLOAD_DIR, file_path)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                    doc_filename = doc.get("metadata", {}).get("filename", "")
                    if doc_filename == filename:
                        os.remove(full_path)
                        deleted_count += 1
                        logger.info(f"ローカルベクトルを削除しました: {file_path}")
            except Exception as e:
                logger.warning(f"ベクトルファイルの読み込み/削除に失敗しました（{file_path}）: {e}")
    
    # S3から削除
    if s3 and _s3_available:
        try:
            prefix = f"{VECTOR_INDEX}/"
            paginator = s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=VECTOR_BUCKET, Prefix=prefix)
            
            keys_to_delete = []
            for page in pages:
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if not key.endswith(".json"):
                        continue
                    
                    try:
                        resp = s3.get_object(Bucket=VECTOR_BUCKET, Key=key)
                        doc = json.loads(resp["Body"].read().decode("utf-8"))
                        doc_filename = doc.get("metadata", {}).get("filename", "")
                        if doc_filename == filename:
                            keys_to_delete.append(key)
                    except Exception as e:
                        logger.warning(f"S3オブジェクトの読み込みに失敗しました（{key}）: {e}")
            
            # バッチ削除
            if keys_to_delete:
                for key in keys_to_delete:
                    try:
                        s3.delete_object(Bucket=VECTOR_BUCKET, Key=key)
                        deleted_count += 1
                        logger.info(f"S3ベクトルを削除しました: {key}")
                    except Exception as e:
                        logger.warning(f"S3ベクトルの削除に失敗しました（{key}）: {e}")
        except Exception as e:
            logger.warning(f"S3からのベクトル削除に失敗しました: {e}")
    
    return deleted_count

