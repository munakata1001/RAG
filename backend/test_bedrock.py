"""
Bedrock接続テストスクリプト
Bedrockが正しく設定されているか確認します
"""
import boto3
import json
import os
import sys

# .envファイルを読み込む
print("=" * 60)
print(".envファイルの読み込み確認")
print("=" * 60)

try:
    from dotenv import load_dotenv
    # スクリプトのディレクトリを基準に.envファイルを探す
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    
    print(f"スクリプトのディレクトリ: {script_dir}")
    print(f".envファイルのパス: {env_path}")
    print(f".envファイルの存在: {os.path.exists(env_path)}")
    
    if os.path.exists(env_path):
        # .envファイルの内容を確認（デバッグ用）
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                print(f".envファイルの行数: {len(lines)}")
                # 最初の数行を表示（機密情報はマスク）
                for i, line in enumerate(lines[:5], 1):
                    stripped = line.strip()
                    if "=" in stripped and not stripped.startswith("#"):
                        key, value = stripped.split("=", 1)
                        if "SECRET" in key.upper() or "KEY" in key.upper():
                            print(f"  行{i}: {key}=***（値あり）" if value.strip() else f"  行{i}: {key}=（空）")
                        else:
                            print(f"  行{i}: {key}={value[:20]}..." if len(value) > 20 else f"  行{i}: {key}={value}")
        except Exception as e:
            print(f"⚠️  .envファイルの読み込み確認に失敗: {e}")
        
        load_dotenv(env_path, override=True)  # override=Trueで既存の環境変数を上書き
        print(f"✓ .envファイルを読み込みました: {env_path}")
        
        # 読み込み後の環境変数を確認
        test_key = os.getenv("AWS_ACCESS_KEY_ID")
        if test_key:
            print(f"✓ 環境変数の読み込み確認: AWS_ACCESS_KEY_ID={test_key[:10]}...")
        else:
            print("⚠️  環境変数が読み込まれていません。.envファイルの形式を確認してください")
    else:
        # カレントディレクトリからも探す
        current_dir = os.getcwd()
        current_env = os.path.join(current_dir, ".env")
        print(f"カレントディレクトリ: {current_dir}")
        print(f"カレントディレクトリの.env: {current_env}")
        print(f"カレントディレクトリの.envの存在: {os.path.exists(current_env)}")
        
        if os.path.exists(current_env):
            load_dotenv(current_env, override=True)
            print(f"✓ .envファイルを読み込みました: {current_env}")
        else:
            # デフォルトの動作（カレントディレクトリを探す）
            load_dotenv(override=True)
            print("⚠️  明示的な.envファイルが見つかりません。デフォルトの検索パスを使用します")
            
except ImportError:
    print("⚠️  python-dotenvがインストールされていません")
    print("   以下のコマンドでインストールしてください:")
    print("   pip install python-dotenv")
except Exception as e:
    print(f"⚠️  .envファイルの読み込みに失敗しました: {e}")
    import traceback
    traceback.print_exc()

print()

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
# デフォルトモデルID: 標準版を使用
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

def test_bedrock():
    """Bedrock接続をテストする"""
    print("=" * 60)
    print("Bedrock接続テスト")
    print("=" * 60)
    print(f"リージョン: {AWS_REGION}")
    print(f"モデルID: {MODEL_ID}")
    print()
    
    # 環境変数の確認（load_dotenvの後に再確認）
    # load_dotenvが呼ばれた後、再度環境変数を読み込む
    try:
        from dotenv import load_dotenv
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            print("✓ .envファイルから環境変数を再読み込みしました")
            print()
    except:
        pass
    
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # デバッグ情報
    print("環境変数の確認:")
    print(f"  AWS_ACCESS_KEY_ID: {'設定済み' if access_key else '未設定'}")
    if access_key:
        print(f"    値: {access_key[:10]}...{access_key[-4:] if len(access_key) > 14 else ''}")
    print(f"  AWS_SECRET_ACCESS_KEY: {'設定済み' if secret_key else '未設定'}")
    
    # AWS認証情報ファイルの確認
    aws_creds_path = os.path.expanduser("~/.aws/credentials")
    aws_config_path = os.path.expanduser("~/.aws/config")
    print(f"  ~/.aws/credentials: {'存在' if os.path.exists(aws_creds_path) else '不存在'}")
    print(f"  ~/.aws/config: {'存在' if os.path.exists(aws_config_path) else '不存在'}")
    
    # .envファイルの内容を確認（デバッグ用）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path) and not access_key:
        print()
        print("⚠️  .envファイルは存在しますが、環境変数が読み込まれていません")
        print("   .envファイルの内容を確認してください:")
        print(f"   python check_env.py")
        print()
        print("   .envファイルの形式例:")
        print("   AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
        print("   AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
        print("   （=の前後にスペースを入れないでください）")
    print()
    
    if not access_key:
        print("⚠️  AWS_ACCESS_KEY_IDが設定されていません")
        print("   以下のいずれかの方法で設定してください:")
        print("   1. .envファイルに AWS_ACCESS_KEY_ID=your-key を追加")
        print("   2. 環境変数で設定: $env:AWS_ACCESS_KEY_ID='your-key' (PowerShell)")
        print("   3. ~/.aws/credentials ファイルに設定")
        print()
    else:
        print(f"✓ AWS_ACCESS_KEY_ID: {access_key[:10]}...")
    
    if not secret_key:
        print("⚠️  AWS_SECRET_ACCESS_KEYが設定されていません")
        print("   以下のいずれかの方法で設定してください:")
        print("   1. .envファイルに AWS_SECRET_ACCESS_KEY=your-secret を追加")
        print("   2. 環境変数で設定: $env:AWS_SECRET_ACCESS_KEY='your-secret' (PowerShell)")
        print("   3. ~/.aws/credentials ファイルに設定")
        print()
    else:
        print("✓ AWS_SECRET_ACCESS_KEY: 設定済み")
    
    print()
    
    # Bedrockクライアントの初期化
    try:
        print("Bedrockクライアントを初期化中...")
        bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        print("✓ Bedrockクライアントの初期化に成功しました")
        print()
    except Exception as e:
        print(f"✗ Bedrockクライアントの初期化に失敗しました: {e}")
        print()
        print("確認事項:")
        print("1. AWS認証情報が正しく設定されているか")
        print("2. リージョンが正しいか（ap-northeast-1）")
        print("3. ネットワーク接続が正常か")
        return False
    
    # モデル一覧の確認（オプション）
    try:
        print("利用可能なモデルを確認中...")
        bedrock_list = boto3.client("bedrock", region_name=AWS_REGION)
        models = bedrock_list.list_foundation_models()
        available_models = [m["modelId"] for m in models["modelSummaries"] if "claude-3" in m["modelId"].lower()]
        if available_models:
            print(f"✓ 利用可能なClaude 3モデル: {len(available_models)}件")
            for model in available_models[:5]:  # 最初の5件を表示
                print(f"  - {model}")
            
            # 現在のモデルIDが利用可能か確認
            if MODEL_ID in available_models:
                print(f"  ✓ 現在のモデルID '{MODEL_ID}' が利用可能です")
            else:
                print(f"  ⚠️  現在のモデルID '{MODEL_ID}' が見つかりません")
                print("  利用可能なモデルIDを使用してください")
                # 推奨モデルを提案
                sonnet_models = [m for m in available_models if "sonnet" in m.lower() and ":0" in m and ":28k" not in m]
                if sonnet_models:
                    print(f"  推奨: {sonnet_models[0]}")
        else:
            print("⚠️  Claude 3モデルが見つかりません")
            print("   Bedrockモデルへのアクセスが有効化されているか確認してください")
        print()
    except Exception as e:
        print(f"⚠️  モデル一覧の取得に失敗しました: {e}")
        print("   モデルアクセスが有効化されていない可能性があります")
        print()
    
    # 実際のモデル呼び出しテスト
    try:
        print("モデル呼び出しテスト中...")
        payload = {
            "modelId": MODEL_ID,
            "contentType": "application/json",
            "accept": "*/*",
            "body": json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.3,
                "messages": [
                    {"role": "user", "content": "こんにちは。簡単に自己紹介してください（1文で）。"}
                ]
            })
        }
        
        response = bedrock.invoke_model(**payload)
        model_response = json.loads(response["body"].read())
        answer = model_response["content"][0]["text"]
        
        print("✓ Bedrockモデル呼び出しに成功しました！")
        print()
        print("回答:")
        print("-" * 60)
        print(answer)
        print("-" * 60)
        print()
        print("=" * 60)
        print("✓ すべてのテストに成功しました！")
        print("=" * 60)
        return True
        
    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        error_message = getattr(e, "response", {}).get("Error", {}).get("Message", str(e))
        
        print(f"✗ Bedrockモデル呼び出しに失敗しました")
        print(f"  エラーコード: {error_code}")
        print(f"  エラーメッセージ: {error_message}")
        print()
        
        if error_code == "UnrecognizedClientException":
            print("解決方法:")
            print("1. AWS認証情報が正しいか確認")
            print("   - .envファイルまたは~/.aws/credentialsの認証情報を確認")
            print("   - 認証情報が期限切れでないか確認")
            print("2. .envファイルを作成（存在しない場合）")
            print("   - python create_env_example.py を実行")
            print("   - または、backend/.envファイルを手動で作成")
            print("3. IAMユーザーにBedrock権限があるか確認")
            print("   - IAM → ユーザー → 許可を確認")
            print("   - AmazonBedrockFullAccess または bedrock:InvokeModel 権限が必要")
        elif error_code == "AccessDeniedException":
            print("解決方法:")
            print("1. IAMユーザーにBedrock権限を付与")
            print("   - IAM → ユーザー → 許可を追加 → AmazonBedrockFullAccess")
            print("2. 初回使用時は使用目的の提出が必要な場合があります")
            print("   - Playgroundで一度モデルを試す")
        elif error_code == "ResourceNotFoundException":
            print("解決方法:")
            print("1. モデルIDが正しいか確認")
            print(f"   現在のモデルID: {MODEL_ID}")
            print("2. 利用可能なモデル一覧を確認:")
            print("   python list_bedrock_models.py")
            print("3. モデルIDの形式を確認:")
            print("   - 正しい形式: anthropic.claude-3-sonnet-20240229-v1:0")
            print("   - 28k版は別のモデルIDの可能性があります")
            print("4. リージョンでモデルが利用可能か確認")
            print(f"   現在のリージョン: {AWS_REGION}")
        elif error_code == "ValidationException":
            print("解決方法:")
            print("1. モデルIDが正しいか確認")
            print(f"   現在のモデルID: {MODEL_ID}")
            print("2. リージョンでモデルが利用可能か確認")
            print(f"   現在のリージョン: {AWS_REGION}")
        else:
            print("詳細は BEDROCK_SETUP.md を参照してください")
            print()
            print("追加の確認事項:")
            print("1. .envファイルが存在するか: python check_env.py")
            print("2. .envファイルを作成: python create_env_example.py")
            print("3. ~/.aws/credentialsの認証情報が有効か確認")
        
        print()
        print("=" * 60)
        print("✗ テストに失敗しました")
        print("=" * 60)
        print()
        print("次のステップ:")
        if not os.path.exists(os.path.join(os.path.dirname(__file__), ".env")):
            print("1. .envファイルを作成: python create_env_example.py")
            print("2. .envファイルに認証情報を記入")
        print("3. 再度テストを実行: python test_bedrock.py")
        return False

if __name__ == "__main__":
    success = test_bedrock()
    sys.exit(0 if success else 1)

