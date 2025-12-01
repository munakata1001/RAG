# AWS Bedrock モデル有効化の手順

Bedrockモデルを使用するための有効化手順を詳しく説明します。

## 重要な変更（2024年以降）

**以前**: モデルアクセスのページで手動で有効化する必要があった
**現在**: サーバーレス基盤モデルは**初回呼び出し時に自動的に有効化**される

## 自動有効化の仕組み

### サーバーレス基盤モデル（Claude 3、Llama 2など）

1. **初回呼び出し時に自動有効化**
   - モデルを初めて呼び出すと、自動的に有効化されます
   - 手動での有効化は不要です

2. **Anthropicモデルの初回使用時**
   - Claude 3モデルを初めて使用する場合、**使用目的の提出**が必要な場合があります
   - これは初回のみで、以降は不要です

3. **AWS Marketplaceモデル**
   - AWS Marketplaceから提供されるモデルの場合
   - 初回は、AWS Marketplace権限を持つユーザーが一度呼び出す必要があります
   - 一度有効化されると、アカウント全体で利用可能になります

## 手順1: IAM権限の確認・設定

### 1.1 IAMユーザーにBedrock権限を付与

1. **AWSコンソールにログイン**
   - https://console.aws.amazon.com/

2. **IAMサービスを開く**
   - 検索バーに「IAM」と入力
   - 「IAM」サービスを選択

3. **ユーザーを選択**
   - 左メニューから「ユーザー」をクリック
   - Bedrockを使用するIAMユーザーを選択

4. **権限を追加**
   - 「許可」タブをクリック
   - 「許可を追加」ボタンをクリック
   - 「ポリシーを直接アタッチ」を選択
   - 検索バーに「Bedrock」と入力
   - **`AmazonBedrockFullAccess`** を選択
   - 「次へ」→「許可を追加」をクリック

詳細は `IAM_BEDROCK_SETUP.md` を参照してください。

## 手順2: 認証情報の設定

### 2.1 .envファイルを作成

`backend/.env`ファイルを作成：

```env
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=ap-northeast-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### 2.2 認証情報の確認

```bash
cd backend
python check_env.py
```

## 手順3: 初回モデル呼び出し（自動有効化）

### 3.1 プログラムから呼び出す（推奨）

バックエンドサーバーを起動して、RAG検索を実行：

```bash
cd backend
uvicorn main:app --reload --port 8000
```

初回呼び出し時に：
- モデルが自動的に有効化されます
- Anthropicモデルの場合、使用目的の入力が求められる場合があります

### 3.2 Playgroundで試す（オプション）

1. **AWSコンソールでBedrockを開く**
   - 検索バーに「Bedrock」と入力
   - 「Amazon Bedrock」サービスを選択

2. **モデルカタログを開く**
   - 左メニューから「モデルカタログ」を選択

3. **モデルを選択**
   - 「Claude 3 Sonnet」などのモデルを選択

4. **Playgroundを開く**
   - 「Playgroundで開く」ボタンをクリック

5. **初回使用時の使用目的入力**
   - 初回使用時は、使用目的の入力フォームが表示される場合があります
   - 使用目的を入力（例：「RAGシステムでの質問応答」）
   - 「送信」をクリック

6. **テスト実行**
   - 簡単なプロンプトを入力してテスト
   - 成功すれば、モデルが有効化されています

## 手順4: 動作確認

### 4.1 テストスクリプトで確認

```bash
cd backend
python test_bedrock.py
```

成功すると、Bedrockからの回答が表示されます。

### 4.2 モデル一覧で確認

```bash
cd backend
python list_bedrock_models.py
```

利用可能なモデル一覧が表示されます。

## トラブルシューティング

### エラー1: "UnrecognizedClientException"

**原因**: 認証情報が無効または設定されていない

**解決方法**:
1. `.env`ファイルの認証情報を確認
2. 認証情報が正しいか確認
3. 認証情報が期限切れでないか確認
4. IAMユーザーにBedrock権限があるか確認

### エラー2: "AccessDeniedException"

**原因**: IAM権限が不足している

**解決方法**:
1. IAMユーザーに`AmazonBedrockFullAccess`ポリシーをアタッチ
2. または、`bedrock:InvokeModel`権限を持つカスタムポリシーを作成

### エラー3: 使用目的の提出が必要

**症状**: 初回使用時にエラーメッセージが表示される

**解決方法**:
1. Playgroundで一度モデルを試す
2. 使用目的の入力フォームに入力
3. または、エラーメッセージに従って使用目的を提出

### エラー4: モデルが見つからない

**原因**: モデルIDが間違っている、またはリージョンで利用できない

**解決方法**:
1. `python list_bedrock_models.py`で利用可能なモデルを確認
2. 正しいモデルIDを使用
3. リージョンが`ap-northeast-1`であることを確認

## 使用目的の例

Anthropicモデルの初回使用時に求められる使用目的の例：

- RAGシステムでの質問応答
- ドキュメント要約
- コンテンツ生成
- カスタマーサポート
- コード生成・レビュー
- データ分析

## まとめ

### 簡略化された手順（2024年以降）

1. ✅ IAMユーザーにBedrock権限を付与
2. ✅ 認証情報を設定（.envファイル）
3. ✅ モデルを呼び出す（自動有効化）
4. ✅ 初回使用時は使用目的を提出（必要な場合のみ）

### 以前の手順（廃止）

~~1. コンソールで「モデルアクセス」ページを開く~~
~~2. モデルを選択してリクエスト~~
~~3. 承認を待つ（数時間）~~

**注意**: モデルアクセスのページは廃止されました。手動での有効化は不要です。

## 参考リンク

- [Amazon Bedrock ドキュメント](https://docs.aws.amazon.com/bedrock/)
- [Bedrock モデルカタログ](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [IAM ポリシーの作成](https://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/access_policies_create.html)

