"""
Calculate time-decayed sentiment.

News sentiment should usually fade over time. This script demonstrates a simple
exponential decay model:

    decayed_sentiment = sentiment_score * exp(-decay_rate * age)

where:
    decay_rate = ln(2) / half_life

If half_life is 6 hours, a sentiment score of 1.0 becomes:
    0 hours old  -> 1.0000
    6 hours old  -> 0.5000
    12 hours old -> 0.2500
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pandas as pd


HALF_LIFE_HOURS = 6.0
NOW = datetime(2026, 6, 1, 16, 0, 0)

NEWS_EVENTS = [
    {
        "time": NOW - timedelta(hours=1),
        "ticker": "NVDA",
        "sentiment_score": 0.70,
        "relevance_score": 0.90,
        "headline": "Nvidia enters PC chip market",
    },
    {
        "time": NOW - timedelta(hours=4),
        "ticker": "NVDA",
        "sentiment_score": 0.40,
        "relevance_score": 0.60,
        "headline": "Analysts discuss Nvidia AI PC opportunity",
    },
    {
        "time": NOW - timedelta(hours=10),
        "ticker": "NVDA",
        "sentiment_score": -0.30,
        "relevance_score": 0.80,
        "headline": "Concern over chip supply constraints",
    },
    {
        "time": NOW - timedelta(hours=2),
        "ticker": "AMD",
        "sentiment_score": -0.50,
        "relevance_score": 0.85,
        "headline": "AMD faces new competition from Nvidia",
    },
    {
        "time": NOW - timedelta(hours=8),
        "ticker": "AMD",
        "sentiment_score": 0.20,
        "relevance_score": 0.50,
        "headline": "AMD launches new laptop processor",
    },
]


def calculate_decay_weight(age_hours: float, half_life_hours: float) -> float:
    decay_rate = math.log(2.0) / half_life_hours
    return math.exp(-decay_rate * age_hours)


def calculate_decayed_sentiment(
    sentiment_score: float,
    relevance_score: float,
    age_hours: float,
    half_life_hours: float,
) -> float:
    decay_weight = calculate_decay_weight(age_hours, half_life_hours)
    return sentiment_score * relevance_score * decay_weight


def build_decayed_sentiment_table(news_events: list[dict]) -> pd.DataFrame:
    rows = []

    for event in news_events:
        age_hours = (NOW - event["time"]).total_seconds() / 3600.0
        decay_weight = calculate_decay_weight(age_hours, HALF_LIFE_HOURS)
        decayed_sentiment = calculate_decayed_sentiment(
            sentiment_score=event["sentiment_score"],
            relevance_score=event["relevance_score"],
            age_hours=age_hours,
            half_life_hours=HALF_LIFE_HOURS,
        )

        rows.append(
            {
                "time": event["time"],
                "ticker": event["ticker"],
                "headline": event["headline"],
                "age_hours": age_hours,
                "sentiment_score": event["sentiment_score"],
                "relevance_score": event["relevance_score"],
                "decay_weight": decay_weight,
                "decayed_sentiment": decayed_sentiment,
            }
        )

    return pd.DataFrame(rows)


def aggregate_signal_by_ticker(df: pd.DataFrame) -> pd.DataFrame:
    signal = (
        df.groupby("ticker", as_index=False)
        .agg(
            raw_sentiment_sum=("sentiment_score", "sum"),
            decayed_sentiment_sum=("decayed_sentiment", "sum"),
            article_count=("ticker", "count"),
        )
        .sort_values("decayed_sentiment_sum", ascending=False)
    )

    return signal


def print_half_life_examples() -> None:
    print("Decay weight examples")
    print("-" * 40)
    print(f"{'Age Hours':>10} {'Half-Lives':>12} {'Decay Weight':>14}")
    print("-" * 40)

    for half_life_count in range(4):
        age_hours = HALF_LIFE_HOURS * half_life_count
        decay_weight = calculate_decay_weight(age_hours, HALF_LIFE_HOURS)
        print(f"{age_hours:>10.2f} {half_life_count:>12.0f} {decay_weight:>14.4f}")

    print()


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:.4f}".format)
    pd.set_option("display.max_colwidth", 60)

    decayed_table = build_decayed_sentiment_table(NEWS_EVENTS)
    signal_by_ticker = aggregate_signal_by_ticker(decayed_table)

    print(f"NOW = {NOW}")
    print(f"HALF_LIFE_HOURS = {HALF_LIFE_HOURS}")
    print()

    print_half_life_examples()

    print("Article-level decayed sentiment")
    print(decayed_table)
    print()

    print("Ticker-level sentiment signal")
    print(signal_by_ticker)
