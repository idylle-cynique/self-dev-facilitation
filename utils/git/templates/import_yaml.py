import json
import os
import subprocess
import yaml


# スクリプトの場所から動的にパスを取得
script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(script_dir))
SETTINGS_FILE_PATH = os.path.join(PROJECT_ROOT, "settings.json")
ISSUE_VARIABLES_FILE_PATH = os.path.join(script_dir, "issue_variables.yml")

def execute_command(command_str, env=None):
    """指定されたコマンドを実行し、標準出力を返す
    
    Args:
        command_str (str): 実行するシェルコマンド
        env (dict, optional): 環境変数の辞書。Noneの場合は現在の環境変数を使用
        
    Returns:
        str: コマンドの標準出力。エラーの場合はエラーメッセージ
    """
    try:
        process = subprocess.run(
            command_str,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        result = process.stdout.strip()
        print(f"結果: {result}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"実行エラー: {e}")
        print(f"エラー出力: {e.stderr.strip()}")
        return f"エラー: {e.stderr.strip()}"
    except FileNotFoundError:
        print("エラー: コマンドが見つかりません。gh CLIやjqがインストールされているか確認してください。")
        return "エラー: コマンド未検出"

def load_settings_json(file_path):
    """settings.jsonファイルを読み込む
    
    Args:
        file_path (str): settings.jsonファイルのパス
        
    Returns:
        tuple: (gh_repo, default_assignee_from_settings) のタプル
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        settings_data = json.load(f)
    gh_repo = settings_data.get("repository")
    default_assignee_from_settings = settings_data.get("default-assignee")
    if not gh_repo:
        raise ValueError(f"{file_path} に 'repository' が設定されていません。")
    print(f"リポジトリ: {gh_repo}")
    print(f"デフォルト担当者 (settings.json): {default_assignee_from_settings}")
    return gh_repo, default_assignee_from_settings

def load_issue_variables_yml(file_path):
    """issue_variables.ymlファイルを読み込む
    
    Args:
        file_path (str): issue_variables.ymlファイルのパス
        
    Returns:
        dict: issueセクションのデータ
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        issue_config = yaml.safe_load(f)

    if 'issue' not in issue_config:
        raise ValueError(f"{file_path} に 'issue' セクションが見つかりません。")

    return issue_config['issue']

def simple_template_render(template_str, context):
    """簡易的なテンプレートレンダリング
    
    テンプレート文字列内の {{ key }} 形式のプレースホルダーを
    contextの値で置換します。
    
    Args:
        template_str (str): テンプレート文字列
        context (dict): 置換する変数の辞書
        
    Returns:
        str: プレースホルダーが置換された文字列
    """
    rendered_str = template_str
    for key, value in context.items():
        rendered_str = rendered_str.replace(f"{{{{ {key} }}}}", str(value))
    return rendered_str

def display_template_results(issue_data, template_context):
    """テンプレート展開結果のサンプル表示を行う
    
    Args:
        issue_data (dict): issueセクションのデータ
        template_context (dict): テンプレート変数の辞書
    """
    print("\n--- テンプレート展開結果のサンプル ---")

    # formatセクションから各テンプレートを取得（配列形式に対応）
    format_data = issue_data.get('format', [])
    templates = {}

    for item in format_data:
        if isinstance(item, dict):
            for key, value in item.items():
                templates[key] = value

    filename_template = templates.get('filename', '')
    title_template = templates.get('title', '')
    body_template = templates.get('body', '')
    assignees_template = templates.get('assignees', '')
    labels_template = templates.get('labels', '')

    print(f"\nFilename テンプレート: {filename_template}")
    print(f"  展開後 (サンプル): {simple_template_render(filename_template, template_context)}")

    print(f"\nTitle テンプレート: {title_template.strip()}")
    rendered_title = simple_template_render(title_template.strip(), template_context)
    print(f"  展開後 (サンプル): {rendered_title}")

    print(f"\nBody テンプレート:\n{body_template.strip()}")
    print(f"  展開後 (サンプル):\n{simple_template_render(body_template.strip(), template_context)}")

    print(f"\nAssignees テンプレート: {assignees_template.strip()}")
    print(f"  展開後 (サンプル): {simple_template_render(assignees_template.strip(), template_context)}")

    print(f"\nLabels テンプレート: {labels_template.strip()}")
    print(f"  展開後 (サンプル): {simple_template_render(labels_template.strip(), template_context)}")

def display_template_samples(issue_data, template_context, default_assignee_from_settings, env=None):
    """テンプレート展開のサンプル表示を行う
    
    Args:
        issue_data (dict): issueセクションのデータ
        template_context (dict): テンプレート変数の辞書
        default_assignee_from_settings (str): デフォルトの担当者
        env (dict, optional): 環境変数の辞書
    """
    if env is None:
        env = os.environ.copy()

    print("\n--- 変数 (Variables) の処理 ---")
    if 'variables' in issue_data and issue_data['variables']:
        for var_info in issue_data['variables']:
            name = var_info.get('name')
            command = var_info.get('command')
            if name and command:
                print(f"\n変数名: {name}")
                value = execute_command(command, env=env)
                template_context[name] = value
            elif name and 'prompt' in var_info:
                print(f"\n変数名 (プロンプト): {name}")
                print(f"  プロンプトメッセージ: {var_info['prompt'].strip()}")
                template_context[name] = f"<{name} のダミー入力>"

    print("\n--- プロンプト (Prompts) の表示 ---")
    if 'prompts' in issue_data and issue_data['prompts']:
        for prompt_info in issue_data['prompts']:
            name = prompt_info.get('name')
            prompt_text_template = prompt_info.get('prompt', '')
            if name:
                prompt_text = simple_template_render(prompt_text_template.strip(), template_context)
                print(f"\nプロンプト名: {name}")
                print(f"  表示されるプロンプト: {prompt_text}")
                if name not in template_context:
                    template_context[name] = f"<{name} のダミー入力>"

    # ダミーデータの補完
    fill_dummy_data(template_context, default_assignee_from_settings)

def fill_dummy_data(template_context, default_assignee_from_settings):
    """テンプレートコンテキストにダミーデータを補完する。"""
    if 'issue_title_text' not in template_context:
        template_context['issue_title_text'] = "<Issueタイトル本文のダミー入力>"
    if 'body' not in template_context:
        template_context['body'] = "<Issue本文のダミー入力>"
    if 'labels' not in template_context:
        template_context['labels'] = "<labelsのダミー入力>"
    if 'assignees' not in template_context:
        template_context['assignees'] = default_assignee_from_settings or "<assigneesのダミー入力>"

def main():
    """メイン関数
    
    settings.jsonとissue_variables.ymlを読み込み、
    変数の解決とプロンプトの表示、テンプレート展開の
    サンプルを実行します。
    """
    # 1. settings.json から情報を読み込む
    gh_repo, default_assignee_from_settings = load_settings_json(SETTINGS_FILE_PATH)

    # 環境変数を設定 (ghコマンド用)
    current_env = os.environ.copy()
    current_env["GH_REPO"] = gh_repo

    # 2. issue_variables.yml を読み込む
    issue_data = load_issue_variables_yml(ISSUE_VARIABLES_FILE_PATH)
    template_context = {}

    # テンプレート展開のサンプル表示
    display_template_samples(issue_data, template_context, default_assignee_from_settings, current_env)

    # テンプレート展開結果の表示
    display_template_results(issue_data, template_context)

if __name__ == "__main__":
    main()
