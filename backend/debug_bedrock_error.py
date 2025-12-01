"""
Bedrockエラーの詳細診断スクリプト
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

def diagnose_bedrock_error():
    """Bedrockエラーの詳細診断"""
    print("=" * 60)
    print("Bedrockエラー診断")
    print("=" * 60)
    print(f"リージョン: {AWS_REGION}")
    print(f"モデルID: {MODEL_ID}")
    print()
    
    # 1. 認証情報の確認
    print("1. 認証情報の確認")
    print("-" * 60)
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if access_key:
        print(f"✓ AWS_ACCESS_KEY_ID: {access_key[:10]}...{access_key[-4:] if len(access_key) > 14 else ''}")
    else:
        print("✗ AWS_ACCESS_KEY_ID: 未設定")
        print("  .envファイルまたは環境変数で設定してください")
    
    if secret_key:
        print("✓ AWS_SECRET_ACCESS_KEY: 設定済み")
    else:
        print("✗ AWS_SECRET_ACCESS_KEY: 未設定")
        print("  .envファイルまたは環境変数で設定してください")
    
    # AWS認証情報ファイルの確認
    aws_creds = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(aws_creds):
        print(f"✓ ~/.aws/credentials: 存在")
    else:
        print(f"✗ ~/.aws/credentials: 不存在")
    
    print()
    
    # 2. Bedrockクライアントの初期化テスト
    print("2. Bedrockクライアントの初期化テスト")
    print("-" * 60)
    try:
        bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        print("✓ Bedrockクライアントの初期化に成功")
    except Exception as e:
        print(f"✗ Bedrockクライアントの初期化に失敗: {e}")
        return
    
    print()
    
    # 3. モデル一覧の取得テスト
    print("3. モデル一覧の取得テスト")
    print("-" * 60)
    try:
        bedrock_list = boto3.client("bedrock", region_name=AWS_REGION)
        response = bedrock_list.list_foundation_models()
        models = response.get("modelSummaries", [])
        print(f"✓ モデル一覧の取得に成功: {len(models)}件")
        
        # 指定されたモデルIDが存在するか確認
        model_ids = [m.get("modelId") for m in models]
        if MODEL_ID in model_ids:
            print(f"✓ 指定されたモデルID '{MODEL_ID}' が利用可能です")
        else:
            print(f"✗ 指定されたモデルID '{MODEL_ID}' が見つかりません")
            print("  利用可能なClaude 3モデル:")
            claude_models = [m for m in models if "claude-3" in m.get("modelId", "").lower()]
            for model in claude_models[:5]:
                print(f"    - {model.get('modelId')}")
    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        error_message = getattr(e, "response", {}).get("Error", {}).get("Message", str(e))
        print(f"✗ モデル一覧の取得に失敗")
        print(f"  エラーコード: {error_code}")
        print(f"  エラーメッセージ: {error_message}")
        
        if error_code == "UnrecognizedClientException":
            print()
            print("  診断: 認証情報が無効です")
            print("  解決方法:")
            print("  1. .envファイルの認証情報を確認")
            print("  2. 認証情報が期限切れでないか確認")
            print("  3. 新しいアクセスキーを生成して設定")
        elif error_code == "AccessDeniedException":
            print()
            print("  診断: IAM権限が不足しています")
            print("  解決方法:")
            print("  1. IAMユーザーにbedrock:ListFoundationModels権限を付与")
            print("  2. または、AmazonBedrockFullAccessポリシーをアタッチ")
    
    print()
    
    # 4. モデル呼び出しテスト
    print("4. モデル呼び出しテスト")
    print("-" * 60)
    try:
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
        
        response = bedrock.invoke_model(**payload)
        model_response = json.loads(response["body"].read())
        answer = model_response["content"][0]["text"]
        print(f"✓ モデル呼び出しに成功")
        print(f"  回答: {answer[:50]}...")
        
    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        error_message = getattr(e, "response", {}).get("Error", {}).get("Message", str(e))
        
        print(f"✗ モデル呼び出しに失敗")
        print(f"  エラーコード: {error_code}")
        print(f"  エラーメッセージ: {error_message}")
        print()
        
        # 詳細な診断
        if error_code == "UnrecognizedClientException":
            print("【診断】認証情報が無効です")
            print()
            print("考えられる原因:")
            print("1. アクセスキーIDまたはシークレットアクセスキーが間違っている")
            print("2. 認証情報が期限切れ")
            print("3. 認証情報が削除または無効化されている")
            print()
            print("解決方法:")
            print("1. AWSコンソールで認証情報を確認")
            print("2. 新しいアクセスキーを生成")
            print("3. .envファイルを更新")
            
        elif error_code == "AccessDeniedException":
            print("【診断】IAM権限が不足しています")
            print()
            print("考えられる原因:")
            print("1. IAMユーザーにBedrock権限がない")
            print("2. モデルへのアクセスが制限されている")
            print("3. 初回使用時の使用目的提出が必要")
            print()
            print("解決方法:")
            print("1. IAMユーザーにAmazonBedrockFullAccessを付与")
            print("2. Playgroundで一度モデルを試す（使用目的提出）")
            print("3. カスタムポリシーでbedrock:InvokeModel権限を付与")
            
        elif error_code == "ValidationException":
            print("【診断】リクエストの形式が不正です")
            print()
            print("考えられる原因:")
            print("1. モデルIDが間違っている")
            print("2. リージョンでモデルが利用できない")
            print("3. リクエストボディの形式が間違っている")
            print()
            print("解決方法:")
            print(f"1. モデルIDを確認: {MODEL_ID}")
            print(f"2. リージョンを確認: {AWS_REGION}")
            print("3. python list_bedrock_models.py で利用可能なモデルを確認")
            
        elif error_code == "ThrottlingException":
            print("【診断】レート制限に達しています")
            print()
            print("解決方法:")
            print("1. しばらく待ってから再試行")
            print("2. リクエスト頻度を減らす")
            
        elif error_code == "ModelNotReadyException":
            print("【診断】モデルが準備できていません")
            print()
            print("解決方法:")
            print("1. しばらく待ってから再試行")
            print("2. 別のモデルIDを試す")
            
        else:
            print("【診断】不明なエラー")
            print()
            print("詳細情報:")
            print(f"  エラーコード: {error_code}")
            print(f"  エラーメッセージ: {error_message}")
            print()
            print("解決方法:")
            print("1. AWSコンソールでBedrockの状態を確認")
            print("2. 認証情報とIAM権限を確認")
            print("3. リージョンとモデルIDを確認")
    
    print()
    print("=" * 60)
    print("診断完了")
    print("=" * 60)

if __name__ == "__main__":
    diagnose_bedrock_error()

