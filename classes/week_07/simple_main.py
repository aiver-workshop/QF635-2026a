"""
Week 7 callback demo main file.

This file connects the gateway to a simple strategy by registering strategy
methods as callbacks.
"""

import logging
import time

from gateway import BinanceFutureGateway
from simple_strategy import SimpleStrategy


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

    gateway = BinanceFutureGateway(
        symbols=SYMBOLS,
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=USE_TESTNET,
        subscribe_execution=True,
    )

    strategy = SimpleStrategy(initial_capital=INITIAL_CAPITAL)

    gateway.register_orderbook_callback(strategy.on_orderbook)
    gateway.register_agg_trade_callback(strategy.on_agg_trade)
    gateway.register_execution_callback(strategy.on_execution)

    gateway.connect()

    while True:
        time.sleep(1)
