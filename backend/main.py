from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ルーター読み込み
from routers import documents   # /upload（文書アップロード）  # pyright: ignore[reportMissingImports]
# 今後ここに search, generate など追加可能
# from routers import search
# from routers import generate

app = FastAPI(
    title="RAG PoC API",
    description="文書取り込み・検索・回答生成のPoC用API",
    version="1.0.0"
)

# --- CORS設定 ---
# React(3000)やローカルでの開発環境UIから呼べるようにする
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 本番では限定する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ルーター登録 ---
app.include_router(documents.router, prefix="/api", tags=["Documents"])
# app.include_router(search.router, prefix="/api", tags=["Search"])
# app.include_router(generate.router, prefix="/api", tags=["Generate"])


@app.get("/")
def root():
    return {"message": "RAG PoC API 起動中"}

