import requests
import json

BASE = "http://localhost:8000/api"

def test_upload_and_register():
    print("\n=== 1. Upload & Register ===")

    files = {"file": open("testdata/sample.pdf", "rb")}
    res = requests.post(f"{BASE}/upload_and_register", files=files)

    print(res.status_code, res.text)
    assert res.status_code == 200
    data = res.json()
    assert data["chunks"] > 0

    return data["filename"]


def test_list_documents():
    print("\n=== 2. List Documents ===")

    res = requests.get(f"{BASE}/documents")
    print(res.status_code, res.text)

    assert res.status_code == 200
    data = res.json()
    assert "files" in data

    return data["files"]


def test_search():
    print("\n=== 3. Search ===")

    payload = {
        "query": "請求書の作成方法を教えてください",
        "top_k": 5
    }
    res = requests.post(f"{BASE}/search", json=payload)

    print(res.status_code, res.text)
    assert res.status_code == 200

    data = res.json()
    assert len(data) > 0
    return data


def test_generate(contexts):
    print("\n=== 4. Generate ===")

    payload = {
        "query": "請求書の作成方法を教えてください",
        "contexts": [
            {"text": c["text"], "score": c["score"], "filename": c["filename"], "chunk_id": c["chunk_id"]}
            for c in contexts[:2]  # 上位2件を使う
        ]
    }

    res = requests.post(f"{BASE}/generate", json=payload)
    print(res.status_code, res.text)

    assert res.status_code == 200
    data = res.json()
    assert "answer" in data


if __name__ == "__main__":
    filename = test_upload_and_register()
    test_list_documents()
    contexts = test_search()
    test_generate(contexts)
