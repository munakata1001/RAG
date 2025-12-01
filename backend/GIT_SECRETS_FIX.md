# Git履歴から機密情報を削除する方法

## 問題

GitHubのプッシュ保護機能が、過去のコミット（`c743e4d`）に含まれる`.env`ファイル内のAWS認証情報を検出して、プッシュをブロックしています。

## 解決方法

### 方法1: 過去のコミットから`.env`を削除（推奨）

以下のコマンドで、過去のコミットから`.env`ファイルを削除します：

```bash
# git-filter-repoを使用（推奨）
pip install git-filter-repo
git filter-repo --path backend/.env --invert-paths

# または、git filter-branchを使用（git-filter-repoが使えない場合）
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch backend/.env" --prune-empty --tag-name-filter cat -- --all
```

### 方法2: 新しいブランチを作成（簡単）

1. 新しいブランチを作成：
   ```bash
   git checkout -b main-clean
   ```

2. `.env`を削除してコミット：
   ```bash
   git rm --cached backend/.env
   git commit -m "Remove .env file"
   ```

3. 新しいブランチをプッシュ：
   ```bash
   git push origin main-clean
   ```

4. GitHubで`main-clean`をデフォルトブランチに設定

### 方法3: 強制プッシュ（注意が必要）

⚠️ **警告**: この方法は履歴を書き換えるため、他の開発者がいる場合は注意が必要です。

```bash
# 過去のコミットから.envを削除
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch backend/.env" --prune-empty --tag-name-filter cat -- --all

# 強制プッシュ
git push origin main --force
```

## 今後の対策

1. `.gitignore`に`.env`を追加（既に追加済み）
2. `.env.example`ファイルを作成して、テンプレートとして使用
3. 機密情報は環境変数やAWS Secrets Managerを使用

## 注意事項

- 過去のコミットを修正すると、コミットハッシュが変更されます
- 他の開発者がいる場合は、事前に連絡してください
- 強制プッシュ後は、他の開発者は`git pull --rebase`が必要です

