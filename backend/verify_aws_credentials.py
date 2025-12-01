"""
AWS認証情報の有効性を確認するスクリプト
~/.aws/credentialsと.envファイルの認証情報を確認
"""
import boto3
import os
import sys

# .envファイルを読み込む
try:
    from dotenv import load_dotenv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print("✓ .envファイルを読み込みました")
except ImportError:
    print("⚠️  python-dotenvがインストールされていません")
except Exception as e:
    print(f"⚠️  .envファイルの読み込みに失敗: {e}")

def verify_aws_credentials():
    """AWS認証情報の有効性を確認"""
    print("=" * 60)
    print("AWS認証情報の有効性確認")
    print("=" * 60)
    print()
    
    # 1. 認証情報の取得元を確認
    print("1. 認証情報の取得元を確認")
    print("-" * 60)
    
    # 環境変数から取得
    env_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    env_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    env_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    
    # AWS認証情報ファイルから取得
    aws_creds_path = os.path.expanduser("~/.aws/credentials")
    aws_config_path = os.path.expanduser("~/.aws/config")
    
    print(f"環境変数 (AWS_ACCESS_KEY_ID): {'設定済み' if env_access_key else '未設定'}")
    print(f"環境変数 (AWS_SECRET_ACCESS_KEY): {'設定済み' if env_secret_key else '未設定'}")
    print(f"~/.aws/credentials: {'存在' if os.path.exists(aws_creds_path) else '不存在'}")
    print(f"~/.aws/config: {'存在' if os.path.exists(aws_config_path) else '不存在'}")
    print()
    
    # 認証情報の優先順位を確認
    if env_access_key:
        print("✓ 環境変数から認証情報を取得します（優先度: 高）")
        access_key = env_access_key
        secret_key = env_secret_key
        region = env_region
    elif os.path.exists(aws_creds_path):
        print("✓ ~/.aws/credentialsから認証情報を取得します（優先度: 中）")
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(aws_creds_path)
            if "default" in config:
                access_key = config["default"].get("aws_access_key_id", "")
                secret_key = config["default"].get("aws_secret_access_key", "")
                print(f"  Access Key ID: {access_key[:10]}...{access_key[-4:] if len(access_key) > 14 else ''}")
                print(f"  Secret Access Key: {'設定済み' if secret_key else '未設定'}")
            else:
                print("  ⚠️  [default]セクションが見つかりません")
                access_key = ""
                secret_key = ""
            
            # リージョンを取得
            if os.path.exists(aws_config_path):
                config_parser = configparser.ConfigParser()
                config_parser.read(aws_config_path)
                if "default" in config_parser:
                    region = config_parser["default"].get("region", "ap-northeast-1")
                else:
                    region = "ap-northeast-1"
            else:
                region = "ap-northeast-1"
        except Exception as e:
            print(f"  ✗ 認証情報ファイルの読み込みに失敗: {e}")
            access_key = ""
            secret_key = ""
            region = "ap-northeast-1"
    else:
        print("✗ 認証情報が見つかりません")
        print("  .envファイルまたは~/.aws/credentialsを設定してください")
        return False
    
    if not access_key or not secret_key:
        print("✗ 認証情報が不完全です")
        return False
    
    print(f"使用するリージョン: {region}")
    print()
    
    # 2. STSで認証情報の有効性を確認
    print("2. 認証情報の有効性を確認（STS GetCallerIdentity）")
    print("-" * 60)
    is_root_user = False
    try:
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
        
        print("✓ 認証情報は有効です")
        print(f"  User ID: {identity.get('UserId', 'N/A')}")
        print(f"  Account: {identity.get('Account', 'N/A')}")
        arn = identity.get('Arn', 'N/A')
        print(f"  ARN: {arn}")
        
        # ARNから認証情報の種類を判定
        if ":root" in arn or arn.endswith(":root"):
            print("  ⚠️  【重要】ルートユーザー（root user）の認証情報を使用しています")
            print("  セキュリティ上の理由から、ルートユーザーの認証情報の使用は推奨されません")
            print("  IAMユーザーを作成して、その認証情報を使用することを強く推奨します")
            is_root_user = True
        elif ":user/" in arn:
            user_name_from_arn = arn.split("/")[-1]
            print(f"  IAMユーザー名（ARNから）: {user_name_from_arn}")
        elif ":role/" in arn:
            role_name = arn.split("/")[-1]
            print(f"  IAMロール名（ARNから）: {role_name}")
            print("  ⚠️  IAMロールを使用しています。一時認証情報の可能性があります")
        print()
        
    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        error_message = getattr(e, "response", {}).get("Error", {}).get("Message", str(e))
        
        print(f"✗ 認証情報が無効です")
        print(f"  エラーコード: {error_code}")
        print(f"  エラーメッセージ: {error_message}")
        print()
        
        if error_code == "InvalidClientTokenId":
            print("【診断】アクセスキーIDが無効です")
            print("解決方法:")
            print("1. AWSコンソールでアクセスキーIDを確認")
            print("2. 新しいアクセスキーを生成")
            print("3. .envファイルまたは~/.aws/credentialsを更新")
        elif error_code == "SignatureDoesNotMatch":
            print("【診断】シークレットアクセスキーが間違っています")
            print("解決方法:")
            print("1. シークレットアクセスキーを確認")
            print("2. コピー&ペースト時に余分なスペースが入っていないか確認")
            print("3. .envファイルまたは~/.aws/credentialsを更新")
        elif error_code == "TokenRefreshRequired":
            print("【診断】認証情報の期限が切れています")
            print("解決方法:")
            print("1. 新しいアクセスキーを生成")
            print("2. .envファイルまたは~/.aws/credentialsを更新")
        
        return False
    
    # 3. IAM権限の確認
    print("3. IAM権限の確認")
    print("-" * 60)
    
    # ルートユーザーの場合はスキップ
    if is_root_user:
        print("⚠️  ルートユーザーのため、IAM権限の確認をスキップします")
        print()
        print("【重要】セキュリティ上の推奨事項:")
        print("1. ルートユーザーの認証情報は日常的な使用には使用しないでください")
        print("2. IAMユーザーを作成して、その認証情報を使用してください")
        print("3. ルートユーザーは管理者タスクのみに使用してください")
        print()
        print("IAMユーザーの作成方法:")
        print("1. AWSコンソール → IAM → ユーザー → ユーザーを追加")
        print("2. ユーザー名を入力")
        print("3. 「プログラムによるアクセス」を選択")
        print("4. 適切な権限ポリシーをアタッチ（例：AmazonBedrockFullAccess）")
        print("5. アクセスキーIDとシークレットアクセスキーを保存")
        print("6. .envファイルまたは~/.aws/credentialsに設定")
        print()
    else:
        try:
            iam = boto3.client("iam", region_name=region)
            
            # 認証情報の種類を確認
            try:
                user_info = iam.get_user()
                user_name = user_info.get("User", {}).get("UserName")
                user_arn = user_info.get("User", {}).get("Arn", "")
                
                if user_name:
                    print(f"✓ IAMユーザー: {user_name}")
                    print(f"  ARN: {user_arn}")
                    
                    # アタッチされているポリシーを確認
                    try:
                        attached_policies = iam.list_attached_user_policies(UserName=user_name)
                        policy_names = [p["PolicyName"] for p in attached_policies.get("AttachedPolicies", [])]
                        
                        print(f"  アタッチされているポリシー: {len(policy_names)}件")
                        for policy_name in policy_names[:5]:  # 最初の5件のみ表示
                            print(f"    - {policy_name}")
                        
                        # Bedrock権限があるか確認
                        has_bedrock_access = any("Bedrock" in name for name in policy_names)
                        if has_bedrock_access:
                            print("  ✓ Bedrock権限が確認されました")
                        else:
                            print("  ⚠️  Bedrock権限が見つかりません")
                            print("     AmazonBedrockFullAccessを付与することを推奨します")
                    except Exception as e:
                        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
                        if error_code == "AccessDenied":
                            print("  ⚠️  ポリシー一覧の取得に失敗（権限不足）")
                            print("     ただし、認証情報自体は有効です")
                        else:
                            print(f"  ⚠️  ポリシー一覧の取得に失敗: {e}")
                else:
                    print("⚠️  IAMユーザー名を取得できませんでした")
                    print(f"  ARN: {user_arn}")
                    print("  認証情報は有効ですが、IAMユーザー情報の取得に失敗しました")
            except Exception as e:
                error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
                if error_code == "AccessDenied":
                    print("⚠️  IAMユーザー情報の取得に失敗（権限不足）")
                    print("   認証情報は有効ですが、IAM権限が不足している可能性があります")
                elif error_code == "NoSuchEntity":
                    # ARNから情報を取得（既に取得済みのidentityを使用）
                    if identity:
                        arn = identity.get("Arn", "")
                        print(f"✓ 認証情報は有効です")
                        print(f"  ARN: {arn}")
                        print("  ⚠️  IAMユーザーとして認識されていません")
                        print("  認証情報の種類:")
                        if ":user/" in arn:
                            print("    - IAMユーザー（ARNに含まれるユーザー名を確認してください）")
                        elif ":role/" in arn:
                            print("    - IAMロール（一時認証情報を使用している可能性があります）")
                        else:
                            print("    - その他の認証情報")
                        print()
                        print("  注意: IAMロールや一時認証情報の場合、直接ポリシーを確認できません")
                        print("  ただし、Bedrockアクセステストで権限を確認できます")
                    else:
                        print(f"⚠️  IAMユーザー情報の取得に失敗: {e}")
                else:
                    print(f"⚠️  IAMユーザー情報の取得に失敗: {e}")
            print()
        except Exception as e:
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
            if error_code == "AccessDenied":
                print("⚠️  IAM権限の確認に失敗（権限不足）")
                print("   ただし、認証情報自体は有効です")
            else:
                print(f"⚠️  IAM権限の確認に失敗: {e}")
            print()
    
    # 4. Bedrockアクセスの確認
    print("4. Bedrockアクセスの確認")
    print("-" * 60)
    try:
        bedrock = boto3.client("bedrock", region_name=region)
        response = bedrock.list_foundation_models()
        models = response.get("modelSummaries", [])
        print(f"✓ Bedrockアクセス成功: {len(models)}件のモデルが見つかりました")
        
        # Claude 3モデルを確認
        claude_models = [m for m in models if "claude-3" in m.get("modelId", "").lower()]
        if claude_models:
            print(f"  Claude 3モデル: {len(claude_models)}件")
            for model in claude_models[:3]:
                print(f"    - {model.get('modelId')}")
        print()
        
    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        error_message = getattr(e, "response", {}).get("Error", {}).get("Message", str(e))
        
        print(f"✗ Bedrockアクセスに失敗")
        print(f"  エラーコード: {error_code}")
        print(f"  エラーメッセージ: {error_message}")
        print()
        
        if error_code == "AccessDeniedException":
            print("【診断】Bedrock権限が不足しています")
            print("解決方法:")
            print("1. IAMユーザーにAmazonBedrockFullAccessを付与")
            print("2. または、bedrock:ListFoundationModels権限を付与")
        elif error_code == "UnrecognizedClientException":
            print("【診断】認証情報が無効です")
            print("解決方法:")
            print("1. 認証情報を再確認")
            print("2. 新しいアクセスキーを生成")
    
    print("=" * 60)
    print("確認完了")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = verify_aws_credentials()
    sys.exit(0 if success else 1)

