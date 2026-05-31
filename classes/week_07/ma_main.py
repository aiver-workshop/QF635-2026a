"""
Week 7 moving average crossover strategy main file.

This file creates the live gateway, live order manager, moving average strategy,
and trading engine. TradingEngine owns callbacks, order routing, position/PnL,
risk, and dashboard publishing.
"""

import logging
import time

from gateway import BinanceFutureGateway
from ma_strategy import MovingAverageCrossoverStrategy
from order_manager import LiveOrderManager
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
    SHORT_WINDOW = 10
    LONG_WINDOW = 30
    TRADE_QUANTITY = 0.1
    MAX_ORDER_NOTIONAL = 50000.0

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
    strategy = MovingAverageCrossoverStrategy(
        short_window=SHORT_WINDOW,
        long_window=LONG_WINDOW,
        trade_quantity=TRADE_QUANTITY,
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
