"""
Download recent BTCUSDT and ETHUSDT 1-second data for the pair backtest.

Binance Futures aggregate trades are downloaded from the public REST API and
resampled into 1-second prices. The output CSV can be loaded by
main_pair_backtest.py.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

import pandas as pd
import requests


BASE_URL = "https://fapi.binance.com"
AGG_TRADES_ENDPOINT = "/fapi/v1/aggTrades"

CURRENT_DIR = Path(__file__).resolve().parent
DATA_DIR = CURRENT_DIR / "data"
OUTPUT_FILE = DATA_DIR / "btc_eth_1s_30m.csv"

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
LOOKBACK_MINUTES = 30
REQUEST_LIMIT = 1000
REQUEST_SLEEP_SECONDS = 0.10


def download_aggregate_trades(
    symbol,
    start_time_ms,
    end_time_ms,
):
    rows = []
    next_start_time_ms = start_time_ms

    while next_start_time_ms < end_time_ms:
        params = {
            "symbol": symbol,
            "startTime": next_start_time_ms,
            "endTime": end_time_ms,
            "limit": REQUEST_LIMIT,
        }
        response = requests.get(
            BASE_URL + AGG_TRADES_ENDPOINT,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        trades = response.json()

        if not trades:
            break

        rows.extend(trades)
        last_trade_time_ms = int(trades[-1]["T"])
        next_start_time_ms = last_trade_time_ms + 1

        if len(trades) < REQUEST_LIMIT:
            break

        time.sleep(REQUEST_SLEEP_SECONDS)

    if not rows:
        raise RuntimeError(f"No trades returned for {symbol}")

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["T"], unit="ms", utc=True)
    df["price"] = df["p"].astype(float)
    df = df[["timestamp", "price"]].drop_duplicates()
    df = df.sort_values("timestamp")

    return df


def resample_to_one_second(df, symbol):
    one_second = (
        df.set_index("timestamp")["price"]
        .resample("1s")
        .last()
        .ffill()
        .rename(symbol)
        .to_frame()
    )

    return one_second


def build_pair_price_table(
    start_time,
    end_time,
):
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)

    price_tables = []
    for symbol in SYMBOLS:
        print(f"Downloading {symbol} aggregate trades...")
        trades = download_aggregate_trades(
            symbol=symbol,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
        )
        one_second_prices = resample_to_one_second(trades, symbol)
        price_tables.append(one_second_prices)
        print(f"{symbol}: trades={len(trades)} seconds={len(one_second_prices)}")

    pair_prices = pd.concat(price_tables, axis=1).ffill().dropna()
    pair_prices = pair_prices.reset_index()
    pair_prices["timestamp"] = pair_prices["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return pair_prices


if __name__ == "__main__":
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=LOOKBACK_MINUTES)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pair_price_table = build_pair_price_table(
        start_time=start_time,
        end_time=end_time,
    )
    pair_price_table.to_csv(OUTPUT_FILE, index=False)

    print()
    print(f"Saved {len(pair_price_table)} rows to:")
    print(OUTPUT_FILE)
    print()
    print(pair_price_table.head())
    print()
    print(pair_price_table.tail())
