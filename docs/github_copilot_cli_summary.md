# GitHub Copilot CLI の使い方まとめ

## シェルからの直接操作について

現時点では、シェルから直接 GitHub Copilot に命令を送信する標準的な機能は提供されていません。

## GitHub Copilot CLI の利用

GitHub Copilot CLI を使用することで、ターミナル経由で GitHub Copilot の機能を利用できます。

### 主なコマンド

*   **コードの提案**:
    ```bash
    gh copilot suggest "やりたいことの説明"
    ```
    例: `gh copilot suggest "Pythonでカレントディレクトリのファイルを一覧表示する"`

*   **コードの説明**:
    ```bash
    gh copilot explain <ファイルパス>
    ```

*   **ターミナルコマンドの提案**:
    ```bash
    gh copilot suggest "gitで最後のコミットを取り消す" --type command
    ```

*   **エイリアスの設定**:
    `gh copilot alias` コマンドで短いエイリアスを設定できます。
    詳細は `gh copilot alias --help` で確認してください。

*   **ヘルプ**:
    ```bash
    gh copilot --help
    gh copilot <サブコマンド> --help
    ```

### プロンプトの渡し方

*   **コマンドラインで直接入力**:
    ```bash
    gh copilot suggest "ここにプロンプトを入力"
    ```

*   **ファイルからリダイレクト**:
    ファイルの内容をプロンプトとして渡します。ファイル形式は `.txt` に限りません (`.yml`, `.md` なども可)。
    ```bash
    gh copilot suggest < prompt.txt
    ```

*   **コマンド置換を利用**:
    ```bash
    gh copilot suggest "$(cat prompt.md)"
    ```

### 応答について

CLI でコマンドを入力した場合、その応答（提案されたコード、説明、エラーメッセージなど）は実行したターミナルにテキストとして返されます。

### 機能の切り替え (ask, edit, agent など)

GitHub Copilot CLI では、実行したい操作に応じてサブコマンドを使い分けます。

*   **質問 (ask)**:
    ```bash
    gh copilot ask "質問内容"
    ```
*   **編集 (edit)**:
    ```bash
    gh copilot edit <ファイルパス> --instructions "編集指示"
    ```
    (注: `--instructions` は仮のオプション名です。正確なオプションはヘルプで確認してください。)
*   **高度なタスク (agent)**:
    ```bash
    gh copilot agent "タスク内容"
    ```
    (注: `agent` サブコマンドの有無や詳細はバージョンにより異なる可能性があります。)

各サブコマンドの正確な使い方やオプションは、`gh copilot <サブコマンド> --help` や公式ドキュメントで確認してください。
