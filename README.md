# connpassイベント検索エージェント

自然言語で技術イベント・勉強会を検索できるWebアプリ

## セットアップ

```bash
# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envにOPENAI_API_KEYを設定
```

## 起動

```bash
streamlit run app.py
```

## 使い方

- 「来週東京でPythonの勉強会ある？」
- 「今月のAWS関連イベント教えて」
- 「オンラインで参加できるReactの勉強会」
