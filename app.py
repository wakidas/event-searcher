"""Streamlit UI"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent import create_agent

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
        st.markdown(msg["content"])

# ユーザー入力
if prompt := st.chat_input("例: 来週東京でPythonの勉強会ある？"):
    # ユーザーメッセージを追加
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # エージェント実行
    with st.chat_message("assistant"):
        with st.spinner("検索中..."):
            result = st.session_state.agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
            response = result["messages"][-1].content
            st.markdown(response)

    # アシスタントメッセージを追加
    st.session_state.messages.append({"role": "assistant", "content": response})
