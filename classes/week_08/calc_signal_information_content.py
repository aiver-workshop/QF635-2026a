"""
Measure signal information content.

Information content is commonly measured with Information Coefficient (IC):

    IC = corr(signal at time t, future return from t to t+h)

If IC is positive, high signal values tend to predict positive future returns.
If IC is negative, high signal values tend to predict negative future returns.
If IC is near zero, the signal has little predictive information.

This script demonstrates:
    - Pearson IC: linear correlation between signal and future return
    - Rank IC: rank correlation, useful when only ordering matters
    - IC t-stat: rough strength of the correlation
    - Hit rate: how often signal direction matches future return direction
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


RANDOM_SEED = 42
N_DAYS = 1000
SIGNAL_EDGE = 0.0015
RETURN_VOLATILITY = 0.0100
HORIZONS = [1, 2, 5, 10, 20]


def simulate_price_and_signal() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    dates = pd.date_range("2022-01-01", periods=N_DAYS, freq="B")

    signal = rng.normal(loc=0.0, scale=1.0, size=N_DAYS)
    noise = rng.normal(loc=0.0, scale=RETURN_VOLATILITY, size=N_DAYS)

    daily_return = noise.copy()

    # Plant a small predictive relationship:
    # signal[t] helps predict return[t+1].
    daily_return[1:] = noise[1:] + SIGNAL_EDGE * signal[:-1]

    close = 100.0 * np.cumprod(1.0 + daily_return)

    return pd.DataFrame(
        {
            "date": dates,
            "close": close,
            "signal": signal,
            "daily_return": daily_return,
        }
    )


def add_forward_returns(df: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    result = df.copy()

    for horizon in horizons:
        result[f"future_return_{horizon}d"] = (
            result["close"].shift(-horizon) / result["close"] - 1.0
        )

    return result


def calculate_t_stat(correlation: float, n_observations: int) -> float:
    if n_observations <= 2:
        return 0.0

    if abs(correlation) >= 1.0:
        return math.inf if correlation > 0 else -math.inf

    return correlation * math.sqrt((n_observations - 2) / (1.0 - correlation ** 2))


def normal_approx_two_sided_p_value(t_stat: float) -> float:
    # For teaching purposes, use a normal approximation to the t-stat p-value.
    return math.erfc(abs(t_stat) / math.sqrt(2.0))


def calculate_hit_rate(signal: pd.Series, future_return: pd.Series) -> float:
    signal_direction = np.sign(signal)
    return_direction = np.sign(future_return)
    valid = (signal_direction != 0) & (return_direction != 0)

    if valid.sum() == 0:
        return 0.0

    return (signal_direction[valid] == return_direction[valid]).mean()


def calculate_information_content(
    df: pd.DataFrame,
    signal_column: str,
    horizons: list[int],
) -> pd.DataFrame:
    rows = []

    for horizon in horizons:
        future_return_column = f"future_return_{horizon}d"
        clean = df[[signal_column, future_return_column]].dropna()

        signal = clean[signal_column]
        future_return = clean[future_return_column]

        pearson_ic = signal.corr(future_return)
        rank_ic = signal.rank().corr(future_return.rank())
        n_observations = len(clean)
        t_stat = calculate_t_stat(pearson_ic, n_observations)
        p_value = normal_approx_two_sided_p_value(t_stat)
        hit_rate = calculate_hit_rate(signal, future_return)

        rows.append(
            {
                "horizon": f"{horizon}d",
                "n": n_observations,
                "pearson_ic": pearson_ic,
                "rank_ic": rank_ic,
                "t_stat": t_stat,
                "approx_p_value": p_value,
                "hit_rate": hit_rate,
                "mean_future_return": future_return.mean(),
            }
        )

    return pd.DataFrame(rows)


def calculate_signal_bucket_returns(
    df: pd.DataFrame,
    signal_column: str,
    future_return_column: str,
    n_buckets: int = 5,
) -> pd.DataFrame:
    clean = df[[signal_column, future_return_column]].dropna().copy()
    clean["signal_bucket"] = pd.qcut(
        clean[signal_column],
        q=n_buckets,
        labels=[f"bucket_{i + 1}" for i in range(n_buckets)],
    )

    return (
        clean.groupby("signal_bucket", observed=True)
        .agg(
            average_signal=(signal_column, "mean"),
            average_future_return=(future_return_column, "mean"),
            count=(future_return_column, "count"),
        )
        .reset_index()
    )


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:.6f}".format)

    data = simulate_price_and_signal()
    data = add_forward_returns(data, HORIZONS)

    information_content = calculate_information_content(
        df=data,
        signal_column="signal",
        horizons=HORIZONS,
    )

    bucket_returns = calculate_signal_bucket_returns(
        df=data,
        signal_column="signal",
        future_return_column="future_return_1d",
        n_buckets=5,
    )

    print("Signal information content")
    print("-" * 80)
    print(information_content)
    print()

    print("1-day future return by signal bucket")
    print("-" * 80)
    print(bucket_returns)
    print()

    print("Interpretation")
    print("-" * 80)
    print("Positive IC means high signal values predict higher future returns.")
    print("Rank IC checks whether the signal sorts returns correctly.")
    print("Hit rate checks whether signal direction matches return direction.")
    print("Bucket returns show whether stronger signals lead to stronger returns.")
