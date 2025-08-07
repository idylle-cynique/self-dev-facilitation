import os
import re
import subprocess
import yaml

from dotenv import load_dotenv

def load_yaml_config(file_path):
    """YAMLファイルを読み込み、内容を返す。エラー時はNoneを返す。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: YAML file not found at {file_path}")
        print("Ensure the YAML file exists at the specified path.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None

def render_template_simple(template_str, variables):
    """
    単純なプレースホルダー置換関数。
    {{ placeholder }} を variables の値で置き換える。
    見つからないプレースホルダーはそのまま残す。
    """
    def replace_match(match):
        key = match.group(1).strip() # {{ key }} の key 部分を取得
        return str(variables.get(key, match.group(0))) # 見つからなければ元の {{ placeholder }} を返す

    return re.sub(r'{{\s*([\w_]+)\s*}}', replace_match, template_str)

def resolve_variables_from_commands(variables_data):
    """コマンドを実行して変数を解決し、辞書として返す。"""
    resolved_vars = {}
    for var_item in variables_data:
        var_name = var_item.get('name')
        command_str = var_item.get('command')
        if var_name and command_str:
            print(f"Executing command for '{var_name}': {command_str.strip()}")
            try:
                current_env = os.environ.copy()
                process = subprocess.run(command_str, capture_output=True, text=True, shell=True,
                                                      check=True, env=current_env)
                resolved_vars[var_name] = process.stdout.strip()
                print(f"  -> Result for '{var_name}': {resolved_vars[var_name]}")
            except subprocess.CalledProcessError as e:
                print(f"  Error executing command for {var_name}: {e}")
                print(f"  Stderr: {e.stderr.strip()}")
                resolved_vars[var_name] = f"ERROR_EXECUTING_COMMAND: {e.stderr.strip()}"
            except FileNotFoundError as e:
                print("  Error: A command was not found (e.g., gh, jq). Ensure they are installed and in PATH.")
                print(f"  Details: {e}")
                resolved_vars[var_name] = "ERROR_COMMAND_NOT_FOUND"
        else:
            print(f"Skipping variable item due to missing name or command: {var_item}")

    print("Resolved variables: \n")
    for k, v in resolved_vars.items():
        print(f"  {k}: {v}")
    return resolved_vars

def load_and_validate_config():
    """YAMLファイルを読み込み、設定を検証する。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_file_path = os.path.join(script_dir, 'issue_variables.yml')

    data = load_yaml_config(yaml_file_path)
    if data is None:
        return None, None, None, None

    issue_data = data.get('issue', {})
    variables_data = issue_data.get('variables', [])
    prompts_data = issue_data.get('prompts', [])

    gh_repo_env = os.environ.get('GH_REPO')
    if not gh_repo_env:
        print("Error: GH_REPO environment variable is not set.")
        print("Please set it before running the script, e.g., export GH_REPO='owner/repo'")
        return None, None, None, None

    print(f"Using GH_REPO: {gh_repo_env}")
    return issue_data, variables_data, prompts_data, script_dir

def extract_templates(issue_data):
    """テンプレート設定を抽出する。"""
    return {
        'filename': issue_data.get('filename', 'issue_{{next_issue_number}}.md'),
        'title': issue_data.get('title', '{{ issue_title_text }}'),
        'body': issue_data.get('body', '{{ body }}'),
        'assignees': issue_data.get('assignees', '{{ assignees }}'),
        'labels': issue_data.get('labels', '{{ labels }}')
    }

def render_all_templates(templates, resolved_variables):
    """すべてのテンプレートをレンダリングする。"""
    print("\\nRendering templates...")
    rendered = {}

    # 変数を先にすべて解決してからテンプレートに適用
    all_render_vars = resolved_variables.copy()

    rendered['filename'] = render_template_simple(templates['filename'], all_render_vars)
    print(f"  Rendered filename: {rendered['filename']}")

    rendered['title'] = render_template_simple(templates['title'], all_render_vars)
    rendered['body'] = render_template_simple(templates['body'], all_render_vars)
    rendered['assignees'] = render_template_simple(templates['assignees'], all_render_vars)
    rendered['labels'] = render_template_simple(templates['labels'], all_render_vars)

    return rendered, all_render_vars

def determine_output_directory(issue_data, script_dir):
    """出力ディレクトリを決定し、作成する。"""
    project_root = os.path.dirname(script_dir)
    output_dir_name = "outputs"  # デフォルト

    reference_path = issue_data.get('reference')
    if reference_path:
        ref_dir = os.path.dirname(reference_path)
        if ref_dir and ref_dir != ".":
            output_dir_name = ref_dir.lstrip('./')

    output_path_dir = os.path.join(project_root, output_dir_name)

    try:
        os.makedirs(output_path_dir, exist_ok=True)
        print(f"Ensured output directory exists: {output_path_dir}")
    except OSError as e:
        print(f"Error creating output directory {output_path_dir}: {e}")
        print(f"Attempting to write to current directory '{os.getcwd()}' instead.")
        output_path_dir = os.getcwd()

    return output_path_dir

def generate_file_content(rendered_templates):
    """テンプレートベースでファイルコンテンツを生成する。"""
    # ファイルコンテンツのテンプレート
    content_template = """
        ---
        title: "{title}"
        assignees: {assignees}
        labels: {labels}
        ---
        {body}
        """

    # タイトル内のバックスラッシュと二重引用符を適切にエスケープ
    escaped_title = rendered_templates['title'].replace('\\\\', '\\\\\\\\').replace('"', '\\\\"')

    # テンプレート変数を準備
    template_vars = {
        'title': escaped_title,
        'assignees': rendered_templates['assignees'],
        'labels': rendered_templates['labels'], 
        'body': rendered_templates['body']
    }

    return content_template.format(**template_vars)

def print_next_steps(prompts_data, all_render_vars):
    """生成後の次のステップを表示する。"""
    # プロンプトの例を表示
    if prompts_data:
        print("\\n   For example, prompts defined in issue_variables.yml are:")
        for p_item in prompts_data:
            p_name = p_item.get('name')
            p_prompt_template = p_item.get('prompt')
            # プロンプト内の変数を解決して表示
            p_prompt_rendered = render_template_simple(p_prompt_template, all_render_vars)
            print(f"   - For '{p_name}': {p_prompt_rendered}")

def main():
    """YAMLファイルを読み込み、変数を解決し、テンプレートをレンダリングして出力ファイルを生成する。"""
    # 設定の読み込みと検証
    issue_data, variables_data, prompts_data, script_dir = load_and_validate_config()
    if issue_data is None:
        return

    resolved_variables = resolve_variables_from_commands(variables_data)

    # テンプレートの抽出とレンダリング
    templates = extract_templates(issue_data)
    rendered_templates, all_render_vars = render_all_templates(templates, resolved_variables)

    # 出力ディレクトリの決定
    output_path_dir = determine_output_directory(issue_data, script_dir)
    output_file_path = os.path.join(output_path_dir, rendered_templates['filename'])

    # ファイルコンテンツの生成
    output_content = generate_file_content(rendered_templates)

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print_next_steps(prompts_data, all_render_vars)
    except IOError as e:
        print(f"Error writing to file {output_file_path}: {e}")

def setup_environment():
    """環境変数を設定する。"""
    main_script_dir = os.path.dirname(os.path.abspath(__file__))

    dotenv_path = os.path.join(os.path.dirname(main_script_dir), '.env')
    load_dotenv(dotenv_path=dotenv_path)

if __name__ == '__main__':
    setup_environment()
    main()
