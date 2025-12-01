from sentence_transformers import SentenceTransformer
from typing import List
import threading

# モデル名（PoCでは MiniLM が高速で最適）
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
_model_lock = threading.Lock()


def get_embedding_model():
    """
    モデルを1回だけロードして使い回す（重複ロード防止）
    """
    global _model

    if _model is None:
        with _model_lock:
            if _model is None:
                print(f"Loading embedding model: {MODEL_NAME}")
                _model = SentenceTransformer(MODEL_NAME)

    return _model


def embed_text(text: str) -> List[float]:
    """
    単一テキスト → 埋め込みベクトル(List[float])を返す
    """
    model = get_embedding_model()
    vector = model.encode(text, convert_to_numpy=True).tolist()
    return vector


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """
    複数チャンクまとめてエンコード
    """
    model = get_embedding_model()
    vectors = model.encode(chunks, convert_to_numpy=True).tolist()
    return vectors
