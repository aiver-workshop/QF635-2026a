"""
Calculate the BTC/ETH covariance matrix using the standard sample covariance formula.

The CSV contains prices, so this script first converts BTCUSDT and ETHUSDT prices
into log returns, then applies:

    covariance = centered_returns.T @ centered_returns / (n - 1)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = Path(__file__).parent / "pair_backtest" / "data" / "btc_eth_1s_30m.csv"
PRICE_COLUMNS = ["BTCUSDT", "ETHUSDT"]


def load_log_returns(csv_path: Path) -> pd.DataFrame:
    prices = pd.read_csv(csv_path, parse_dates=["timestamp"])
    prices = prices.sort_values("timestamp")

    log_prices = np.log(prices[PRICE_COLUMNS])
    log_returns = log_prices.diff().dropna()

    return log_returns


def calculate_sample_covariance(returns: pd.DataFrame) -> pd.DataFrame:
    n_observations = len(returns)

    if n_observations < 2:
        raise ValueError("At least two return observations are needed for covariance.")

    centered_returns = returns - returns.mean()
    covariance = centered_returns.T @ centered_returns / (n_observations - 1)

    return pd.DataFrame(
        covariance,
        index=PRICE_COLUMNS,
        columns=PRICE_COLUMNS,
    )


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:.10f}".format)

    returns = load_log_returns(DATA_FILE)
    covariance_matrix = calculate_sample_covariance(returns)
    correlation_matrix = returns.corr()

    print(f"Data file: {DATA_FILE}")
    print(f"Return observations: {len(returns)}")
    print()

    print("Standard sample covariance matrix")
    print(covariance_matrix)
    print()

    print("Sample correlation matrix")
    print(correlation_matrix)
