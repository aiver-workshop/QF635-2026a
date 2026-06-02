"""
Backtest the copied BTC/ETH pair strategy with TradingEngine.

This script demonstrates the same architecture used in live trading:

    simulated market data -> SimulatedGateway -> TradingEngine -> PairTradingStrategy
    PairTradingStrategy -> TradingEngine -> SimulatorOrderManager -> SimulatedGateway

The strategy does not know whether orders are live or simulated. It only calls
TradingEngine.place_market_order(...). The order manager decides how to execute.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys

import numpy as np
import pandas as pd


CURRENT_DIR = Path(__file__).resolve().parent
MARKET_DATA_FILE = CURRENT_DIR / "data" / "btc_eth_1s_30m.csv"

sys.path.insert(0, str(CURRENT_DIR))

from simulated_gateway import SimulatedGateway
from simulator_order_manager import SimulatorOrderManager
from strategy_pair import PairTradingStrategy
from trading_engine import TradingEngine


RANDOM_SEED = 123
N_BARS = 500
INITIAL_CAPITAL = 10000.0
MAX_ORDER_NOTIONAL = 10000.0

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
BASE_QUANTITY = 0.001
HEDGE_QUANTITY = 0.035
SPREAD_WINDOW_SIZE = 60
ENTRY_Z_SCORE = 2.0
EXIT_Z_SCORE = 0.5


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.WARNING,
)


def simulate_pair_market_data() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    dates = pd.date_range("2025-01-01", periods=N_BARS, freq="h")

    btc_returns = rng.normal(loc=0.0, scale=0.0020, size=N_BARS)
    btc_log_price = np.log(70000.0) + np.cumsum(btc_returns)

    spread_center = np.log(35.0)
    spread_cycle = 0.0300 * np.sin(np.linspace(0, 12 * np.pi, N_BARS))
    spread_noise = rng.normal(loc=0.0, scale=0.0040, size=N_BARS)
    spread = spread_center + spread_cycle + spread_noise

    eth_log_price = btc_log_price - spread

    return pd.DataFrame(
        {
            "timestamp": dates,
            "BTCUSDT": np.exp(btc_log_price),
            "ETHUSDT": np.exp(eth_log_price),
            "true_spread": spread,
        }
    )


def load_downloaded_market_data() -> pd.DataFrame:
    df = pd.read_csv(MARKET_DATA_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    missing_symbols = [symbol for symbol in SYMBOLS if symbol not in df.columns]
    if missing_symbols:
        raise ValueError(f"Downloaded market data is missing columns: {missing_symbols}")

    return df[["timestamp", *SYMBOLS]].dropna().reset_index(drop=True)


def load_market_data() -> pd.DataFrame:
    if MARKET_DATA_FILE.exists():
        print(f"Loading downloaded market data: {MARKET_DATA_FILE}")
        return load_downloaded_market_data()

    print("Downloaded market data not found. Using simulated market data.")
    return simulate_pair_market_data()


def print_backtest_summary(engine: TradingEngine) -> None:
    position_manager = engine.position_manager
    risk_manager = engine.risk_manager

    positions = pd.DataFrame(position_manager.get_positions_snapshot())
    orders = pd.DataFrame(engine.get_order_history())

    print("Backtest summary")
    print("-" * 80)
    print(f"initial_capital     = {position_manager.initial_capital:.2f}")
    print(f"final_equity        = {position_manager.get_equity():.2f}")
    print(f"total_pnl           = {position_manager.get_total_pnl():.4f}")
    print(f"realized_pnl        = {position_manager.total_realized_pnl:.4f}")
    print(f"unrealized_pnl      = {position_manager.total_unrealized_pnl:.4f}")
    print(f"max_drawdown        = {risk_manager.get_max_drawdown():.4f}")
    print(f"max_drawdown_pct    = {risk_manager.get_max_drawdown_pct() * 100:.4f}%")
    print()

    print("Final positions")
    print("-" * 80)
    if positions.empty:
        print("No positions")
    else:
        print(positions)
    print()

    print("Order history")
    print("-" * 80)
    if orders.empty:
        print("No orders")
    else:
        columns = [
            "symbol",
            "side",
            "status",
            "order_type",
            "average_filled_price",
            "filled_quantity",
            "order_id",
        ]
        print(orders[columns].tail(20))
    print()

    print("Latest strategy analytics")
    print("-" * 80)
    print(engine.strategy_analytics)


def get_pnl_and_risk_snapshot(engine: TradingEngine) -> dict:
    position_manager = engine.position_manager
    risk_manager = engine.risk_manager

    return {
        "initial_capital": position_manager.initial_capital,
        "final_equity": position_manager.get_equity(),
        "total_pnl": position_manager.get_total_pnl(),
        "realized_pnl": position_manager.total_realized_pnl,
        "unrealized_pnl": position_manager.total_unrealized_pnl,
        "current_drawdown": risk_manager.get_current_drawdown(),
        "current_drawdown_pct": risk_manager.get_current_drawdown_pct(),
        "max_drawdown": risk_manager.get_max_drawdown(),
        "max_drawdown_pct": risk_manager.get_max_drawdown_pct(),
        "peak_equity": risk_manager.get_peak_equity(),
        "latest_equity": risk_manager.get_latest_equity(),
    }


def print_pnl_and_risk_snapshot(engine: TradingEngine) -> None:
    snapshot = get_pnl_and_risk_snapshot(engine)

    print("Final PnL and risk")
    print("-" * 80)
    print(f"initial_capital      = {snapshot['initial_capital']:.2f}")
    print(f"final_equity         = {snapshot['final_equity']:.2f}")
    print(f"peak_equity          = {snapshot['peak_equity']:.2f}")
    print(f"latest_equity        = {snapshot['latest_equity']:.2f}")
    print(f"total_pnl            = {snapshot['total_pnl']:.4f}")
    print(f"realized_pnl         = {snapshot['realized_pnl']:.4f}")
    print(f"unrealized_pnl       = {snapshot['unrealized_pnl']:.4f}")
    print(f"current_drawdown     = {snapshot['current_drawdown']:.4f}")
    print(f"current_drawdown_pct = {snapshot['current_drawdown_pct'] * 100:.4f}%")
    print(f"max_drawdown         = {snapshot['max_drawdown']:.4f}")
    print(f"max_drawdown_pct     = {snapshot['max_drawdown_pct'] * 100:.4f}%")
    print()


if __name__ == "__main__":
    market_data = load_market_data()

    gateway = SimulatedGateway(
        market_data=market_data,
        symbols=SYMBOLS,
        spread_bps=2.0,
    )
    order_manager = SimulatorOrderManager(
        gateway=gateway,
        max_order_notional=MAX_ORDER_NOTIONAL,
    )
    strategy = PairTradingStrategy(
        base_symbol="BTCUSDT",
        hedge_symbol="ETHUSDT",
        base_quantity=BASE_QUANTITY,
        hedge_quantity=HEDGE_QUANTITY,
        spread_window_size=SPREAD_WINDOW_SIZE,
        entry_z_score=ENTRY_Z_SCORE,
        exit_z_score=EXIT_Z_SCORE,
        sample_interval_seconds=0.0,
        log_interval_seconds=0.0,
    )
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        order_manager=order_manager,
        initial_capital=INITIAL_CAPITAL,
        dashboard_file=CURRENT_DIR / "state" / "backtest_dashboard_state.json",
        kill_switch_file=CURRENT_DIR / "state" / "backtest_kill_switch_state.json",
        exit_program_file=CURRENT_DIR / "state" / "backtest_exit_program_state.json",
    )

    engine.register_callbacks()
    gateway.run_backtest()

    print_pnl_and_risk_snapshot(engine)
    print_backtest_summary(engine)
