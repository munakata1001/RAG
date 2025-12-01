"""
エンドポイントの動作確認用スクリプト
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None):
    """エンドポイントをテストする"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"未対応のメソッド: {method}")
            return
        
        print(f"\n{method} {path}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            try:
                print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            except:
                print(f"Response: {response.text[:200]}")
        else:
            print(f"Error: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print(f"\n{method} {path}")
        print("Error: サーバーに接続できません。バックエンドサーバーが起動しているか確認してください。")
    except Exception as e:
        print(f"\n{method} {path}")
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("エンドポイント動作確認")
    print("=" * 50)
    
    # ヘルスチェック
    test_endpoint("GET", "/health")
    
    # RAGエンドポイント
    test_endpoint("POST", "/api/rag", {
        "query": "テスト",
        "top_k": 5
    })
    
    # ドキュメント一覧
    test_endpoint("GET", "/api/list_docs")
    
    print("\n" + "=" * 50)
    print("確認完了")
    print("=" * 50)

