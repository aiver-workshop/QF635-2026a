"""
Week 7 twenty-signal technical strategy main file.

This file creates the live gateway, live order manager, technical strategy, and
trading engine. TradingEngine owns callbacks, order routing, position/PnL, risk,
dashboard publishing, stop/start trading, and the kill switch.
"""

import logging
import os
import time

from gateway import BinanceFutureGateway
from order_manager import LiveOrderManager
from strategy_technical20 import TwentySignalTechnicalStrategy
from trading_engine import TradingEngine


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


if __name__ == "__main__":
    API_KEY = "CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz"
    API_SECRET = "cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC"
    USE_TESTNET = True
    INITIAL_CAPITAL = 10000.0

    SYMBOLS = ["BTCUSDT"]
    TRADE_QUANTITY = 0.001
    MAX_ORDER_NOTIONAL = 10000.0

    HISTORY_SIZE = 240
    ENTRY_SCORE = 5
    EXIT_SCORE = 2
    MIN_TRADE_INTERVAL_SECONDS = 5.0
    SIGNAL_WINDOW_SIZE = 20

    gateway = BinanceFutureGateway(
        symbols=SYMBOLS,
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=USE_TESTNET,
        subscribe_execution=True,
    )

    order_manager = LiveOrderManager(
        gateway=gateway,
        max_order_notional=MAX_ORDER_NOTIONAL,
    )
    strategy = TwentySignalTechnicalStrategy(
        history_size=HISTORY_SIZE,
        signal_window_size=SIGNAL_WINDOW_SIZE,
        trade_quantity=TRADE_QUANTITY,
        entry_score=ENTRY_SCORE,
        exit_score=EXIT_SCORE,
        min_trade_interval_seconds=MIN_TRADE_INTERVAL_SECONDS,
    )
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        order_manager=order_manager,
        initial_capital=INITIAL_CAPITAL,
    )

    engine.start()

    while True:
        time.sleep(1)
