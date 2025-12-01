# IAMユーザーにBedrock権限を付与する方法

IAMユーザーにBedrock権限を付与する詳細な手順を説明します。

## 前提条件

- AWSアカウントにログインしていること
- IAMユーザーが既に作成されていること
- 管理者権限があること（IAMユーザーを作成・編集できる権限）

## ステップ1: IAMコンソールにアクセス

### 1.1 AWSコンソールにログイン

1. ブラウザで [AWSコンソール](https://console.aws.amazon.com/) にアクセス
2. AWSアカウントでログイン

### 1.2 IAMサービスを開く

1. 画面上部の検索バーに「IAM」と入力
2. 「IAM」サービスを選択
   - または、サービス一覧から「セキュリティ、アイデンティティ、コンプライアンス」→「IAM」を選択

## ステップ2: ユーザーを選択

### 2.1 ユーザー一覧を表示

1. 左側のメニューから「ユーザー」をクリック
2. Bedrockを使用するIAMユーザーを探す
   - ユーザー名で検索できる場合は検索バーを使用

### 2.2 ユーザーを選択

1. ユーザー名をクリックして詳細ページを開く

## ステップ3: 権限を確認・追加

### 3.1 現在の権限を確認

1. ユーザー詳細ページで「許可」タブをクリック
2. 現在アタッチされているポリシーを確認
   - 「ユーザーベースのポリシー」セクション
   - 「グループから継承されたポリシー」セクション
   - 「インラインポリシー」セクション

### 3.2 権限を追加

1. 「許可を追加」ボタンをクリック
2. 以下のいずれかの方法を選択：

#### 方法A: 既存のポリシーを直接アタッチ（推奨・簡単）

1. 「ポリシーを直接アタッチ」を選択
2. 検索バーに「Bedrock」と入力
3. 以下のポリシーを検索して選択：
   - **`AmazonBedrockFullAccess`** （フルアクセス・推奨）
   - または **`AmazonBedrockReadOnlyAccess`** （読み取り専用・テスト用）
4. チェックボックスをオンにして選択
5. 「次へ」をクリック
6. 確認画面で「許可を追加」をクリック

#### 方法B: 最小権限のカスタムポリシーを作成（推奨・セキュア）

1. 「許可を追加」→「ポリシーを作成」を選択
2. JSONタブを選択
3. 以下のJSONを貼り付け：

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
                "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-opus-20240229-v1:0"
            ]
        }
    ]
}
```

4. 「次へ」をクリック
5. ポリシー名を入力（例：`BedrockRAGAccess`）
6. 「ポリシーを作成」をクリック
7. 作成したポリシーをユーザーにアタッチ（方法Aの手順を参照）

## ステップ4: 権限の確認

### 4.1 権限が正しく付与されているか確認

1. ユーザー詳細ページの「許可」タブを確認
2. 以下のいずれかが表示されていれば成功：
   - `AmazonBedrockFullAccess`
   - または、作成したカスタムポリシー

### 4.2 権限の詳細を確認

1. ポリシー名をクリック
2. 「JSON」タブで権限の詳細を確認
3. 以下のアクションが含まれていることを確認：
   - `bedrock:InvokeModel` - モデルを呼び出す権限
   - `bedrock:ListFoundationModels` - モデル一覧を取得する権限（オプション）

## 利用可能なBedrockポリシー

### AmazonBedrockFullAccess（フルアクセス）

**用途**: すべてのBedrock機能にアクセス可能
**権限**: 
- すべてのBedrockアクション
- すべてのリソースへのアクセス

**使用場面**: 
- 開発・テスト環境
- 管理者ユーザー

### AmazonBedrockReadOnlyAccess（読み取り専用）

**用途**: Bedrockの情報を読み取るのみ（モデル呼び出しは不可）
**権限**: 
- モデル一覧の取得
- モデル情報の閲覧

**使用場面**: 
- 監査・確認用途
- **注意**: モデル呼び出しには不十分

### カスタムポリシー（最小権限）

**用途**: 必要最小限の権限のみを付与
**権限**: 
- 指定したモデルのみ呼び出し可能
- リージョンやモデルを制限可能

**使用場面**: 
- 本番環境
- セキュリティ要件が厳しい環境

## 最小権限のカスタムポリシー例

### 例1: 特定のモデルのみ許可

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            ]
        }
    ]
}
```

### 例2: すべてのClaude 3モデルを許可

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-*"
            ]
        }
    ]
}
```

### 例3: すべてのBedrockモデルを許可（リージョン制限あり）

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
                "arn:aws:bedrock:ap-northeast-1::foundation-model/*"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": "ap-northeast-1"
                }
            }
        }
    ]
}
```

## トラブルシューティング

### 問題1: ポリシーが見つからない

**原因**: ポリシー名の検索が正しく動作していない

**解決方法**:
1. 検索バーに「Bedrock」と入力
2. フィルターで「AWS管理」を選択
3. スクロールして`AmazonBedrockFullAccess`を探す

### 問題2: 権限を追加できない

**原因**: 管理者権限がない

**解決方法**:
1. 管理者アカウントでログイン
2. または、IAMユーザー管理権限を持つユーザーでログイン

### 問題3: 権限を追加したが動作しない

**原因**: 
- 権限の反映に時間がかかる（通常は即座）
- ポリシーが正しくアタッチされていない

**解決方法**:
1. ブラウザをリフレッシュ
2. ユーザーの「許可」タブでポリシーが表示されているか確認
3. 数分待ってから再度試す

### 問題4: 特定のモデルにアクセスできない

**原因**: カスタムポリシーでモデルARNが間違っている

**解決方法**:
1. モデルARNを確認：
   ```
   arn:aws:bedrock:{リージョン}::foundation-model/{モデルID}
   ```
2. 例：`arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0`
3. ポリシーのResourceセクションに正しいARNを記入

## 権限の確認方法

### 方法1: AWSコンソールで確認

1. IAM → ユーザー → 該当ユーザー
2. 「許可」タブを確認
3. ポリシー名をクリックして詳細を確認

### 方法2: AWS CLIで確認

```bash
aws iam list-attached-user-policies --user-name your-username
aws iam list-user-policies --user-name your-username
```

### 方法3: テスト実行で確認

```bash
cd backend
python test_bedrock.py
```

成功すれば権限が正しく設定されています。

## セキュリティのベストプラクティス

1. **最小権限の原則**
   - 必要最小限の権限のみを付与
   - カスタムポリシーを使用して権限を制限

2. **定期的な監査**
   - 不要な権限を削除
   - 使用していないポリシーを確認

3. **アクセスキーのローテーション**
   - 定期的にアクセスキーを更新
   - 古いキーは無効化

4. **MFA（多要素認証）の有効化**
   - セキュリティを強化
   - 特に本番環境では必須

## 参考リンク

- [IAM ユーザーの管理](https://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/id_users.html)
- [IAM ポリシーの作成](https://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/access_policies_create.html)
- [Bedrock の IAM アクセス制御](https://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html)

