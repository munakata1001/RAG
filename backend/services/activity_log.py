import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
LOG_PATH = os.path.join(DATA_DIR, "activity_logs.jsonl")

os.makedirs(DATA_DIR, exist_ok=True)

_lock = threading.Lock()


def append_log(action: str, detail: Dict[str, Any], user_id: Optional[str] = None) -> None:
    """
    Append a usage log entry. Stored as JSONL for easy streaming.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user": user_id or "local-user",
        "detail": detail,
    }

    line = json.dumps(entry, ensure_ascii=False)
    with _lock:
        with open(LOG_PATH, "a", encoding="utf-8") as fp:
            fp.write(line + "\n")


def read_logs(limit: int = 200) -> List[Dict[str, Any]]:
    """
    Read the most recent log entries (default 200).
    """
    if not os.path.exists(LOG_PATH):
        return []

    with _lock:
        with open(LOG_PATH, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

    entries = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(entries) >= limit:
            break

    return entries

