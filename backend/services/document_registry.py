import json
import os
import threading
from datetime import datetime, timezone
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
REGISTRY_PATH = os.path.join(DATA_DIR, "documents_meta.json")

os.makedirs(DATA_DIR, exist_ok=True)

_lock = threading.Lock()


def _load() -> Dict[str, Any]:
    if not os.path.exists(REGISTRY_PATH):
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError:
            return {}


def _save(data: Dict[str, Any]) -> None:
    with open(REGISTRY_PATH, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def upsert_document(filename: str, metadata: Dict[str, Any]) -> None:
    """
    Create or update metadata for a document.
    """
    with _lock:
        data = _load()
        data[filename] = {
            **metadata,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        _save(data)


def remove_document(filename: str) -> None:
    with _lock:
        data = _load()
        if filename in data:
            data.pop(filename)
            _save(data)


def get_all() -> Dict[str, Any]:
    with _lock:
        return _load()

