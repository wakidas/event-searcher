"""connpass API v2 検索ツール"""

import logging
import os
import json
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)
from langchain_core.tools import tool

CONNPASS_API_URL = "https://connpass.com/api/v2/events/"


@tool
def search_connpass_events(
    keyword: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    locations: Optional[list[str]] = None,
) -> str:
    """connpass APIでイベントを検索します。

    Args:
        keyword: 検索キーワード（例: Python, React, AWS）
        start_date: 開始日（YYYY-MM-DD形式）。指定しない場合は今日から検索。
        end_date: 終了日（YYYY-MM-DD形式）。指定しない場合は1ヶ月先まで。
        locations: 場所フィルターのリスト（例: ["東京都", "online"]）。指定しない場合は全国検索。

    Returns:
        検索結果のイベント一覧（JSON文字列）
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
        "prefecture": ",".join(locations) if locations else None,
    }

    # Noneの値を除去
    params = {k: v for k, v in params.items() if v is not None}

    headers = {
        "X-API-Key": api_key,
        "User-Agent": "EventSearcher/1.0",
    }

    try:
        response = requests.get(CONNPASS_API_URL, params=params, headers=headers, timeout=10)
        if response.status_code == 429:
            logger.warning("connpass API rate limit hit: %s", response.url)
        if response.status_code != 200:
            return f"APIエラー: status={response.status_code}, body={response.text}, url={response.url}"
        data = response.json()
    except requests.RequestException as e:
        return f"APIリクエストエラー: {e}"

    events = data.get("events", [])

    # 開催日が近い順にソート
    events.sort(key=lambda e: e.get("started_at", "") or "9999-12-31")

    if not events:
        return "該当するイベントが見つかりませんでした。"

    # 結果を構造化
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

        image_url = event.get("image_url")

        results.append(
            {
                "index": i,
                "title": event.get("title", "無題"),
                "date": date_str,
                "address": address,
                "capacity": capacity,
                "url": event.get("url", ""),
                "image_url": image_url,
            }
        )

    payload = {
        "total": len(events),
        "shown": len(results),
        "events": results,
    }
    return json.dumps(payload, ensure_ascii=False)


def get_tools():
    """利用可能なツールのリストを返す"""
    return [search_connpass_events]
