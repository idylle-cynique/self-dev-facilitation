#!/bin/bash

# 現在のGitブランチ名を取得してIssue番号を抽出
branch_name=$(git rev-parse --abbrev-ref HEAD)
issue_number=$(echo "$branch_name" | awk -F'/' '{print $2}')
issue="${issue_number}"

# 対応するmdファイルのパスを設定
md_file="outputs/pr_${issue}.md"

# mdファイルが存在するか確認
if [ ! -f "$md_file" ]; then
    echo "Markdown file not found: $md_file"
    exit 1
fi

# Copilotにテキストを追加する指示を出す
script_dir=$(dirname "$0")
prompt_file="$script_dir/prompts/complete_pr_md.txt"
if [ ! -f "$prompt_file" ]; then
    echo "Prompt file not found: $prompt_file"
    exit 1
fi

additional_text=$(cat "$prompt_file")

# GitHub Copilot CLIを実行
echo "Executing GitHub Copilot CLI..."
echo "File: $md_file"
echo "Prompt: $additional_text"
echo ""

# Copilotにプロンプトと対象ファイルの情報を渡す
full_prompt="ファイル「$md_file」に対して以下の指示を実行してください: $additional_text"

# GitHub Copilot CLIを実行（非対話モード）
gh copilot suggest "$full_prompt" --no-interactive 2>/dev/null || {
    echo "Copilot suggest failed, trying explain command..."
    gh copilot explain "$full_prompt" --no-interactive 2>/dev/null || {
        echo "Both commands failed. Please run manually:"
        echo "gh copilot suggest \"$full_prompt\""
    }
}
