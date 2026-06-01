"""
Week 7 BTC/ETH pair trading strategy main file.

This file creates the live gateway, live order manager, pair trading strategy,
and trading engine. TradingEngine owns callbacks, order routing, position/PnL,
risk, dashboard publishing, stop/start trading, and the kill switch.
"""

import logging
import time

from gateway import BinanceFutureGateway
from order_manager import LiveOrderManager
from strategy_pair import PairTradingStrategy
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

    SYMBOLS = ["BTCUSDT", "ETHUSDT"]
    MAX_ORDER_NOTIONAL = 10000.0

    BASE_QUANTITY = 0.001
    HEDGE_QUANTITY = 0.01
    SPREAD_WINDOW_SIZE = 120
    ENTRY_Z_SCORE = 2.0
    EXIT_Z_SCORE = 0.5

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
    strategy = PairTradingStrategy(
        base_symbol="BTCUSDT",
        hedge_symbol="ETHUSDT",
        base_quantity=BASE_QUANTITY,
        hedge_quantity=HEDGE_QUANTITY,
        spread_window_size=SPREAD_WINDOW_SIZE,
        entry_z_score=ENTRY_Z_SCORE,
        exit_z_score=EXIT_Z_SCORE,
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
