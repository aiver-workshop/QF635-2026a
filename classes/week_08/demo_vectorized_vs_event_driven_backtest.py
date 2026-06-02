"""
Demonstrate vectorized vs event-driven backtesting.

Vectorized backtest:
    - Calculate signals, positions, returns, and equity using pandas columns.
    - Fast and compact.
    - Best for simple strategies that can be expressed as array operations.

Event-driven backtest:
    - Process one bar at a time.
    - Closer to how live trading systems work.
    - Easier to extend with order objects, fills, slippage, partial fills,
      position limits, and portfolio state.

Both examples trade the same moving-average crossover rule:
    - long when short moving average > long moving average
    - short when short moving average <= long moving average
    - signal is calculated at today's close
    - position is applied to the next day's return
"""

from __future__ import annotations

import numpy as np
import pandas as pd


RANDOM_SEED = 11
N_DAYS = 500
INITIAL_CAPITAL = 10000.0
SHORT_WINDOW = 10
LONG_WINDOW = 30
TRANSACTION_COST_PER_UNIT = 0.0005


def simulate_price_data() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    dates = pd.date_range("2024-01-01", periods=N_DAYS, freq="B")

    drift = 0.0002
    volatility = 0.0120
    returns = rng.normal(loc=drift, scale=volatility, size=N_DAYS)
    close = 100.0 * np.cumprod(1.0 + returns)

    return pd.DataFrame(
        {
            "date": dates,
            "close": close,
        }
    )


def run_vectorized_backtest(price_data: pd.DataFrame) -> pd.DataFrame:
    df = price_data.copy()

    df["return"] = df["close"].pct_change().fillna(0.0)
    df["short_ma"] = df["close"].rolling(SHORT_WINDOW).mean()
    df["long_ma"] = df["close"].rolling(LONG_WINDOW).mean()

    df["signal"] = 0
    df.loc[df["short_ma"] > df["long_ma"], "signal"] = 1
    df.loc[df["short_ma"] <= df["long_ma"], "signal"] = -1

    # Position at t-1 earns return at t. This avoids look-ahead bias.
    df["position"] = df["signal"].shift(1).fillna(0)

    # Cost is paid when today's close signal changes tomorrow's position.
    df["target_position"] = df["signal"]
    df["turnover"] = df["target_position"].diff().abs().fillna(df["target_position"].abs())
    df["transaction_cost"] = df["turnover"] * TRANSACTION_COST_PER_UNIT

    df["gross_strategy_return"] = df["position"] * df["return"]
    df["net_strategy_return"] = (
        (1.0 + df["gross_strategy_return"]) * (1.0 - df["transaction_cost"]) - 1.0
    )
    df["equity"] = INITIAL_CAPITAL * (1.0 + df["net_strategy_return"]).cumprod()

    return df


def run_event_driven_backtest(price_data: pd.DataFrame) -> pd.DataFrame:
    close_history = []
    rows = []

    cash_equity = INITIAL_CAPITAL
    current_position = 0
    previous_close = None

    for _, bar in price_data.iterrows():
        date = bar["date"]
        close = bar["close"]

        if previous_close is None:
            daily_return = 0.0
        else:
            daily_return = close / previous_close - 1.0

        gross_strategy_return = current_position * daily_return
        cash_equity *= 1.0 + gross_strategy_return

        close_history.append(close)
        short_ma = np.nan
        long_ma = np.nan
        target_position = 0

        if len(close_history) >= SHORT_WINDOW:
            short_ma = float(np.mean(close_history[-SHORT_WINDOW:]))
        if len(close_history) >= LONG_WINDOW:
            long_ma = float(np.mean(close_history[-LONG_WINDOW:]))
            target_position = 1 if short_ma > long_ma else -1

        turnover = abs(target_position - current_position)
        transaction_cost = turnover * TRANSACTION_COST_PER_UNIT
        cash_equity *= 1.0 - transaction_cost

        rows.append(
            {
                "date": date,
                "close": close,
                "return": daily_return,
                "short_ma": short_ma,
                "long_ma": long_ma,
                "position": current_position,
                "target_position": target_position,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
                "gross_strategy_return": gross_strategy_return,
                "net_strategy_return": (1.0 + gross_strategy_return) * (1.0 - transaction_cost) - 1.0,
                "equity": cash_equity,
            }
        )

        current_position = target_position
        previous_close = close

    return pd.DataFrame(rows)


def calculate_summary(backtest_name: str, result: pd.DataFrame) -> dict:
    net_returns = result["net_strategy_return"]
    final_equity = result["equity"].iloc[-1]
    total_return = final_equity / INITIAL_CAPITAL - 1.0
    annualized_return = (1.0 + total_return) ** (252 / len(result)) - 1.0
    annualized_volatility = net_returns.std(ddof=1) * np.sqrt(252)

    if annualized_volatility == 0:
        sharpe = 0.0
    else:
        sharpe = annualized_return / annualized_volatility

    running_peak = result["equity"].cummax()
    drawdown = result["equity"] / running_peak - 1.0

    return {
        "backtest": backtest_name,
        "final_equity": final_equity,
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe": sharpe,
        "max_drawdown": drawdown.min(),
        "trade_count": int((result["turnover"] > 0).sum()),
    }


if __name__ == "__main__":
    pd.set_option("display.float_format", "{:.6f}".format)

    prices = simulate_price_data()

    vectorized_result = run_vectorized_backtest(prices)
    event_driven_result = run_event_driven_backtest(prices)

    summary = pd.DataFrame(
        [
            calculate_summary("vectorized", vectorized_result),
            calculate_summary("event_driven", event_driven_result),
        ]
    )

    comparison = pd.DataFrame(
        {
            "date": vectorized_result["date"],
            "vectorized_equity": vectorized_result["equity"],
            "event_driven_equity": event_driven_result["equity"],
            "equity_difference": vectorized_result["equity"] - event_driven_result["equity"],
            "vectorized_position": vectorized_result["position"],
            "event_driven_position": event_driven_result["position"],
        }
    )

    print("Backtest summary")
    print("-" * 100)
    print(summary)
    print()

    print("Last 10 rows: vectorized vs event-driven")
    print("-" * 100)
    print(comparison.tail(10))
    print()

    print("Maximum absolute equity difference")
    print("-" * 100)
    print(f"{comparison['equity_difference'].abs().max():.10f}")
    print()

    print("Key lesson")
    print("-" * 100)
    print("Vectorized backtests are fast and concise.")
    print("Event-driven backtests are more verbose, but closer to live trading architecture.")
