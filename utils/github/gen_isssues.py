import os
import yaml

# --- 設定 ---
# issue_variables.yml と issue_template.md のパスをスクリプトの場所からの相対パスで指定
script_dir = os.path.dirname(os.path.abspath(__file__))
VARIABLES_FILE_PATH = os.path.join(script_dir, "templates", "issue_variables.yml")
TEMPLATE_FILE_PATH = os.path.join(script_dir, "templates", "issue_template.md")
OUTPUT_DIR = os.path.join(os.path.dirname(script_dir), "outputs")
# --- 設定ここまで ---

def load_yaml_file(file_path):
    """YAMLファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"エラー: YAMLファイルの解析に失敗しました - {file_path}\n{e}")
        return None

def load_markdown_file(file_path):
    """Markdownファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {file_path}")
        return None

# pylint: disable=inconsistent-return-statements
# pylint: disable=useless-return
def generate_copilot_prompt(issue_vars_content, issue_template_content):
    """
        未実装のため一時的に無効化
        GitHub Copilot CLIに渡すプロンプトを生成する
    """
    if not issue_vars_content or not issue_template_content:
        return None
