"""
Calculate the BTC/ETH covariance matrix using EWMA.

Assumptions:
    - Log returns have zero mean.
    - The starting BTC/ETH correlation is 0.5.

EWMA recursion:

    Sigma_t = lambda * Sigma_{t-1} + (1 - lambda) * r_t @ r_t.T

where r_t is the zero-mean return vector at time t.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = Path(__file__).parent / "pair_backtest" / "data" / "btc_eth_1s_30m.csv"
PRICE_COLUMNS = ["BTCUSDT", "ETHUSDT"]

LAMBDA = 0.94
STARTING_CORRELATION = 0.50
INITIAL_VOL_LOOKBACK = 60


def load_log_returns(csv_path: Path) -> pd.DataFrame:
    prices = pd.read_csv(csv_path, parse_dates=["timestamp"])
    prices = prices.sort_values("timestamp")

    log_prices = np.log(prices[PRICE_COLUMNS])
    log_returns = log_prices.diff().dropna()

    return log_returns


def build_initial_covariance(returns: pd.DataFrame) -> np.ndarray:
    lookback = min(INITIAL_VOL_LOOKBACK, len(returns))

    if lookback < 1:
        raise ValueError("At least one return observation is needed for EWMA.")

    initial_returns = returns.iloc[:lookback]

    # Zero-mean variance estimate: E[r^2].
    initial_variances = (initial_returns**2).mean().to_numpy()
    initial_volatility = np.sqrt(initial_variances)

    covariance = np.diag(initial_variances)
    covariance[0, 1] = STARTING_CORRELATION * initial_volatility[0] * initial_volatility[1]
    covariance[1, 0] = covariance[0, 1]

    return covariance


def calculate_ewma_covariance(returns: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    covariance = build_initial_covariance(returns)
    start_index = min(INITIAL_VOL_LOOKBACK, len(returns))

    for row in returns.iloc[start_index:].to_numpy():
        return_vector = row.reshape(-1, 1)

        # EWMA update: keep lambda of the old covariance and add (1 - lambda) of today's zero-mean return outer product.
        covariance = LAMBDA * covariance + (1.0 - LAMBDA) * (return_vector @ return_vector.T)

    initial_covariance = build_initial_covariance(returns)
    return initial_covariance, covariance


def covariance_to_correlation(covariance: np.ndarray) -> np.ndarray:
    volatility = np.sqrt(np.diag(covariance))
    denominator = np.outer(volatility, volatility)

    return np.divide(
        covariance,
        denominator,
        out=np.zeros_like(covariance),
        where=denominator != 0,
    )


def as_matrix_frame(matrix: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(matrix, index=PRICE_COLUMNS, columns=PRICE_COLUMNS)


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:.10f}".format)

    returns = load_log_returns(DATA_FILE)
    initial_covariance_matrix, ewma_covariance_matrix = calculate_ewma_covariance(returns)
    ewma_correlation_matrix = covariance_to_correlation(ewma_covariance_matrix)

    print(f"Data file: {DATA_FILE}")
    print(f"Return observations: {len(returns)}")
    print(f"Lambda: {LAMBDA:.2f}")
    print(f"Starting correlation: {STARTING_CORRELATION:.2f}")
    print(f"Initial volatility lookback: {min(INITIAL_VOL_LOOKBACK, len(returns))}")
    print()

    print("Initial covariance matrix")
    print(as_matrix_frame(initial_covariance_matrix))
    print()

    print("Final EWMA covariance matrix")
    print(as_matrix_frame(ewma_covariance_matrix))
    print()

    print("Final EWMA correlation matrix")
    print(as_matrix_frame(ewma_correlation_matrix))
