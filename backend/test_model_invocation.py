"""
モデル呼び出しの詳細テストスクリプト
モデルIDが利用可能でも呼び出せない場合の原因を特定
"""
import boto3
import json
import os
import sys

# .envファイルを読み込む
try:
    from dotenv import load_dotenv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print(f"✓ .envファイルを読み込みました")
except ImportError:
    print("⚠️  python-dotenvがインストールされていません")
except Exception as e:
    print(f"⚠️  .envファイルの読み込みに失敗: {e}")

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
# デフォルトモデルID: 28kコンテキストウィンドウ版を使用
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0:28k")

def test_model_invocation():
    """モデル呼び出しを詳細にテスト"""
    print("=" * 60)
    print("モデル呼び出し詳細テスト")
    print("=" * 60)
    print(f"リージョン: {AWS_REGION}")
    print(f"モデルID: {MODEL_ID}")
    print()
    
    # 認証情報の確認
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if not access_key or not secret_key:
        print("✗ 認証情報が設定されていません")
        print("  .envファイルに認証情報を設定してください")
        return False
    
    print("✓ 認証情報が設定されています")
    print()
    
    # Bedrockクライアントの初期化
    try:
        print("1. Bedrockクライアントの初期化")
        print("-" * 60)
        bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        print("✓ 初期化成功")
        print()
    except Exception as e:
        print(f"✗ 初期化失敗: {e}")
        return False
    
    # モデル一覧の確認
    try:
        print("2. モデル一覧の確認")
        print("-" * 60)
        bedrock_list = boto3.client("bedrock", region_name=AWS_REGION)
        response = bedrock_list.list_foundation_models()
        models = response.get("modelSummaries", [])
        model_ids = [m.get("modelId") for m in models]
        
        if MODEL_ID in model_ids:
            print(f"✓ モデルID '{MODEL_ID}' が利用可能です")
        else:
            print(f"✗ モデルID '{MODEL_ID}' が見つかりません")
            print("  利用可能なClaude 3モデル:")
            claude_models = [m for m in models if "claude-3" in m.get("modelId", "").lower()]
            for model in claude_models[:5]:
                print(f"    - {model.get('modelId')}")
            return False
        print()
    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        if error_code == "AccessDeniedException":
            print(f"⚠️  モデル一覧の取得に失敗（権限不足）: {error_code}")
            print("   ただし、モデル呼び出しは試行します")
        else:
            print(f"⚠️  モデル一覧の取得に失敗: {e}")
        print()
    
    # モデル呼び出しテスト（最小限のリクエスト）
    try:
        print("3. モデル呼び出しテスト（最小限のリクエスト）")
        print("-" * 60)
        print("リクエスト内容:")
        print(f"  modelId: {MODEL_ID}")
        print(f"  region: {AWS_REGION}")
        print()
        
        payload = {
            "modelId": MODEL_ID,
            "contentType": "application/json",
            "accept": "*/*",
            "body": json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "temperature": 0.3,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ]
            })
        }
        
        print("リクエスト送信中...")
        response = bedrock.invoke_model(**payload)
        model_response = json.loads(response["body"].read())
        answer = model_response["content"][0]["text"]
        
        print("✓ モデル呼び出しに成功しました！")
        print(f"  回答: {answer}")
        print()
        print("=" * 60)
        print("✓ すべてのテストに成功しました")
        print("=" * 60)
        return True
        
    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        error_message = getattr(e, "response", {}).get("Error", {}).get("Message", str(e))
        
        print(f"✗ モデル呼び出しに失敗しました")
        print(f"  エラーコード: {error_code}")
        print(f"  エラーメッセージ: {error_message}")
        print()
        
        # 詳細な診断
        print("=" * 60)
        print("詳細診断")
        print("=" * 60)
        
        if error_code == "UnrecognizedClientException":
            print("【原因】認証情報が無効です")
            print()
            print("確認事項:")
            print("1. .envファイルのAWS_ACCESS_KEY_IDとAWS_SECRET_ACCESS_KEYが正しいか")
            print("2. 認証情報が期限切れでないか")
            print("3. 認証情報が削除または無効化されていないか")
            print()
            print("解決方法:")
            print("1. AWSコンソール → IAM → ユーザー → セキュリティ認証情報")
            print("2. 新しいアクセスキーを生成")
            print("3. .envファイルを更新")
            
        elif error_code == "AccessDeniedException":
            print("【原因】IAM権限が不足している、または初回使用時の使用目的提出が必要")
            print()
            print("確認事項:")
            print("1. IAMユーザーにAmazonBedrockFullAccessが付与されているか")
            print("2. 初回使用時の使用目的提出が完了しているか")
            print()
            print("解決方法:")
            print("方法1: IAM権限を確認・付与")
            print("  1. AWSコンソール → IAM → ユーザー")
            print("  2. 該当ユーザーを選択 → 許可タブ")
            print("  3. AmazonBedrockFullAccessを確認または追加")
            print()
            print("方法2: Playgroundで初回使用時の使用目的提出")
            print("  1. AWSコンソール → Bedrock → モデルカタログ")
            print("  2. Claude 3 Sonnetを選択")
            print("  3. Playgroundで開く")
            print("  4. 使用目的を入力して送信")
            print("  5. 再度このスクリプトを実行")
            
        elif error_code == "ValidationException":
            print("【原因】リクエストの形式が不正です")
            print()
            print("確認事項:")
            print(f"1. モデルIDが正しいか: {MODEL_ID}")
            print(f"2. リージョンが正しいか: {AWS_REGION}")
            print("3. リクエストボディの形式が正しいか")
            print()
            print("解決方法:")
            print("1. モデルIDとリージョンを再確認")
            print("2. 利用可能なモデル一覧を確認: python list_bedrock_models.py")
            
        elif error_code == "ThrottlingException":
            print("【原因】レート制限に達しています")
            print()
            print("解決方法:")
            print("1. しばらく待ってから再試行")
            print("2. リクエスト頻度を減らす")
            
        elif error_code == "ModelNotReadyException":
            print("【原因】モデルが準備できていません")
            print()
            print("解決方法:")
            print("1. しばらく待ってから再試行")
            print("2. 別のモデルIDを試す")
            
        else:
            print(f"【原因】不明なエラー: {error_code}")
            print()
            print("詳細情報:")
            print(f"  エラーコード: {error_code}")
            print(f"  エラーメッセージ: {error_message}")
            print()
            print("解決方法:")
            print("1. AWSコンソールでBedrockの状態を確認")
            print("2. 認証情報とIAM権限を確認")
            print("3. リージョンとモデルIDを確認")
            print("4. AWSサポートに問い合わせ")
        
        print()
        print("=" * 60)
        print("✗ テストに失敗しました")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_model_invocation()
    sys.exit(0 if success else 1)

