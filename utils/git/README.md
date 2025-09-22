# Git Utilities

このディレクトリにはGitワークフローを改善するためのユーティリティが含まれています。

## Git Hooks

### Pre-push Hook

`hooks/pre-push`はブランチへのpushを制限するフックです。

#### 制限内容

1. **mainブランチ**: 例外なく直接pushを禁止
2. **その他のブランチ**: 以下3条件をすべて満たす場合にpushを禁止
   - PRが存在している
   - Assigneeが存在しない、もしくは自分以外のID
   - Reviewerに自分がアサインされている

#### インストール方法

```bash
# リポジトリルートで実行
./utils/git/install-hooks.sh
```

#### 必要な依存関係

- **GitHub CLI (gh)**: PR情報の取得に必要
  ```bash
  # macOS
  brew install gh

  # Ubuntu/Debian
  sudo apt install gh

  # 認証
  gh auth login
  ```

#### 動作確認

```bash
# mainブランチへのpush（失敗するはず）
git push origin main

# 他のブランチへのpush
git push origin feature-branch
```

#### トラブルシューティング

- **GitHub CLI未インストール**: 警告が表示されるがmainブランチ制限は動作
- **認証エラー**: `gh auth login`で再認証
- **フック無効化**: `.git/hooks/pre-push`を削除または無実行権限に変更