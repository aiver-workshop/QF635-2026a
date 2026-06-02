"""
Demonstrate White's Reality Check.

White's Reality Check asks:

    If I test many strategies, is the best one genuinely good,
    or did it only look good because I tried many alternatives?

This script creates several example strategy return series, finds the best
average excess return, then uses a moving block bootstrap to estimate a
data-snooping-adjusted p-value.

Interpretation:
    small p-value  -> the best strategy is unlikely to be luck
    large p-value  -> the best strategy may be a false discovery
"""

from __future__ import annotations

import numpy as np
import pandas as pd


RANDOM_SEED = 7
N_DAYS = 500
N_STRATEGIES = 20
BOOTSTRAP_SAMPLES = 2000
BLOCK_SIZE = 10
TRADING_DAYS_PER_YEAR = 252


def simulate_strategy_returns() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)

    market_return = rng.normal(loc=0.0002, scale=0.0100, size=N_DAYS)

    strategy_returns = {}
    for strategy_index in range(N_STRATEGIES):
        noise = rng.normal(loc=0.0, scale=0.0060, size=N_DAYS)
        beta = rng.normal(loc=0.2, scale=0.1)
        alpha = 0.0

        # Add one small true edge so the example has something to detect.
        if strategy_index == 3:
            alpha = 0.0008

        strategy_returns[f"strategy_{strategy_index + 1:02d}"] = (
            alpha + beta * market_return + noise
        )

    df = pd.DataFrame(strategy_returns)
    df["benchmark"] = market_return
    return df


def calculate_performance_table(excess_returns: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for strategy_name in excess_returns.columns:
        daily_mean = excess_returns[strategy_name].mean()
        daily_std = excess_returns[strategy_name].std(ddof=1)
        annualized_return = daily_mean * TRADING_DAYS_PER_YEAR
        annualized_volatility = daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)
        sharpe = annualized_return / annualized_volatility

        rows.append(
            {
                "strategy": strategy_name,
                "daily_mean_excess": daily_mean,
                "annualized_excess": annualized_return,
                "annualized_volatility": annualized_volatility,
                "sharpe": sharpe,
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values("daily_mean_excess", ascending=False)
        .reset_index(drop=True)
    )


def sample_moving_block_indices(
    n_observations: int,
    block_size: int,
    rng: np.random.Generator,
) -> np.ndarray:
    sampled_indices = []

    while len(sampled_indices) < n_observations:
        start_index = rng.integers(0, n_observations - block_size + 1)
        block_indices = range(start_index, start_index + block_size)
        sampled_indices.extend(block_indices)

    return np.array(sampled_indices[:n_observations])


def whites_reality_check(
    excess_returns: pd.DataFrame,
    bootstrap_samples: int,
    block_size: int,
) -> dict:
    values = excess_returns.to_numpy()
    n_observations = values.shape[0]
    rng = np.random.default_rng(RANDOM_SEED)

    strategy_mean = values.mean(axis=0)
    observed_best_mean = strategy_mean.max()
    observed_best_index = strategy_mean.argmax()
    observed_test_stat = np.sqrt(n_observations) * observed_best_mean

    # Center each strategy under the null hypothesis of no outperformance.
    centered_values = values - strategy_mean

    bootstrap_test_stats = []
    for _ in range(bootstrap_samples):
        sample_indices = sample_moving_block_indices(
            n_observations=n_observations,
            block_size=block_size,
            rng=rng,
        )
        bootstrap_sample = centered_values[sample_indices, :]
        bootstrap_strategy_mean = bootstrap_sample.mean(axis=0)
        bootstrap_test_stat = np.sqrt(n_observations) * bootstrap_strategy_mean.max()
        bootstrap_test_stats.append(bootstrap_test_stat)

    bootstrap_test_stats = np.array(bootstrap_test_stats)
    p_value = np.mean(bootstrap_test_stats >= observed_test_stat)

    return {
        "best_strategy": excess_returns.columns[observed_best_index],
        "observed_best_mean": observed_best_mean,
        "observed_test_stat": observed_test_stat,
        "bootstrap_95pct": np.quantile(bootstrap_test_stats, 0.95),
        "p_value": p_value,
    }


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:.6f}".format)

    returns = simulate_strategy_returns()
    strategy_columns = [col for col in returns.columns if col != "benchmark"]
    excess_returns = returns[strategy_columns].subtract(returns["benchmark"], axis=0)

    performance_table = calculate_performance_table(excess_returns)
    reality_check = whites_reality_check(
        excess_returns=excess_returns,
        bootstrap_samples=BOOTSTRAP_SAMPLES,
        block_size=BLOCK_SIZE,
    )

    print("Top strategies by raw average excess return")
    print(performance_table.head(10))
    print()

    print("White's Reality Check")
    print("-" * 60)
    print(f"best_strategy       = {reality_check['best_strategy']}")
    print(f"observed_best_mean  = {reality_check['observed_best_mean']:.6f}")
    print(f"observed_test_stat  = {reality_check['observed_test_stat']:.6f}")
    print(f"bootstrap_95pct     = {reality_check['bootstrap_95pct']:.6f}")
    print(f"p_value             = {reality_check['p_value']:.4f}")
    print()

    if reality_check["p_value"] < 0.05:
        print("Conclusion: reject the null. The best strategy looks significant after data snooping adjustment.")
    else:
        print("Conclusion: do not reject the null. The best strategy may be luck after testing many strategies.")
