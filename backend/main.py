from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# .envファイルから環境変数を読み込む（開発環境用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenvがインストールされていない場合はスキップ

# Routers
from routers import pipeline, list_docs, rag, search, generate, usage_logs, dashboard, debug

app = FastAPI(title="RAG PoC API")

# CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(pipeline.router, prefix="/admin", tags=["Pipeline"])
app.include_router(dashboard.router, prefix="/admin", tags=["Dashboard"])
app.include_router(list_docs.router, prefix="/api", tags=["Documents"])
app.include_router(rag.router, prefix="/api", tags=["RAG"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(generate.router, prefix="/api", tags=["Generate"])
app.include_router(usage_logs.router, prefix="/api", tags=["UsageLogs"])
app.include_router(debug.router, prefix="/api", tags=["Debug"])

# 健康チェック
@app.get("/health")
def health():
    return {"status": "ok"}

# 静的ファイル（SPA）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FILES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist"))

# 静的アセット（JS、CSS等）をマウント
assets_dir = os.path.join(STATIC_FILES_DIR, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# ルートパス（/）はSPAのindex.htmlを返す
@app.get("/")
def serve_root():
    index_file = os.path.join(STATIC_FILES_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "これはAPIのルートです（SPAファイルが見つかりません）"}

# SPAのルーティング用（すべてのパスでindex.htmlを返す）
# 注意: FastAPIのルーティングでは、より具体的なルート（/assets, /api等）が先にマッチするため、
# この関数はAPIパスや静的ファイルパス以外のGETリクエストに対してのみ呼ばれる
# POST/PUT/DELETEなどのリクエストは、APIルーターが先にマッチするため、この関数には到達しない
# ただし、念のためAPIパスを明示的に除外
@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    # APIパスやヘルスチェックは除外（GETリクエストのみ）
    # この関数はGETリクエストのみを処理するため、POSTリクエストには影響しない
    if (full_path.startswith("api/") or 
        full_path.startswith("admin/") or 
        full_path == "health" or
        full_path.startswith("assets/")):
        raise HTTPException(status_code=404, detail="Not found")
    
    # SPAのindex.htmlを返す（クライアント側ルーティング用）
    index_file = os.path.join(STATIC_FILES_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="SPA not found")
