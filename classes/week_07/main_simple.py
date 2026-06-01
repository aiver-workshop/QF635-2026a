"""
Week 7 trading engine demo main file.

This file creates the live gateway, live order manager, strategy, and trading
engine. The engine wires callbacks between the gateway and strategy, and gives
the strategy an engine API for sending orders. The engine also owns shared
runtime services such as position, PnL, risk, and dashboard publishing.
"""

import logging
import time

from gateway import BinanceFutureGateway
from order_manager import LiveOrderManager
from strategy_simple import SimpleStrategy
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
    MAX_ORDER_NOTIONAL = 10000.0

    SYMBOLS = ["BTCUSDT"]

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
    strategy = SimpleStrategy()
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        order_manager=order_manager,
        initial_capital=INITIAL_CAPITAL,
    )

    engine.start()

    while True:
        time.sleep(1)
