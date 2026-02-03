"""Streamlit UI"""

import json

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent import create_agent


def render_response(text: str):
    """レスポンスを解析し、画像をst.imageで表示する"""
    if not text:
        return

    # まずJSON形式を試す
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None

    if isinstance(data, dict) and "events" in data:
        total = data.get("total")
        shown = data.get("shown")
        if total is not None and shown is not None:
            st.markdown(f"**{total}件のイベントが見つかりました**（上位{shown}件を表示）")
        for event in data.get("events", []):
            st.markdown(f"{event.get('index', '')}. **{event.get('title', '無題')}**")
            image_url = event.get("image_url")
            if image_url:
                st.image(image_url, width=450)
            st.markdown(f"📅 {event.get('date', '未定')}")
            st.markdown(f"📍 {event.get('address', 'オンライン')}")
            st.markdown(f"👥 {event.get('capacity', '')}")
            st.markdown(f"🔗 {event.get('url', '')}")
        return

    if text.strip():
        st.markdown(text)

st.set_page_config(page_title="connpassイベント検索", page_icon="🔍")
st.title("🔍 connpassイベント検索")
st.caption("自然言語で技術イベントを探せます")

# エージェント初期化
if "agent" not in st.session_state:
    st.session_state.agent = create_agent()

# チャット履歴初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# チャット履歴表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_response(msg["content"])

# ユーザー入力
if prompt := st.chat_input("例: 来週東京でPythonの勉強会ある？"):
    # ユーザーメッセージを追加
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # エージェント実行
    with st.chat_message("assistant"):
        status_container = st.status("🔍 検索中...", expanded=True)
        response = ""
        tool_response = ""
        
        for chunk in st.session_state.agent.stream(
            {"messages": [{"role": "user", "content": prompt}]}
        ):
            # ノード名を取得
            node_name = list(chunk.keys())[0]
            node_data = chunk[node_name]
            
            if node_name == "agent":
                # LLMの思考/ツール呼び出し判断
                messages = node_data.get("messages", [])
                for msg in messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.get("name", "unknown")
                            status_container.update(label=f"🛠️ ツール「{tool_name}」を呼び出し中...")
                            status_container.write(f"📡 {tool_name} を実行しています...")
                    elif hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
                        # 最終回答（ツール呼び出しがないメッセージ）
                        response = msg.content
            
            elif node_name == "tools":
                # ツール実行結果
                messages = node_data.get("messages", [])
                for msg in messages:
                    if hasattr(msg, "content"):
                        status_container.update(label="📊 検索結果を処理中...")
                        status_container.write("✅ データ取得完了、回答を生成中...")
                        tool_response = msg.content or ""
        
        status_container.update(label="✨ 完了!", state="complete", expanded=False)

        # LLMの最終回答がない場合のみ、ツール結果を表示する
        if tool_response and not response:
            response = tool_response
        render_response(response)

    # アシスタントメッセージを追加
    st.session_state.messages.append({"role": "assistant", "content": response})
