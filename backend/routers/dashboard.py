from fastapi import APIRouter
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from datetime import datetime

from services import activity_log

# ======================
# AWS 設定
# ======================
AWS_REGION = "ap-northeast-1"
S3_BUCKET = "munakata1001-bucket "
VECTOR_INDEX = "company-rag-embeddings-poc"

# 環境変数から AWS 認証情報を取得
import os

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

bedrock_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

router = APIRouter()


@router.get("/dashboard")
async def dashboard():
    try:
        # --- ① S3 に格納されている文書数 ---
        docs = s3.list_objects_v2(Bucket=S3_BUCKET).get("Contents", [])
        document_count = len(docs)

        # --- 最新アップロード日時 ---
        latest_upload = None
        if docs:
            latest = max(docs, key=lambda d: d["LastModified"])
            latest_upload = latest["LastModified"].isoformat()

        # --- ② Vector store 内の全チャンク数 ---
        vectors = bedrock_runtime.list_vectors(
            indexIdentifier=VECTOR_INDEX,
            maxResults=5000,
        )
        chunk_count = len(vectors.get("vectors", []))

        # --- ③ Embedding モデル & ベクトル設定 ---
        index_info = bedrock_runtime.get_vector_index(
            indexIdentifier=VECTOR_INDEX
        )
        embedding_model = index_info.get("modelArn", "unknown")
        vector_dimension = index_info.get("dimensions", 0)

        # --- ④ API 稼働ステータス ---
        status = "running"

        return {
            "status": status,
            "documents": document_count,
            "chunks": chunk_count,
            "latest_upload": latest_upload,
            "embedding_model": embedding_model,
            "vector_dimension": vector_dimension,
            "vector_index": VECTOR_INDEX,
        }

    except NoCredentialsError:
        return {"error": "AWS credentials not found"}
    except ClientError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


@router.get("/logs")
async def get_logs(limit: int = 100):
    """
    利用ログを最新順で返す。
    """
    try:
        return activity_log.read_logs(limit=limit)
    except Exception as e:
        return {"error": str(e)}
