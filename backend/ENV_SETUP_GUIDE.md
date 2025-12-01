# .envファイルの作成ガイド

## 問題

`.env`ファイルが存在しない、または正しく読み込まれていない場合の対処法です。

## 解決方法

### 方法1: スクリプトで作成（推奨）

```bash
cd backend
python create_env_example.py
```

このスクリプトは`.env`ファイルのテンプレートを作成します。

### 方法2: 手動で作成

1. `backend`ディレクトリに`.env`ファイルを作成
2. 以下の内容を記入：

```env
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=ap-northeast-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0:28k
```

### 方法3: Windowsでファイルを作成する場合

**PowerShellの場合：**
```powershell
cd backend
New-Item -Path .env -ItemType File -Force
notepad .env
```

**エクスプローラーで作成する場合：**
1. `backend`フォルダを開く
2. 新しいテキストファイルを作成
3. ファイル名を`.env`に変更（拡張子なし）
   - 注意: Windowsでは「ファイル名を変更」で「.env.txt」にならないように注意
   - 「名前を付けて保存」で「すべてのファイル」を選択し、`.env`と入力

## .envファイルの形式

- `=`の前後にスペースを入れない
- 値にスペースがある場合は引用符で囲む（通常は不要）
- コメントは`#`で始める
- 改行コードは`LF`または`CRLF`のどちらでも可
- エンコーディングは`UTF-8`を推奨

## 確認方法

```bash
cd backend
python check_env.py
```

このスクリプトで`.env`ファイルの内容を確認できます。

## .aws/credentialsを使用する場合

`.env`ファイルがなくても、`~/.aws/credentials`ファイルがあれば、boto3は自動的にそこから認証情報を読み込みます。

ただし、`UnrecognizedClientException`エラーが発生している場合：
1. 認証情報が正しいか確認
2. 認証情報が期限切れでないか確認
3. IAMユーザーにBedrock権限があるか確認

## トラブルシューティング

### .envファイルが読み込まれない

1. `python-dotenv`がインストールされているか確認：
   ```bash
   pip install python-dotenv
   ```

2. ファイル名が正確か確認（`.env.txt`ではなく`.env`）

3. ファイルの場所が正しいか確認（`backend/.env`）

4. ファイルのエンコーディングがUTF-8か確認

