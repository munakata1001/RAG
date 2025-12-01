"""
.envファイルの内容を確認するスクリプト（機密情報はマスク）
"""
import os

def check_env_file():
    """.envファイルの存在と内容を確認"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    
    print("=" * 60)
    print(".envファイルの確認")
    print("=" * 60)
    print(f"パス: {env_path}")
    print(f"存在: {os.path.exists(env_path)}")
    print()
    
    if not os.path.exists(env_path):
        print("⚠️  .envファイルが見つかりません")
        print(f"   以下のパスに作成してください: {env_path}")
        print()
        print("例:")
        print("AWS_ACCESS_KEY_ID=your-access-key-id")
        print("AWS_SECRET_ACCESS_KEY=your-secret-access-key")
        print("AWS_REGION=ap-northeast-1")
        print("BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0:28k")
        return
    
    print("✓ .envファイルが見つかりました")
    print()
    print("内容（機密情報はマスク）:")
    print("-" * 60)
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    print(f"{i:3}: {line}")
                    continue
                
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 機密情報をマスク
                    if "SECRET" in key.upper() or "KEY" in key.upper():
                        if value:
                            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
                            print(f"{i:3}: {key}={masked}")
                        else:
                            print(f"{i:3}: {key}=（空）")
                    else:
                        print(f"{i:3}: {key}={value}")
                else:
                    print(f"{i:3}: {line}")
    except Exception as e:
        print(f"エラー: {e}")
    
    print("-" * 60)
    print()
    
    # python-dotenvで読み込んで確認
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)
        
        print("環境変数の読み込み結果:")
        print("-" * 60)
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region = os.getenv("AWS_REGION")
        model_id = os.getenv("BEDROCK_MODEL_ID")
        
        print(f"AWS_ACCESS_KEY_ID: {'✓ 設定済み' if access_key else '✗ 未設定'}")
        if access_key:
            if len(access_key) > 14:
                print(f"  値: {access_key[:10]}...{access_key[-4:]}")
            else:
                print(f"  値: {access_key}")
        else:
            print("  ⚠️  値が空です。.envファイルに AWS_ACCESS_KEY_ID=your-key を記入してください")
        
        print(f"AWS_SECRET_ACCESS_KEY: {'✓ 設定済み' if secret_key else '✗ 未設定'}")
        if not secret_key:
            print("  ⚠️  値が空です。.envファイルに AWS_SECRET_ACCESS_KEY=your-secret を記入してください")
        
        print(f"AWS_REGION: {region or '未設定（デフォルト: ap-northeast-1）'}")
        print(f"BEDROCK_MODEL_ID: {model_id or '未設定（デフォルト: anthropic.claude-3-sonnet-20240229-v1:0）'}")
        print("-" * 60)
        
        # 問題の診断
        if not access_key or not secret_key:
            print()
            print("⚠️  問題の診断:")
            print("   .envファイルに値が記入されていない可能性があります")
            print()
            print("   正しい形式:")
            print("   AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
            print("   AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
            print()
            print("   注意:")
            print("   - =の前後にスペースを入れない")
            print("   - 値にyour-access-key-idなどのプレースホルダーが残っていないか確認")
            print("   - コメント行（#で始まる行）は無視されます")
        
    except ImportError:
        print("⚠️  python-dotenvがインストールされていません")
        print("   pip install python-dotenv でインストールしてください")

if __name__ == "__main__":
    check_env_file()

