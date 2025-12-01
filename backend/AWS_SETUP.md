# AWS認証情報の設定方法

S3やBedrockを使用するために、AWS認証情報を設定する方法を説明します。

## 方法1: 環境変数で設定（推奨：開発環境）

### Windows PowerShell の場合

```powershell
# 現在のセッションのみ有効
$env:AWS_ACCESS_KEY_ID="your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY="your-secret-access-key"
$env:AWS_REGION="ap-northeast-1"

# バックエンドサーバーを起動
cd backend
uvicorn main:app --reload --port 8000
```

### Windows CMD の場合

```cmd
set AWS_ACCESS_KEY_ID=your-access-key-id
set AWS_SECRET_ACCESS_KEY=your-secret-access-key
set AWS_REGION=ap-northeast-1

cd backend
uvicorn main:app --reload --port 8000
```

### 永続的に設定する場合（Windows）

1. **システムの環境変数として設定**
   - 「システムのプロパティ」→「環境変数」を開く
   - 「ユーザー環境変数」または「システム環境変数」に以下を追加：
     - `AWS_ACCESS_KEY_ID` = `your-access-key-id`
     - `AWS_SECRET_ACCESS_KEY` = `your-secret-access-key`
     - `AWS_REGION` = `ap-northeast-1`

2. **PowerShellプロファイルに設定**
   ```powershell
   # プロファイルを編集
   notepad $PROFILE
   
   # 以下を追加
   $env:AWS_ACCESS_KEY_ID="your-access-key-id"
   $env:AWS_SECRET_ACCESS_KEY="your-secret-access-key"
   $env:AWS_REGION="ap-northeast-1"
   ```

## 方法2: AWS認証情報ファイル（推奨：本番環境）

### 1. AWS認証情報ファイルを作成

Windowsの場合、以下のパスにファイルを作成します：
```
C:\Users\<ユーザー名>\.aws\credentials
```

ファイルの内容：
```ini
[default]
aws_access_key_id = your-access-key-id
aws_secret_access_key = your-secret-access-key
```

### 2. AWS設定ファイルを作成

以下のパスにファイルを作成します：
```
C:\Users\<ユーザー名>\.aws\config
```

ファイルの内容：
```ini
[default]
region = ap-northeast-1
```

### 3. ファイルの権限設定（セキュリティ）

認証情報ファイルは機密情報を含むため、適切な権限を設定してください：

```powershell
# 現在のユーザーのみが読み取り可能にする
icacls "$env:USERPROFILE\.aws\credentials" /inheritance:r /grant "$env:USERNAME:(R)"
icacls "$env:USERPROFILE\.aws\config" /inheritance:r /grant "$env:USERNAME:(R)"
```

## 方法3: .envファイルを使用（開発環境向け）

### 1. python-dotenvをインストール

```bash
pip install python-dotenv
```

### 2. .envファイルを作成

`backend/.env`ファイルを作成：
```env
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=ap-northeast-1
VECTOR_BUCKET=your-s3-bucket-name
VECTOR_INDEX=company-rag-embeddings-poc
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### 3. main.pyで.envを読み込む

`backend/main.py`の先頭に以下を追加：
```python
from dotenv import load_dotenv
load_dotenv()
```

**注意**: `.env`ファイルは`.gitignore`に追加して、Gitにコミットしないようにしてください。

## AWS認証情報の取得方法

### 1. IAMユーザーを作成

1. AWSコンソールにログイン
2. IAMサービスに移動
3. 「ユーザー」→「ユーザーを追加」
4. ユーザー名を入力
5. 「プログラムによるアクセス」を選択
6. 適切な権限ポリシーをアタッチ（例：`AmazonS3FullAccess`, `AmazonBedrockFullAccess`）
7. アクセスキーIDとシークレットアクセスキーを保存

### 2. 必要な権限

以下の権限が必要です：
- **S3**: `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`
- **Bedrock**: `bedrock:InvokeModel`, `bedrock:ListFoundationModels`

最小権限のポリシー例：
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

## 設定の確認方法

### 1. AWS CLIで確認（インストール済みの場合）

```bash
aws configure list
```

### 2. Pythonスクリプトで確認

```python
import boto3
import os

print("AWS_ACCESS_KEY_ID:", os.getenv("AWS_ACCESS_KEY_ID")[:10] + "..." if os.getenv("AWS_ACCESS_KEY_ID") else "未設定")
print("AWS_SECRET_ACCESS_KEY:", "設定済み" if os.getenv("AWS_SECRET_ACCESS_KEY") else "未設定")
print("AWS_REGION:", os.getenv("AWS_REGION", "未設定"))

# S3クライアントのテスト
try:
    s3 = boto3.client("s3", region_name="ap-northeast-1")
    buckets = s3.list_buckets()
    print("✓ S3接続成功")
    print("利用可能なバケット:", [b["Name"] for b in buckets.get("Buckets", [])])
except Exception as e:
    print("✗ S3接続失敗:", e)
```

## トラブルシューティング

### 認証情報が読み込まれない場合

1. **環境変数の確認**
   ```powershell
   echo $env:AWS_ACCESS_KEY_ID
   echo $env:AWS_SECRET_ACCESS_KEY
   ```

2. **認証情報ファイルのパス確認**
   ```powershell
   echo $env:USERPROFILE\.aws\credentials
   ```

3. **バックエンドサーバーの再起動**
   - 環境変数を設定した後は、サーバーを再起動してください

### セキュリティのベストプラクティス

1. **アクセスキーのローテーション**
   - 定期的にアクセスキーを更新する
   - 古いキーは無効化する

2. **最小権限の原則**
   - 必要最小限の権限のみを付与する

3. **認証情報の保護**
   - `.env`ファイルや認証情報ファイルをGitにコミットしない
   - `.gitignore`に追加する

4. **本番環境ではIAMロールを使用**
   - EC2やECSで実行する場合は、IAMロールを使用することを推奨

## 現在の設定確認

バックエンドサーバーのログで、以下のメッセージが表示されれば設定成功です：
```
INFO: S3/Bedrockクライアントを初期化しました（リージョン: ap-northeast-1）
```

設定されていない場合は：
```
DEBUG: S3/Bedrockクライアントの初期化に失敗しました。ローカルモードで動作します
```

