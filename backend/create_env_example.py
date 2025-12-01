"""
.envファイルの作成を支援するスクリプト
"""
import os

def create_env_file():
    """`.env`ファイルのテンプレートを作成"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    env_example_path = os.path.join(script_dir, ".env.example")
    
    print("=" * 60)
    print(".envファイルの作成支援")
    print("=" * 60)
    
    # .env.exampleが存在するか確認
    if os.path.exists(env_example_path):
        print(f"✓ .env.exampleファイルが見つかりました: {env_example_path}")
        with open(env_example_path, "r", encoding="utf-8") as f:
            example_content = f.read()
        print("\n.env.exampleの内容:")
        print("-" * 60)
        print(example_content)
        print("-" * 60)
    
    # .envファイルが存在するか確認
    if os.path.exists(env_path):
        print(f"\n⚠️  .envファイルは既に存在します: {env_path}")
        response = input("上書きしますか？ (y/N): ")
        if response.lower() != 'y':
            print("キャンセルしました")
            return
    
    # テンプレートを作成
    template = """# AWS認証情報
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=ap-northeast-1

# Bedrock設定
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0:28k

# S3設定（オプション）
VECTOR_BUCKET=your-s3-bucket-name
VECTOR_INDEX=company-rag-embeddings-poc
"""
    
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(template)
        print(f"\n✓ .envファイルを作成しました: {env_path}")
        print("\n次のステップ:")
        print("1. .envファイルを開く")
        print("2. your-access-key-id と your-secret-access-key を実際の値に置き換える")
        print("3. ファイルを保存")
    except Exception as e:
        print(f"\n✗ .envファイルの作成に失敗しました: {e}")

if __name__ == "__main__":
    create_env_file()

