"""
Simple vectorized BTC/ETH pair trading backtest.

This script uses the same CSV as main_pair_backtest.py:

    data/btc_eth_1s_30m.csv

The goal is to compare styles:
    - main_pair_backtest.py is event-driven and uses TradingEngine callbacks
    - this file uses pandas columns to calculate spread, z-score, position,
      transaction cost, PnL, equity, and drawdown

This is intentionally simpler than the event-driven strategy. It is useful for
fast research, but it does not model order objects, callbacks, partial fills, or
live-trading control flow.
"""

from pathlib import Path

import numpy as np
import pandas as pd


CURRENT_DIR = Path(__file__).resolve().parent
MARKET_DATA_FILE = CURRENT_DIR / "data" / "btc_eth_1s_30m.csv"

INITIAL_CAPITAL = 10000.0
BASE_SYMBOL = "BTCUSDT"
HEDGE_SYMBOL = "ETHUSDT"
BASE_QUANTITY = 0.001
HEDGE_QUANTITY = 0.035
SPREAD_WINDOW_SIZE = 60
ENTRY_Z_SCORE = 2.0
EXIT_Z_SCORE = 0.5
SPREAD_BPS = 2.0


def load_market_data():
    if not MARKET_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Market data file not found: {MARKET_DATA_FILE}\n"
            "Run download_binance_1s_data.py first."
        )

    df = pd.read_csv(MARKET_DATA_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df[["timestamp", BASE_SYMBOL, HEDGE_SYMBOL]].dropna().reset_index(drop=True)


def calculate_pair_signal(df):
    result = df.copy()

    result["spread"] = np.log(result[BASE_SYMBOL]) - np.log(result[HEDGE_SYMBOL])
    result["spread_mean"] = result["spread"].rolling(SPREAD_WINDOW_SIZE).mean()
    result["spread_std"] = result["spread"].rolling(SPREAD_WINDOW_SIZE).std(ddof=0)
    result["z_score"] = (
        (result["spread"] - result["spread_mean"]) / result["spread_std"]
    )

    result["target_state"] = np.nan
    result.loc[result["z_score"] <= -ENTRY_Z_SCORE, "target_state"] = 1.0
    result.loc[result["z_score"] >= ENTRY_Z_SCORE, "target_state"] = -1.0
    result.loc[result["z_score"].abs() <= EXIT_Z_SCORE, "target_state"] = 0.0
    result["target_state"] = result["target_state"].ffill().fillna(0.0)

    result["base_position"] = result["target_state"] * BASE_QUANTITY
    result["hedge_position"] = -result["target_state"] * HEDGE_QUANTITY

    return result


def calculate_vectorized_pnl(df):
    result = df.copy()

    result["base_trade_quantity"] = result["base_position"].diff().fillna(result["base_position"])
    result["hedge_trade_quantity"] = result["hedge_position"].diff().fillna(result["hedge_position"])

    half_spread_cost = SPREAD_BPS / 10000.0 / 2.0
    result["transaction_cost"] = (
        result["base_trade_quantity"].abs() * result[BASE_SYMBOL] * half_spread_cost
        + result["hedge_trade_quantity"].abs() * result[HEDGE_SYMBOL] * half_spread_cost
    )

    result["base_price_change"] = result[BASE_SYMBOL].diff().fillna(0.0)
    result["hedge_price_change"] = result[HEDGE_SYMBOL].diff().fillna(0.0)

    result["base_pnl"] = result["base_position"].shift(1).fillna(0.0) * result["base_price_change"]
    result["hedge_pnl"] = result["hedge_position"].shift(1).fillna(0.0) * result["hedge_price_change"]
    result["gross_pnl"] = result["base_pnl"] + result["hedge_pnl"]
    result["net_pnl"] = result["gross_pnl"] - result["transaction_cost"]
    result["total_pnl"] = result["net_pnl"].cumsum()
    result["equity"] = INITIAL_CAPITAL + result["total_pnl"]

    result["peak_equity"] = result["equity"].cummax()
    result["drawdown"] = result["equity"] - result["peak_equity"]
    result["drawdown_pct"] = result["drawdown"] / result["peak_equity"]

    return result


def print_summary(result):
    trade_count = int(
        (
            (result["base_trade_quantity"].abs() > 0)
            | (result["hedge_trade_quantity"].abs() > 0)
        ).sum()
    )

    print("Vectorized pair backtest summary")
    print("-" * 80)
    print(f"rows                 = {len(result)}")
    print(f"initial_capital      = {INITIAL_CAPITAL:.2f}")
    print(f"final_equity         = {result['equity'].iloc[-1]:.2f}")
    print(f"total_pnl            = {result['total_pnl'].iloc[-1]:.4f}")
    print(f"gross_pnl            = {result['gross_pnl'].sum():.4f}")
    print(f"transaction_cost     = {result['transaction_cost'].sum():.4f}")
    print(f"max_drawdown         = {result['drawdown'].min():.4f}")
    print(f"max_drawdown_pct     = {result['drawdown_pct'].min() * 100:.4f}%")
    print(f"trade_count          = {trade_count}")
    print(f"final_base_position  = {result['base_position'].iloc[-1]:.6f}")
    print(f"final_hedge_position = {result['hedge_position'].iloc[-1]:.6f}")
    print()

    print("Last 10 rows")
    print("-" * 80)
    columns = [
        "timestamp",
        BASE_SYMBOL,
        HEDGE_SYMBOL,
        "z_score",
        "target_state",
        "base_position",
        "hedge_position",
        "net_pnl",
        "equity",
    ]
    print(result[columns].tail(10))


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:.6f}".format)

    market_data = load_market_data()
    signal_data = calculate_pair_signal(market_data)
    backtest_result = calculate_vectorized_pnl(signal_data)
    print_summary(backtest_result)
