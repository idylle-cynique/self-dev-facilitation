import os
import subprocess
import yaml

config_path = os.path.join(os.path.dirname(__file__), 'pr_variables.yml')
with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

variables = config['pull_request']['variables']
filename_template = config['pull_request']['filename']
title_template = config['pull_request']['title']
body_template = config['pull_request']['body']

def run_command(command):
    """シェルコマンドを実行し、その出力を返す。"""
    result = subprocess.run(command, shell=True, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"コマンドが失敗しました: {command}\n{result.stderr}")
    return result.stdout.strip()

def generate_pr():
    """YAML設定に基づいてプルリクエストファイルを生成する。"""
    context = {}

    # 変数を取得するためにコマンドを実行
    for variable in variables:
        name = variable['name']
        command = variable['command']
        context[name] = run_command(command)

    # ファイル名、タイトル、本文をレンダリング
    filename = filename_template
    for key, value in context.items():
        filename = filename.replace(f"{{{{ {key} }}}}", value)

    title = title_template
    for key, value in context.items():
        title = title.replace(f"{{{{ {key} }}}}", value)

    body = body_template
    for key, value in context.items():
        body = body.replace(f"{{{{ {key} }}}}", value)

    # PRファイルを書き込む
    with open(filename, 'w', encoding='utf-8') as pr_file:
        pr_file.write(f"{body}")

    print(f"プルリクエストファイルが作成されました: {filename}")

if __name__ == "__main__":
    generate_pr()
