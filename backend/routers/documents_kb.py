# routers/documents_kb.py
import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
import boto3
from botocore.exceptions import ClientError
from services.vector_store import add_kb_vectors 

logger = logging.getLogger(__name__)
router = APIRouter()

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
KB_ID = os.getenv("KB_ID")                 # 必須：Knowledge Base ID
S3_BUCKET = os.getenv("S3_BUCKET")         # 必須：アップロード先バケット
DATA_SOURCE_ID = os.getenv("DATA_SOURCE_ID")  # 任意：KB に紐づく DataSource ID（ある場合）

s3 = boto3.client("s3", region_name=AWS_REGION)
bedrock_agent = boto3.client("bedrock-agent", region_name=AWS_REGION)


@router.post("/admin/upload_and_register")
async def upload_and_register_document(file: UploadFile = File(...)):
    if not KB_ID or not S3_BUCKET:
        raise HTTPException(status_code=500, detail="KB_ID and S3_BUCKET must be set in env")

    # 1) S3 にアップロード
    file_id = str(uuid.uuid4())
    key = f"uploads/{file_id}_{file.filename}"

    try:
        # file.file は SpooledTemporaryFile のような file-like object
        s3.upload_fileobj(file.file, S3_BUCKET, key)
        logger.info("Uploaded file to s3://%s/%s", S3_BUCKET, key)
    except ClientError as e:
        logger.exception("S3 upload failed")
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

    # 2) dataSourceId が env にあれば使う、なければ KB の data sources を列挙して最初のものを使う
    data_source_id = DATA_SOURCE_ID
    try:
        if not data_source_id:
            resp = bedrock_agent.list_data_sources(knowledgeBaseId=KB_ID, maxResults=50)
            items = resp.get("dataSources", []) or resp.get("dataSourceSummaries", []) or []
            if not items:
                raise HTTPException(status_code=400, detail="No data sources found for KB. Create/connect an S3 data source in Bedrock console first.")
            # 単純化：最初の dataSource を使う（必要ならフィルタリング処理を追加）
            data_source_id = items[0].get("dataSourceId") or items[0].get("id")
            logger.info("Selected dataSourceId: %s", data_source_id)
    except ClientError as e:
        logger.exception("Failed to list data sources")
        raise HTTPException(status_code=500, detail=f"Failed to list data sources: {e}")

    # 3) Start ingestion job
    try:
        start_resp = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=KB_ID,
            dataSourceId=data_source_id,
            description=f"ingest {key}"
        )
        ingestion_job_id = start_resp.get("ingestionJobId") or start_resp.get("id") or start_resp.get("jobId")
        logger.info("Started ingestion job %s", ingestion_job_id)
    except ClientError as e:
        logger.exception("Failed to start ingestion job")
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion job: {e}")

    return {
        "status": "started",
        "s3_key": key,
        "data_source_id": data_source_id,
        "ingestion_job_id": ingestion_job_id,
    }


@router.get("/admin/ingestion_status")
def get_ingestion_status(ingestion_job_id: str, data_source_id: str = None):
    """Get ingestion job status. ingestion_job_id は upload_and_register の戻り値から取得"""
    if not KB_ID:
        raise HTTPException(status_code=500, detail="KB_ID must be set in env")
    if not data_source_id:
        raise HTTPException(status_code=400, detail="data_source_id is required")

    try:
        resp = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=KB_ID,
            dataSourceId=data_source_id,
            ingestionJobId=ingestion_job_id
        )
        return resp
    except ClientError as e:
        logger.exception("Failed to get ingestion job")
        raise HTTPException(status_code=500, detail=f"Failed to get ingestion job: {e}")
