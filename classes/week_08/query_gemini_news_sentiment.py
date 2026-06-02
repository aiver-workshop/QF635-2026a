"""
Use Gemini AI to extract news sentiment.

This script takes a raw news paragraph and asks Gemini to return a structured
sentiment result similar to Alpha Vantage NEWS_SENTIMENT output:
    - generated title
    - short summary
    - topics with relevance scores
    - overall sentiment score and label
    - relevant companies discovered from the news
    - per-company ticker, relevance, relationship, and sentiment

Install the Gemini SDK first:
    pip install google-genai
"""

from __future__ import annotations

import json
import os
from typing import Any


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

NEWS_TEXT = """
Nvidia is entering the personal computer chip market with its new RTX Spark
super chip, co-developed with MediaTek, set to launch in laptops and desktops
this autumn. This move challenges the dominance of Intel and AMD in the sector.
The initial focus will be on the high-end market, with future versions expanding
to a broader price range.
"""

COMPANY_HINTS = []
MIN_RELEVANCE_SCORE = 0.30


NEWS_SENTIMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "relevance_score": {"type": "number"},
                },
                "required": ["topic", "relevance_score"],
            },
        },
        "overall_sentiment_score": {"type": "number"},
        "overall_sentiment_label": {"type": "string"},
        "company_sentiment": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "ticker": {"type": "string"},
                    "ticker_confidence": {"type": "number"},
                    "relationship_to_news": {"type": "string"},
                    "directly_mentioned": {"type": "boolean"},
                    "relevance_score": {"type": "number"},
                    "sentiment_score": {"type": "number"},
                    "sentiment_label": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": [
                    "company_name",
                    "ticker",
                    "ticker_confidence",
                    "relationship_to_news",
                    "directly_mentioned",
                    "relevance_score",
                    "sentiment_score",
                    "sentiment_label",
                    "reason",
                ],
            },
        },
    },
    "required": [
        "title",
        "summary",
        "topics",
        "overall_sentiment_score",
        "overall_sentiment_label",
        "company_sentiment",
    ],
}


def build_prompt(
    news_text: str,
    company_hints: list[str],
    min_relevance_score: float,
) -> str:
    hint_text = ", ".join(company_hints) if company_hints else "None provided"
    return f"""
You are a financial news sentiment extraction engine.

Analyze the news text and produce a JSON object similar to Alpha Vantage
NEWS_SENTIMENT, but also discover relevant companies when tickers are not given.

Rules:
- Sentiment score must be between -1.0 and 1.0.
- Relevance score must be between 0.0 and 1.0.
- Ticker confidence must be between 0.0 and 1.0.
- Use these sentiment labels only:
  Bearish, Somewhat-Bearish, Neutral, Somewhat-Bullish, Bullish.
- Overall sentiment should describe the article as a whole.
- Company sentiment should describe how the article affects each company.
- Discover companies that are directly mentioned or economically affected.
- Include direct competitors, suppliers, partners, customers, and ecosystem beneficiaries.
- Only include companies with relevance_score >= {min_relevance_score}.
- If the ticker is confidently known, provide it.
- If the ticker is not confidently known, use an empty string for ticker and a low ticker_confidence.
- Do not invent ticker symbols when uncertain.
- Keep reasons short and trading-focused.

Optional company hints:
{hint_text}

News text:
{news_text.strip()}
"""


def query_gemini_news_sentiment(
    api_key: str,
    model: str,
    news_text: str,
    company_hints: list[str],
    min_relevance_score: float,
) -> dict[str, Any]:
    try:
        from google import genai
    except ImportError as error:
        raise RuntimeError("Missing Gemini SDK. Install it with: pip install google-genai") from error

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(news_text, company_hints, min_relevance_score)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": NEWS_SENTIMENT_SCHEMA,
        },
    )

    return json.loads(response.text)


def print_sentiment_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=4))
    print()

    print("Company sentiment summary")
    print("-" * 120)
    print(
        f"{'Company':<22} {'Ticker':<8} {'Rel':>6} {'Score':>8} "
        f"{'Label':<18} {'Relationship':<24} Reason"
    )
    print("-" * 120)

    for item in result.get("company_sentiment", []):
        company_name = item.get("company_name", "-")
        ticker = item.get("ticker", "-")
        if ticker == "":
            ticker = "-"
        relevance = float(item.get("relevance_score", 0.0))
        score = float(item.get("sentiment_score", 0.0))
        label = item.get("sentiment_label", "-")
        relationship = item.get("relationship_to_news", "-")
        reason = item.get("reason", "-")

        print(
            f"{company_name:<22} {ticker:<8} {relevance:>6.3f} {score:>8.3f} "
            f"{label:<18} {relationship:<24} {reason}"
        )


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        raise RuntimeError("Set GEMINI_API_KEY before running this script.")

    sentiment_result = query_gemini_news_sentiment(
        api_key=GEMINI_API_KEY,
        model=GEMINI_MODEL,
        news_text=NEWS_TEXT,
        company_hints=COMPANY_HINTS,
        min_relevance_score=MIN_RELEVANCE_SCORE,
    )
    print_sentiment_result(sentiment_result)
