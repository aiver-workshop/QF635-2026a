"""
Query Alpha Vantage news sentiment.

This script demonstrates how to call the Alpha Vantage NEWS_SENTIMENT endpoint
and print a compact summary of recent articles.

Examples:
    python query_alphavantage_news_sentiment.py
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests


BASE_URL = "https://www.alphavantage.co/query"
API_KEY = "MHRMKWZ9XJH9C5EB"
TICKERS = "NVDA"
TOPICS = None
TIME_FROM = None
TIME_TO = None
SORT = "LATEST"
LIMIT = 10


def query_news_sentiment(
    api_key: str,
    tickers: str | None = None,
    topics: str | None = None,
    time_from: str | None = None,
    time_to: str | None = None,
    sort: str = "LATEST",
    limit: int = 10,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "function": "NEWS_SENTIMENT",
        "apikey": api_key,
        "sort": sort,
        "limit": limit,
    }

    if tickers:
        params["tickers"] = tickers
    if topics:
        params["topics"] = topics
    if time_from:
        params["time_from"] = time_from
    if time_to:
        params["time_to"] = time_to

    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()
    if "Error Message" in data:
        raise RuntimeError(data["Error Message"])
    if "Information" in data:
        raise RuntimeError(data["Information"])

    return data


def format_alpha_time(value: str) -> str:
    if not value:
        return "-"

    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def format_ticker_sentiment(article: dict[str, Any], requested_tickers: set[str]) -> str:
    ticker_sentiment = article.get("ticker_sentiment", [])
    formatted_items = []

    for item in ticker_sentiment:
        ticker = item.get("ticker", "")
        if requested_tickers and ticker not in requested_tickers:
            continue

        score = item.get("ticker_sentiment_score", "-")
        label = item.get("ticker_sentiment_label", "-")
        relevance = item.get("relevance_score", "-")
        formatted_items.append(
            f"{ticker}: sentiment={score} label={label} relevance={relevance}"
        )

    return "; ".join(formatted_items) if formatted_items else "-"


def print_news_summary(data: dict[str, Any], tickers: str | None) -> None:
    feed = data.get("feed", [])
    requested_tickers = {
        ticker.strip().upper()
        for ticker in (tickers or "").split(",")
        if ticker.strip()
    }

    print(f"Items returned: {len(feed)}")
    print()

    for index, article in enumerate(feed, start=1):
        title = article.get("title", "-")
        source = article.get("source", "-")
        url = article.get("url", "-")
        time_published = format_alpha_time(article.get("time_published", ""))
        overall_score = article.get("overall_sentiment_score", "-")
        overall_label = article.get("overall_sentiment_label", "-")
        ticker_summary = format_ticker_sentiment(article, requested_tickers)

        print(f"{index}. {title}")
        print(f"   source: {source}")
        print(f"   time: {time_published}")
        print(f"   overall: sentiment={overall_score} label={overall_label}")
        print(f"   tickers: {ticker_summary}")
        print(f"   url: {url}")
        print()


if __name__ == "__main__":
    result = query_news_sentiment(
        api_key=API_KEY,
        tickers=TICKERS,
        topics=TOPICS,
        time_from=TIME_FROM,
        time_to=TIME_TO,
        sort=SORT,
        limit=LIMIT,
    )
    print_news_summary(result, TICKERS)
