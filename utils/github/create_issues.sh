#!/bin/bash

# .envファイルを読み込み
ENV_FILE="$( pwd )/.env"

if [ -f "$ENV_FILE" ]; then
  source "$ENV_FILE"
  REPO="$GH_REPO"
else
  echo "エラー: .envファイルが見つかりません。($ENV_FILE)"
  exit 1
fi

# YAMLファイルのパス
YAML_FILE="$( pwd )/issues.yml"

# 実行前に確認
echo "以下のIssueを作成します:"
echo "------------------------"

# YAMLファイルから各issueを取得して表示
ISSUES_COUNT=$(yq '.issues | length' "$YAML_FILE")
for ((i=0; i<$ISSUES_COUNT; i++)); do
  title=$(yq ".issues[$i].title" "$YAML_FILE")
  body=$(yq ".issues[$i].body" "$YAML_FILE")
  tag=$(yq ".issues[$i].tag // \"なし\"" "$YAML_FILE")

  echo "タイトル: $title"
  echo "本文:"
  # ここで改行を保持して表示するように変更
  echo -e "$body"
  echo "タグ: $tag"
  echo "------------------------"
done

# ユーザーに確認
read -p "これらのIssueをGitHubに作成しますか？ (y/n): " confirm
if [[ $confirm != [yY] ]]; then
  echo "キャンセルしました。"
  exit 0
fi

echo "Issueを作成しています..."

# 各issueをGitHubに作成
for ((i=0; i<$ISSUES_COUNT; i++)); do
  title=$(yq ".issues[$i].title" "$YAML_FILE")
  body=$(yq ".issues[$i].body" "$YAML_FILE")
  tag=$(yq ".issues[$i].tag // \"\"" "$YAML_FILE")

  # タグがある場合はラベルオプションを追加
  if [ -n "$tag" ] && [ "$tag" != "null" ]; then
    echo "「$title」を作成中..."
    gh issue create --repo "$REPO" --title "$title" --body "$body" --label "$tag"
  else
    echo "「$title」を作成中..."
    gh issue create --repo "$REPO" --title "$title" --body "$body"
  fi

  sleep 1
done

echo "全てのIssueが正常に作成されました。"
