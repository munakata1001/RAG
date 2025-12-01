from fastapi import APIRouter, HTTPException
import boto3  # pyright: ignore[reportMissingImports]
from botocore.exceptions import NoCredentialsError, ClientError  # pyright: ignore[reportMissingImports]
import os
from datetime import datetime
import logging

from services import document_registry
from routers.documents import extract_text

router = APIRouter()
logger = logging.getLogger(__name__)

AWS_REGION = "ap-northeast-1"
# S3バケット名とS3 Vectorsインデックス名はdocuments.pyと一致させる
S3_BUCKET = "company-rag-docs-poc"
VECTOR_INDEX = "company-rag-embeddings-poc"
UPLOAD_DIR = "./data/uploads"

# S3クライアントとBedrockクライアント（エラー時はNoneになる）
s3_client = None
bedrock_runtime = None
_s3_available = False
_s3_auth_error_logged = False  # 認証エラーのログを一度だけ出力するフラグ

def _init_s3_clients():
    """S3とBedrockクライアントを初期化（リトライ可能）"""
    global s3_client, bedrock_runtime, _s3_available
    try:
        s3_client = boto3.client("s3", region_name=AWS_REGION)
        bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
        _s3_available = True
        logger.info(f"S3/Bedrockクライアントを初期化しました（リージョン: {AWS_REGION}）")
        return True
    except Exception as e:
        logger.debug(f"S3/Bedrockクライアントの初期化に失敗しました。ローカルモードで動作します: {e}")
        s3_client = None
        bedrock_runtime = None
        _s3_available = False
        return False

# 初期化を実行
_init_s3_clients()


@router.get("/list_docs")
async def list_documents():
    """
    S3バケットにアップロードされている文書の一覧を返す。
    S3へ接続できなかった場合はローカルのUPLOAD_DIRを参照する。
    """
    global s3_client, _s3_available, _s3_auth_error_logged
    
    # S3が利用できない場合は、再初期化を試みる（認証エラーが発生していない場合のみ）
    if not s3_client or (not _s3_available and not _s3_auth_error_logged):
        _init_s3_clients()
    
    if s3_client and _s3_available:
        try:
            response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
            s3_files = response.get("Contents", [])
            documents_list = _format_s3_response(s3_files)
            logger.info(f"S3から{len(documents_list)}件のドキュメントを取得しました")
            return {"docs": documents_list}
        except (NoCredentialsError, ClientError) as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
            if error_code == "InvalidAccessKeyId" or error_code == "SignatureDoesNotMatch":
                if not _s3_auth_error_logged:
                    logger.info("S3認証情報が設定されていないため、ローカルモードで動作します")
                    logger.debug("S3を使用するには、AWS認証情報を設定してください（環境変数または~/.aws/credentials）")
                    _s3_auth_error_logged = True
                _s3_available = False
            else:
                logger.debug("S3に接続できなかったためローカルファイル一覧にフォールバックします: %s", e)
            return {"docs": _list_local_documents()}
        except Exception as e:
            logger.debug("S3からの取得に失敗しました。ローカルファイル一覧にフォールバックします: %s", e)
            return {"docs": _list_local_documents()}
    else:
        # 認証エラーが既にログ出力されている場合は、デバッグログのみ
        if not _s3_auth_error_logged:
            logger.debug("S3が利用できないため、ローカルファイル一覧を返します")
        return {"docs": _list_local_documents()}


def _format_s3_response(s3_files):
    documents_list = []
    for s3_file in s3_files:
        filename = s3_file.get("Key", "")
        if not filename or filename.startswith("."):
            continue

        file_extension = os.path.splitext(filename)[1].lstrip(".")
        last_modified_dt = s3_file.get("LastModified")
        last_modified = (
            last_modified_dt.isoformat() if last_modified_dt else datetime.utcnow().isoformat()
        )

        documents_list.append(
            {
                "filename": filename,
                "file_type": file_extension,
                "last_modified": last_modified,
            }
        )

    documents_list.sort(key=lambda x: x["filename"])
    return _merge_metadata(documents_list)


def _list_local_documents():
    if not os.path.exists(UPLOAD_DIR):
        return []

    documents_list = []
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.isfile(file_path) or filename.startswith("."):
            continue

        file_extension = os.path.splitext(filename)[1].lstrip(".")
        last_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

        documents_list.append(
            {
                "filename": filename,
                "file_type": file_extension,
                "last_modified": last_modified,
            }
        )

    documents_list.sort(key=lambda x: x["filename"])
    return _merge_metadata(documents_list)


def _merge_metadata(documents):
    registry = document_registry.get_all()
    for item in documents:
        meta = registry.get(item["filename"])
        if meta:
            item.update(meta)
    return documents


@router.get("/document/{filename}")
async def get_document_content(filename: str):
    """
    指定されたファイル名のドキュメントの内容を取得する
    """
    # ファイル名の安全性チェック（ディレクトリトラバーサル対策）
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="無効なファイル名です")
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail="ファイルではありません")
    
    try:
        # テキスト抽出
        text = extract_text(file_path)
        return {
            "filename": filename,
            "content": text
        }
    except Exception as e:
        logger.error(f"ドキュメント内容の取得に失敗しました: {e}")
        raise HTTPException(status_code=500, detail=f"ドキュメント内容の取得に失敗しました: {str(e)}")


@router.delete("/document/{filename}")
async def delete_document(filename: str):
    """
    指定されたファイル名のドキュメントを削除する
    ファイル、メタデータ、ベクトルストアから削除
    """
    global s3_client, _s3_available
    
    # ファイル名の安全性チェック
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="無効なファイル名です")
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    deleted_items = []
    errors = []
    
    # 1. ローカルファイルを削除
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            deleted_items.append("ローカルファイル")
            logger.info(f"ローカルファイルを削除しました: {filename}")
        except Exception as e:
            errors.append(f"ローカルファイルの削除に失敗: {str(e)}")
            logger.error(f"ローカルファイルの削除に失敗しました: {e}")
    
    # 2. S3から削除（試行）
    if s3_client and _s3_available:
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=filename)
            deleted_items.append("S3ファイル")
            logger.info(f"S3ファイルを削除しました: {filename}")
        except (NoCredentialsError, ClientError) as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
            if error_code == "InvalidAccessKeyId" or error_code == "SignatureDoesNotMatch":
                logger.warning("S3認証エラー: AWS認証情報を確認してください")
                _s3_available = False
            else:
                logger.warning(f"S3からの削除をスキップしました: {e}")
        except Exception as e:
            logger.warning(f"S3からの削除に失敗しました: {e}")
    else:
        logger.info("S3が利用できないため、S3からの削除をスキップします")
    
    # 3. ドキュメントレジストリから削除
    try:
        document_registry.remove_document(filename)
        deleted_items.append("メタデータ")
        logger.info(f"メタデータを削除しました: {filename}")
    except Exception as e:
        errors.append(f"メタデータの削除に失敗: {str(e)}")
        logger.error(f"メタデータの削除に失敗しました: {e}")
    
    # 4. ベクトルストアから削除
    try:
        from services.s3vectors_store import delete_vectors_by_filename
        deleted_count = delete_vectors_by_filename(filename)
        if deleted_count > 0:
            deleted_items.append(f"ベクトル（{deleted_count}件）")
            logger.info(f"ベクトルを削除しました: {filename} ({deleted_count}件)")
    except Exception as e:
        errors.append(f"ベクトルの削除に失敗: {str(e)}")
        logger.error(f"ベクトルの削除に失敗しました: {e}")
    
    if not deleted_items and not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    
    return {
        "message": "削除完了",
        "filename": filename,
        "deleted_items": deleted_items,
        "errors": errors if errors else None
    }
