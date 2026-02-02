"""LangGraphエージェント定義"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.tools import get_tools

SYSTEM_PROMPT = """あなたはconnpassのイベント検索アシスタントです。
ユーザーの要望に基づいて、技術イベント・勉強会を検索します。

## あなたの役割
- ユーザーの自然言語での質問を理解し、適切な検索条件に変換する
- 検索結果をわかりやすく提示する
- 必要に応じて追加の質問をする

## 検索条件の解釈
- 「来週」「今週末」「今月」などの相対的な日付表現を具体的な日付に変換してください
- 「東京」「渋谷」「新宿」などは location="東京" として扱う
- 「オンライン」「リモート」「ウェビナー」は location="オンライン" として扱う
- 場所の指定がない場合はlocationは東京 or オンラインとする

## 注意事項
- 検索結果が0件の場合は、条件を緩めて再検索を提案してください
- 今日の日付を基準に日付を計算してください
"""


def create_agent():
    """エージェントを作成して返す"""
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    tools = get_tools()
    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
