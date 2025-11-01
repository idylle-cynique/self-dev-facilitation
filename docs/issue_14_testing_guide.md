# Issue #14: Force-Push検出機能のテストガイド

## 概要

Issue #14で実装したforce-push検出機能（コミット履歴改変の検知）の手動テスト手順を記載します。

## 実装内容

pre-pushフックに以下の機能を追加しました：

- `remote_oid`が`0000...`でない場合（既存のブランチへのpush）
- `git merge-base --is-ancestor <remote_oid> <local_oid>`がfalseを返す場合
- → 履歴が改変されている（force-push）と判定し、警告メッセージを表示
- `force_push_detected`フラグを`true`に設定（将来的な拡張で使用）

**注意**: この実装はforce-pushを検出するのみで、pushをブロックしません。実際のブロック処理はIssue #13で実装される「子ブランチが存在する場合のforce-push抑止」機能で行われます。

実装場所:
- 関数定義: [utils/git/hooks/pre-push:69-88](../utils/git/hooks/pre-push#L69-L88) (`is_force_push()`)
- 関数呼び出し: [utils/git/hooks/pre-push:110-116](../utils/git/hooks/pre-push#L110-L116)

## 実装の設計

- `is_force_push()`: Force-pushの検出のみを担当（boolean値を返す）
  - 戻り値: `0` (true) = force-push検出、`1` (false) = 通常のpush
  - エラーメッセージの出力は行わない（単一責任の原則）
- メインループ: 検出結果に基づいて警告メッセージを表示し、`force_push_detected`フラグを設定
  - 現時点ではpushをブロックしない（検出のみ）
  - Issue #13の実装で、このフラグと子ブランチの存在チェックを組み合わせてブロック判定を行う予定

## 手動テスト手順

### 前提条件

- Gitフックがインストールされている
- テスト用のブランチを作成できる

### テストケース1: 通常のpush（成功するべき）

```bash
# 1. テスト用ブランチを作成
git checkout -b test-force-push-14
git commit --allow-empty -m "test: force-push detection initial commit"
git push origin test-force-push-14

# 2. 新しいコミットを追加してpush
git commit --allow-empty -m "test: force-push detection second commit"
git push origin test-force-push-14

# Expected: pushが成功し、force-push警告は表示されない
```

### テストケース2: Force-push（警告が表示されるがpushは成功）

```bash
# 1. コミット履歴を改変（amend）
git commit --amend -m "test: force-push detection amended commit"

# 2. 通常のpushを試みる
git push origin test-force-push-14

# Expected: 以下のような警告メッセージが表示されるが、pushは成功する
# Warning: Force-push detected (commit history will be modified)
# Remote commit XXXX is not an ancestor of local commit YYYY
#
# 注意: Issue #13実装後は、子ブランチが存在する場合にのみpushがブロックされるようになります
```

### テストケース3: 新規ブランチのpush（成功するべき）

```bash
# 1. 新しいブランチを作成
git checkout -b test-force-push-14-new
git commit --allow-empty -m "test: new branch push"

# 2. 新規ブランチとしてpush
git push origin test-force-push-14-new

# Expected: pushが成功する（remote_oidが0000...なので検査をスキップ）
```

### テストケース4: Rebaseによる履歴改変（警告が表示されるがpushは成功）

```bash
# 1. 別のブランチから分岐
git checkout main
git checkout -b test-force-push-14-rebase
git commit --allow-empty -m "test: rebase test commit 1"
git commit --allow-empty -m "test: rebase test commit 2"
git push origin test-force-push-14-rebase

# 2. mainブランチを更新（ダミー）
git checkout main
git pull origin main

# 3. rebaseして履歴を書き換え
git checkout test-force-push-14-rebase
git rebase main

# 4. 通常のpushを試みる
git push origin test-force-push-14-rebase

# Expected: 警告メッセージが表示されるが、pushは成功する
```

### クリーンアップ

```bash
# テスト用ブランチを削除
git push origin --delete test-force-push-14 test-force-push-14-new test-force-push-14-rebase
git checkout main
git branch -D test-force-push-14 test-force-push-14-new test-force-push-14-rebase
```

## 期待される動作

### 警告なしでpushが成功するパターン

- 新規ブランチへのpush
- 既存ブランチへの通常のコミット追加（履歴を変更しない）

### 警告が表示されるがpushは成功するパターン

- `git commit --amend`による履歴改変
- `git rebase`による履歴改変
- `git reset --hard`後の古いコミットへの戻し

### 警告メッセージ

Force-pushが検出された場合、以下の警告が表示されます：

```
Warning: Force-push detected (commit history will be modified)
Remote commit <remote_oid> is not an ancestor of local commit <local_oid>
```

**重要**: 現時点ではこの警告が表示されてもpushは継続されます。Issue #13の実装により、子ブランチが存在する場合にのみpushがブロックされるようになります。

## 注意事項

- このフックは`git push`コマンドでのみ動作します
- `git push --force`や`git push --force-with-lease`を使用した場合でも、force-push検出は機能します
- フックをバイパスしたい場合は、`git push --no-verify`を使用できますが、推奨されません

## 既存機能との統合

この機能は既存のpre-pushフック機能と統合されており、以下の順序でチェックが行われます：

1. Force-push検出（Issue #14） - **警告のみ、ブロックしない**
2. Mainブランチへの直接pushの禁止 - ブロック
3. PR存在時のassignee/reviewerチェック（Issue #10） - ブロック

## 今後の拡張

Issue #13の実装により、以下のロジックが追加される予定です：

```
if force_push_detected && 子ブランチが存在する:
    pushをブロック
```

これにより、force-pushが検出され、かつそのブランチをベースとする子ブランチが存在する場合にのみ、pushがブロックされるようになります。
