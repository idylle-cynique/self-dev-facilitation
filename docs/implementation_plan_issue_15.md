# Issue #15 実装計画: pre-push時に子ブランチの存在を検出する

## 概要

force-push検知後、現在のブランチをbaseとする子ブランチ(PR)が存在するかを確認し、存在する場合は警告を表示する機能を実装する。

## 背景

- 親Issue: [#13](https://github.com/idylle-cynique/self-dev-facilitation/issues/13)
- 前提条件: [#14](https://github.com/idylle-cynique/self-dev-facilitation/issues/14) でforce-push検知機能が実装済み

## 目的

スタック式ブランチ運用において、親ブランチへのforce-pushが子ブランチに影響を与える可能性がある場合に、**force-pushを明確に抑止**し、意図しない影響を防ぐ。

### 重要な設計方針

1. **子ブランチが存在する場合**: force-pushを**明確に抑止**（exit 1でpushを中断）
2. **gh/jqコマンドが利用不可の場合**: 子ブランチの存在確認ができないため、force-push自体を**拒否**（安全側に倒す設計）

## 実装仕様

### 処理フロー

1. **force-push検知** (issue #14で実装済み)
2. **オープンPRの取得**
   - `gh pr list` コマンドで全てのオープンPRを取得
3. **子ブランチの判定**
   - 各PRの `baseRefName` を確認
   - 現在pushしようとしているブランチと一致するものを探す
4. **結果の判定と処理**
   - 該当するPRが存在する場合、子ブランチが存在すると判定
   - エラーメッセージを表示し、**pushを中断（exit 1）**

### 実装対象ファイル

- **`.git/hooks/pre-push`** (既存ファイル修正)
  - 既存のBashスクリプトに機能を追加
  - 現在107-115行目にforce-push検知機能が実装済み
  - この検知処理の後に子ブランチチェックを追加

### 実装方法

#### 1. 子ブランチチェック関数の追加

既存の `get_pr_info()` 関数と同様に、新しい関数を追加：

```bash
# Function to get child branches (PRs that use current branch as base)
get_child_branches() {
    local branch_name="$1"

    # Check if gh CLI is available
    if ! command -v gh >/dev/null 2>&1; then
        echo "ERROR:gh_not_found" >&2
        return 2
    fi

    # Check if jq is available
    if ! command -v jq >/dev/null 2>&1; then
        echo "ERROR:jq_not_found" >&2
        return 2
    fi

    # Get all open PRs with base branch matching current branch
    local child_prs=$(gh pr list --state open --json number,headRefName,baseRefName --repo "$REPO_OWNER/$REPO_NAME" 2>/dev/null | \
        jq -r --arg base "$branch_name" '.[] | select(.baseRefName == $base) | "\(.number):\(.headRefName)"')

    if [ -z "$child_prs" ]; then
        return 1  # No child branches found
    fi

    echo "$child_prs"
    return 0  # Child branches found
}
```

**戻り値の意味:**
- `0`: 子ブランチが存在する（`$child_prs` に結果を出力）
- `1`: 子ブランチが存在しない
- `2`: gh/jqコマンドが利用不可（エラー）

#### 2. メインロジックへの統合

force-push検知後（115行目付近）に以下を追加：

```bash
# If force-push detected, check for child branches
if [ "$force_push_detected" = true ]; then
    echo "Force-push detected. Checking for child branches..." >&2

    child_branches=$(get_child_branches "$branch_name")
    check_result=$?

    # Case 1: Child branches found (return code 0)
    if [ $check_result -eq 0 ]; then
        echo -e "${RED}Error: Cannot force-push - child branches detected!${NC}" >&2
        echo -e "${RED}The following PRs are based on '$branch_name':${NC}" >&2
        echo "$child_branches" | while IFS=: read -r pr_num branch; do
            echo -e "${RED}  - PR #$pr_num: $branch${NC}" >&2
        done
        echo -e "${RED}Force-pushing would break these child branches.${NC}" >&2
        echo -e "${YELLOW}Please rebase child branches first, or use regular push.${NC}" >&2
        exit 1
    # Case 2: Command not available (return code 2)
    elif [ $check_result -eq 2 ]; then
        echo -e "${RED}Error: Cannot verify child branches - required commands not available${NC}" >&2
        echo -e "${RED}Force-push is blocked for safety reasons.${NC}" >&2
        echo -e "${YELLOW}Please install 'gh' (GitHub CLI) and 'jq' to enable force-push with child branch detection.${NC}" >&2
        echo -e "${YELLOW}Or contact your team lead if you need to force-push urgently.${NC}" >&2
        exit 1
    # Case 3: No child branches (return code 1)
    else
        echo "No child branches detected. Force-push allowed." >&2
    fi
fi
```

**処理の流れ:**
1. force-push検知時に `get_child_branches()` を呼び出し
2. 戻り値で3つのケースに分岐：
   - `0`: 子ブランチ存在 → **force-push抑止**
   - `2`: gh/jq利用不可 → **force-push抑止**（安全側）
   - `1`: 子ブランチなし → force-push許可

### GitHub CLI コマンド仕様

```bash
gh pr list --state open --json number,headRefName,baseRefName --repo "$REPO_OWNER/$REPO_NAME"
```

**レスポンス例:**
```json
[
  {
    "number": 123,
    "headRefName": "feature/child-branch",
    "baseRefName": "feature/parent-branch"
  }
]
```

### データ処理

`jq` を使用してJSON処理：
- baseRefNameが現在のブランチと一致するPRをフィルタ
- PR番号とヘッドブランチ名を `数値:ブランチ名` 形式で出力
- Bashで読み取りやすい形式に変換

### エラーハンドリング

**安全側に倒す設計（Fail-safe）:**
- **`gh` コマンドが利用不可の場合**: return 2 → **force-pushを抑止**
- **`jq` コマンドが利用不可の場合**: return 2 → **force-pushを抑止**
- **子ブランチが検知された場合**: return 0 → **force-pushを抑止** (exit 1でpush中断)
- **子ブランチが存在しない場合**: return 1 → force-pushを許可
- **APIエラーの場合**: 標準エラー出力は `/dev/null` にリダイレクトされ、`child_prs` が空になる → return 1 → force-push許可

**設計理念:**
子ブランチの存在確認ができない状態（gh/jqが利用不可）では、安全のためforce-pushを拒否する。これにより、意図しない子ブランチへの影響を確実に防ぐ。

## 実装ステップ

1. **`get_child_branches()` 関数の追加**
   - pre-pushスクリプトの関数定義セクション（20-85行目付近）に追加
   - 既存の `get_pr_info()` 関数の後に配置
   - `gh pr list` + `jq` でPRをフィルタリング

2. **force-push検知後のチェック処理追加**
   - メインループ内の115行目付近（force-push検知直後）に追加
   - 子ブランチが存在する場合にエラーメッセージを表示
   - **exit 1 でpushを中断**

3. **動作確認**
   - 実際のリポジトリで子ブランチを持つPRを作成してテスト
   - force-push時にエラーが表示され、pushが中断されることを確認
   - 子ブランチが存在しない場合はforce-pushが許可されることを確認

4. **ドキュメントの更新**
   - README.mdに機能説明を追加

## エラーメッセージ出力例

### ケース1: 子ブランチが存在する場合

```
Force-push detected. Checking for child branches...
Error: Cannot force-push - child branches detected!
The following PRs are based on 'feature/parent-branch':
  - PR #123: feature/child-branch
  - PR #456: feature/another-child
Force-pushing would break these child branches.
Please rebase child branches first, or use regular push.
```

※赤色（`${RED}`）と黄色（`${YELLOW}`）で表示されます

### ケース2: gh/jqコマンドが利用不可の場合

```
Force-push detected. Checking for child branches...
Error: Cannot verify child branches - required commands not available
Force-push is blocked for safety reasons.
Please install 'gh' (GitHub CLI) and 'jq' to enable force-push with child branch detection.
Or contact your team lead if you need to force-push urgently.
```

※赤色（`${RED}`）と黄色（`${YELLOW}`）で表示されます

## テストシナリオ

### 正常系
1. **force-pushかつ子ブランチが存在する場合**
   - force-push検知メッセージが表示されること
   - 子ブランチ一覧がPR番号付きで表示されること
   - **pushが中断されること（exit 1）**

2. **force-pushだが子ブランチが存在しない場合**
   - force-push検知メッセージが表示されること
   - "No child branches detected. Force-push allowed." と表示されること
   - pushが継続されること

3. **通常のpush（force-pushでない）の場合**
   - 子ブランチチェックが実行されないこと
   - pushが継続されること

### 異常系（安全側に倒す設計）
1. **GitHub CLIが利用不可の場合**
   - "Cannot verify child branches - required commands not available" と表示されること
   - **force-pushが拒否されること（exit 1）**
   - gh/jqのインストールを促すメッセージが表示されること

2. **jqコマンドが利用不可の場合**
   - "Cannot verify child branches - required commands not available" と表示されること
   - **force-pushが拒否されること（exit 1）**
   - gh/jqのインストールを促すメッセージが表示されること

3. **API呼び出しエラーの場合**
   - エラーメッセージは `/dev/null` にリダイレクトされる
   - `child_prs` が空になり、return 1（子ブランチなし）と判定される
   - **pushが継続される**こと

## 関連Issue・PR

- 親Issue: [#13](https://github.com/idylle-cynique/self-dev-facilitation/issues/13)
- 前提Issue: [#14](https://github.com/idylle-cynique/self-dev-facilitation/issues/14)

## 実装上の注意点

1. **パフォーマンス**
   - PR数が多い場合も考慮（ただし、通常は数十件程度と想定）
   - API呼び出しは1回のみ（gh pr list）
   - jqでのフィルタリングは高速

2. **既存機能との整合性**
   - force-pushチェック（issue #14）との統合
   - 既存のpre-pushフローを壊さないこと
   - 既存の関数定義パターン（`get_pr_info` など）に合わせた実装

3. **ユーザビリティ**
   - 明確で分かりやすいエラーメッセージ
   - 誤検知を避けるため、正確なブランチ名マッチング（`baseRefName == branch_name`）
   - **子ブランチが存在する場合はforce-pushを中断**（データ整合性を保護）
   - **チェック自体が失敗した場合もforce-pushを拒否**（安全側に倒す設計）

4. **依存関係**
   - `gh` コマンド: 既存のpre-pushフックで使用済み
   - `jq` コマンド: 既存のpre-pushフックで使用済み
   - 新たな依存関係は不要
   - **重要**: これらのコマンドが利用不可の場合、force-pushは拒否される

## コードの配置場所

### 関数定義
- 20-85行目付近の関数定義セクション
- `is_self_reviewer()` 関数（56-63行目）の後に `get_child_branches()` を追加

### メインロジック
- 105-116行目のforce-push検知処理の後
- 115行目 `echo "DEBUG: force_push_detected=$force_push_detected" >&2` の後に追加

## タスク分解とman-hours見積もり

### Todo List

1. **`get_child_branches()` 関数の実装** (1.0h)
   - gh/jqコマンドの存在チェック処理
   - `gh pr list` によるPR一覧取得
   - jqによるフィルタリング処理
   - 3パターンの戻り値の実装（0: 子ブランチあり、1: なし、2: コマンド不可）

2. **メインロジックへの統合** (1.5h)
   - force-push検知後の子ブランチチェック呼び出し
   - 3つの分岐処理の実装
   - エラーメッセージの実装（2パターン）
   - 既存処理との整合性確認

3. **テストケースの作成と実行** (2.5h)
   - 正常系テスト
     - 子ブランチあり → force-push拒否
     - 子ブランチなし → force-push許可
     - 通常のpush → チェックスキップ
   - 異常系テスト
     - ghコマンド利用不可 → force-push拒否
     - jqコマンド利用不可 → force-push拒否
     - API呼び出しエラー → force-push許可
   - 実際のリポジトリでの動作確認

4. **ドキュメント更新** (0.5h)
   - README.mdに機能説明を追加
   - 使用例の記載
   - 依存関係の明記

5. **コードレビューと修正** (0.5h)
   - コード品質の確認
   - エラーハンドリングの改善
   - メッセージの文言確認

**合計見積もり**: 約6.0時間

## 技術的考慮事項

### 依存関係
- `gh` (GitHub CLI): 必須（子ブランチ検出用）
  - 利用不可の場合: force-pushを拒否
- `jq`: 必須（JSON解析用）
  - 利用不可の場合: force-pushを拒否
- `git merge-base`: Git標準コマンド（issue #14で使用）

### パフォーマンス
- `gh pr list`の実行時間: リポジトリのPR数に依存（通常は0.5〜2秒程度）
- 通常のpush操作（force-pushでない場合）には影響なし
- force-push時のみチェックが実行される

### 互換性
- 既存のブランチ制限ロジックとの共存を確認
- issue #14で実装されたforce-push検知機能との統合
- mainブランチへのforce-push試行は既に別ルールで禁止されている

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| gh CLIが利用できない環境 | 高 | force-pushを拒否し、インストールを促すメッセージを表示 |
| jqが利用できない環境 | 高 | force-pushを拒否し、インストールを促すメッセージを表示 |
| API呼び出しの失敗 | 中 | エラーを無視し、子ブランチなしと判定（force-push許可） |
| 大量のPR（50件以上）の扱い | 低 | デフォルトの取得上限で対応、必要に応じて`--limit`を調整 |
| 既存機能への影響 | 低 | force-push検知後に独立した処理として追加、既存ロジックに影響なし |

## 実装後の検証項目

- [ ] 子ブランチが存在する場合、force-pushが正しくブロックされる
- [ ] 子ブランチが存在しない場合、force-pushが許可される
- [ ] 通常のpush（非force-push）は子ブランチチェックが実行されない
- [ ] gh CLIが利用できない場合、force-pushが拒否される
- [ ] jqが利用できない場合、force-pushが拒否される
- [ ] エラーメッセージが明確で、対処方法が示される
- [ ] 既存のブランチ制限機能が正常に動作し続ける
- [ ] PR番号と子ブランチ名が正しく表示される
