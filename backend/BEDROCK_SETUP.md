# AWS Bedrock 設定ガイド

RAGシステムでBedrockを使用して高品質な回答を生成するための設定方法を説明します。

## 前提条件

1. AWSアカウントを持っていること
2. AWS認証情報（アクセスキーID、シークレットアクセスキー）を取得していること
3. IAMユーザーにBedrockへのアクセス権限があること

## ステップ1: Bedrockモデルへのアクセス（自動有効化）

**重要**: 2024年以降、Bedrockのサーバーレス基盤モデルは自動的に有効化されるようになりました。手動でのアクセス有効化は不要です。

### 新しい仕様（2024年以降）

AWS Bedrockのサーバーレス基盤モデル（Claude 3など）は、**初回の呼び出し時に自動的に有効化**されます。

#### 主な変更点

1. **モデルアクセスの手動有効化が不要**
   - 以前は「モデルアクセス」ページで手動で有効化する必要がありました
   - 現在は、モデルを初めて呼び出すと自動的に有効化されます

2. **Anthropicモデルの初回使用時の注意**
   - Anthropicモデル（Claude 3など）を初めて使用する場合、**使用目的の提出が必要**な場合があります
   - これは初回のみで、以降は不要です

3. **IAMポリシーによる制御**
   - アカウント管理者は、IAMポリシーやService Control Policies（SCP）を使用してモデルアクセスを制限できます
   - セキュリティとコスト管理の観点から推奨されます

### 初回使用時の手順

1. **モデルカタログで確認**
   - AWSコンソール → Bedrock → モデルカタログ
   - 使用したいモデル（例：Claude 3 Sonnet）を選択

2. **Playgroundで試す（オプション）**
   - モデル詳細ページから「Playground」を開く
   - 初回使用時は使用目的の入力が求められる場合があります

3. **プログラムから直接呼び出す**
   - コードから`InvokeModel`または`Converse` APIを呼び出す
   - 初回呼び出し時に自動的に有効化されます

### 使用目的の提出が必要な場合

Anthropicモデルを初めて使用する際、以下のような使用目的の提出が求められる場合があります：

- **使用目的の例**:
  - RAGシステムでの質問応答
  - ドキュメント要約
  - コンテンツ生成
  - カスタマーサポート

- **提出方法**:
  - Playgroundで初回使用時に表示されるフォームに入力
  - または、モデル呼び出し時のエラーメッセージに従う

## ステップ2: IAMユーザーにBedrock権限を付与

### 1. IAMコンソールでユーザーを選択

1. AWSコンソールで「IAM」サービスを選択
2. 左側のメニューから「ユーザー」を選択
3. Bedrockを使用するIAMユーザーを選択

### 2. 権限ポリシーをアタッチ

1. 「許可」タブを選択
2. 「許可を追加」をクリック
3. 「ポリシーを直接アタッチ」を選択
4. 以下のポリシーを検索して選択：
   - `AmazonBedrockFullAccess`（フルアクセス）
   - または、最小権限のカスタムポリシー（下記参照）

### 3. 最小権限のカスタムポリシー（推奨）

以下のJSONポリシーを作成してアタッチ：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": [
        "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
        "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
      ]
    }
  ]
}
```

## ステップ3: 環境変数の設定

### 方法1: .envファイルを使用（推奨）

`backend/.env`ファイルを作成または編集：

```env
# AWS認証情報
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=ap-northeast-1

# Bedrock設定
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0:28k

# S3設定（オプション）
VECTOR_BUCKET=your-s3-bucket-name
VECTOR_INDEX=company-rag-embeddings-poc
```

### 方法2: 環境変数で設定

**PowerShellの場合：**
```powershell
$env:AWS_ACCESS_KEY_ID="your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY="your-secret-access-key"
$env:AWS_REGION="ap-northeast-1"
$env:BEDROCK_MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"
```

**CMDの場合：**
```cmd
set AWS_ACCESS_KEY_ID=your-access-key-id
set AWS_SECRET_ACCESS_KEY=your-secret-access-key
set AWS_REGION=ap-northeast-1
set BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0:28k
```

### 方法3: AWS認証情報ファイル

`C:\Users\<ユーザー名>\.aws\credentials`:
```ini
[default]
aws_access_key_id = your-access-key-id
aws_secret_access_key = your-secret-access-key
```

`C:\Users\<ユーザー名>\.aws\config`:
```ini
[default]
region = ap-northeast-1
```

## ステップ4: バックエンドサーバーの起動

環境変数を設定した後、バックエンドサーバーを起動：

```bash
cd backend
uvicorn main:app --reload --port 8000
```

## ステップ5: 動作確認

### 1. ログで確認

バックエンドサーバーの起動時に、以下のログが表示されれば成功：

```
INFO: Bedrockクライアントの初期化に失敗しました: ...
```

または、エラーが表示されない場合は正常に初期化されています。

### 2. RAG検索で確認

1. フロントエンドでRAG検索を実行
2. 自然な日本語の回答が生成されれば成功
3. 「※ より詳細な回答には、Bedrockの設定が必要です」というメッセージが表示されないことを確認

### 3. Pythonスクリプトで確認

`backend/test_bedrock.py`を作成：

```python
import boto3
import json
import os

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

try:
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    
    # テストプロンプト
    payload = {
        "modelId": MODEL_ID,
        "contentType": "application/json",
        "accept": "*/*",
        "body": json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.3,
            "messages": [
                {"role": "user", "content": "こんにちは。簡単に自己紹介してください。"}
            ]
        })
    }
    
    response = bedrock.invoke_model(**payload)
    model_response = json.loads(response["body"].read())
    answer = model_response["content"][0]["text"]
    
    print("✓ Bedrock接続成功！")
    print(f"回答: {answer}")
except Exception as e:
    print(f"✗ Bedrock接続失敗: {e}")
    print("\n確認事項:")
    print("1. AWS認証情報が正しく設定されているか")
    print("2. Bedrockモデルへのアクセスが有効化されているか")
    print("3. IAMユーザーにBedrock権限があるか")
    print("4. リージョンがap-northeast-1であるか")
```

実行：
```bash
cd backend
python test_bedrock.py
```

## トラブルシューティング

### エラー1: "AccessDeniedException"

**原因**: IAM権限が不足している、または初回使用時の使用目的提出が必要

**解決方法**:
1. **IAM権限の確認**
   - IAMユーザーにBedrock権限（`bedrock:InvokeModel`）が付与されているか確認
   - 必要に応じて`AmazonBedrockFullAccess`ポリシーをアタッチ

2. **初回使用時の対応**
   - Anthropicモデルの場合、初回使用時に使用目的の提出が必要な場合があります
   - Playgroundで一度モデルを試すか、エラーメッセージに従って使用目的を提出

3. **IAMポリシーの確認**
   - アカウントレベルでSCP（Service Control Policies）が設定されていないか確認
   - 組織の管理者に確認が必要な場合があります

### エラー2: "ValidationException"

**原因**: モデルIDが間違っている、またはリージョンで利用できない

**解決方法**:
1. モデルIDを確認（`anthropic.claude-3-sonnet-20240229-v1:0`）
2. リージョンが`ap-northeast-1`であることを確認
3. 利用可能なモデルを確認：
   ```python
   import boto3
   bedrock = boto3.client("bedrock", region_name="ap-northeast-1")
   models = bedrock.list_foundation_models()
   print([m["modelId"] for m in models["modelSummaries"]])
   ```

### エラー3: "UnrecognizedClientException"

**原因**: AWS認証情報が正しく設定されていない

**解決方法**:
1. 環境変数を確認
2. AWS認証情報ファイルを確認
3. バックエンドサーバーを再起動

### エラー4: タイムアウト

**原因**: ネットワーク接続の問題、またはリージョンが遠い

**解決方法**:
1. インターネット接続を確認
2. リージョンを`ap-northeast-1`に設定（日本に最も近い）

## 利用可能なモデル

### Claude 3 Sonnet（推奨）
- **モデルID**: `anthropic.claude-3-sonnet-20240229-v1:0`
- **特徴**: バランスの取れた性能、高品質な回答
- **用途**: 一般的なRAGシステム

### Claude 3 Haiku
- **モデルID**: `anthropic.claude-3-haiku-20240307-v1:0`
- **特徴**: 高速、低コスト
- **用途**: 大量のリクエストを処理する場合

### Claude 3 Opus
- **モデルID**: `anthropic.claude-3-opus-20240229-v1:0`
- **特徴**: 最高品質、高コスト
- **用途**: 高品質な回答が必要な場合

## コストについて

Bedrockの使用には料金がかかります。詳細は以下を参照：
- [Amazon Bedrock 料金](https://aws.amazon.com/jp/bedrock/pricing/)

概算（Claude 3 Sonnet）:
- 入力: $3.00 / 1Mトークン
- 出力: $15.00 / 1Mトークン

## 重要な注意事項

### モデルアクセスの自動有効化について

- **サーバーレス基盤モデル**: Claude 3、Llama 2などは自動的に有効化されます
- **AWS Marketplaceモデル**: 初回呼び出し時に、AWS Marketplace権限を持つユーザーが一度呼び出す必要があります
- **プロビジョニング済みモデル**: 従来通り、手動でのプロビジョニングが必要です

### セキュリティとコスト管理

- **IAMポリシー**: 必要最小限の権限のみを付与することを推奨
- **Service Control Policies**: 組織レベルでモデルアクセスを制限可能
- **CloudWatch**: モデル使用量を監視してコストを管理

## 参考リンク

- [Amazon Bedrock ドキュメント](https://docs.aws.amazon.com/bedrock/)
- [Claude 3 モデル仕様](https://docs.anthropic.com/claude/docs/models-overview)
- [AWS認証情報の設定](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [Bedrock モデルカタログ](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)

