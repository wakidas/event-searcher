"""connpass API v2 検索ツール"""

import os
from datetime import datetime, timedelta
from typing import Optional

import requests
from langchain_core.tools import tool

CONNPASS_API_URL = "https://connpass.com/api/v2/events/"


@tool
def search_connpass_events(
    keyword: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    location: Optional[str] = None,
) -> str:
    """connpass APIでイベントを検索します。

    Args:
        keyword: 検索キーワード（例: Python, React, AWS）
        start_date: 開始日（YYYY-MM-DD形式）。指定しない場合は今日から検索。
        end_date: 終了日（YYYY-MM-DD形式）。指定しない場合は1ヶ月先まで。
        location: 場所フィルター（"東京" または "オンライン"）

    Returns:
        検索結果のイベント一覧（テキスト形式）
    """
    api_key = os.getenv("CONNPASS_API_KEY")
    if not api_key:
        return "エラー: CONNPASS_API_KEYが設定されていません。.envファイルを確認してください。"

    # 日付範囲を生成
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start = datetime.now()

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end = start + timedelta(days=30)

    # ymd形式のリストを作成
    ymd_list = []
    current = start
    while current <= end and len(ymd_list) < 31:
        ymd_list.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)

    params = {
        "keyword": keyword,
        "ymd": ",".join(ymd_list) if ymd_list else None,
        "count": 30,
        "order": 2,  # 開催日時順
    }

    # 場所フィルター（v2 APIのprefectureパラメータ）
    if location:
        if location == "オンライン":
            params["prefecture"] = "online"
        elif location == "東京":
            params["prefecture"] = "東京都"

    # Noneの値を除去
    params = {k: v for k, v in params.items() if v is not None}

    headers = {
        "X-API-Key": api_key,
        "User-Agent": "EventSearcher/1.0",
    }

    try:
        response = requests.get(CONNPASS_API_URL, params=params, headers=headers, timeout=10)
        # デバッグ: ステータスコードとレスポンスを確認
        if response.status_code != 200:
            return f"APIエラー: status={response.status_code}, body={response.text}, url={response.url}"
        data = response.json()
    except requests.RequestException as e:
        return f"APIリクエストエラー: {e}"

    events = data.get("events", [])

    if not events:
        return "該当するイベントが見つかりませんでした。"

    # 結果をフォーマット
    results = []
    for i, event in enumerate(events[:10], 1):
        started_at = event.get("started_at", "")
        if started_at:
            dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y/%m/%d %H:%M")
        else:
            date_str = "未定"

        address = event.get("address") or "オンライン"
        accepted = event.get("accepted", 0)
        limit = event.get("limit")
        capacity = f"{accepted}/{limit}人" if limit else f"{accepted}人参加"

        results.append(
            f"{i}. **{event.get('title', '無題')}**\n"
            f"   📅 {date_str}\n"
            f"   📍 {address}\n"
            f"   👥 {capacity}\n"
            f"   🔗 {event.get('event_url', '')}"
        )

    header = f"**{len(events)}件のイベントが見つかりました**（上位10件を表示）\n\n"
    return header + "\n\n".join(results)


def get_tools():
    """利用可能なツールのリストを返す"""
    return [search_connpass_events]
