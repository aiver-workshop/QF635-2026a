"""
BTC/ETH pair trading strategy for Week 7.

TradingEngine owns the shared runtime services: order routing, position/PnL,
risk, dashboard publishing, and kill-switch checks. This strategy owns only the
pair signal:
    - build a rolling log-price spread between BTCUSDT and ETHUSDT
    - enter long spread when z-score is low
    - enter short spread when z-score is high
    - exit when z-score mean-reverts
"""

from __future__ import annotations

from collections import deque
import logging
import math
import time
from typing import TYPE_CHECKING

from common.interface_book import OrderBook, VenueOrderBook
from common.interface_order import OrderEvent, Side
from common.interface_trade import AggTrade

if TYPE_CHECKING:
    from trading_engine import TradingEngine


class PairTradingStrategy:

    def __init__(
        self,
        base_symbol: str = "BTCUSDT",
        hedge_symbol: str = "ETHUSDT",
        name: str = "PairTradingStrategy",
        hedge_ratio: float = 1.0,
        spread_window_size: int = 120,
        entry_z_score: float = 2.0,
        exit_z_score: float = 0.5,
        base_quantity: float = 0.001,
        hedge_quantity: float = 0.01,
        sample_interval_seconds: float = 1.0,
        log_interval_seconds: float = 1.0,
    ) -> None:
        if spread_window_size <= 1:
            raise ValueError("spread_window_size must be larger than 1")
        if entry_z_score <= exit_z_score:
            raise ValueError("entry_z_score must be larger than exit_z_score")
        if base_quantity <= 0:
            raise ValueError("base_quantity must be positive")
        if hedge_quantity <= 0:
            raise ValueError("hedge_quantity must be positive")

        self.name: str = name
        self.base_symbol: str = base_symbol.upper()
        self.hedge_symbol: str = hedge_symbol.upper()
        self.hedge_ratio: float = hedge_ratio
        self.entry_z_score: float = entry_z_score
        self.exit_z_score: float = exit_z_score
        self.base_quantity: float = base_quantity
        self.hedge_quantity: float = hedge_quantity
        self.sample_interval_seconds: float = sample_interval_seconds
        self.log_interval_seconds: float = log_interval_seconds

        self.trading_engine: TradingEngine | None = None
        self.last_book: dict[str, OrderBook] = {}
        self.spread_window: deque[float] = deque(maxlen=spread_window_size)
        self.last_sample_time: float = 0.0
        self.last_log_time: float = 0.0
        self.last_window_log_time: float = 0.0
        self.has_pending_order: dict[str, bool] = {}

        # -1 = short spread, 0 = flat, 1 = long spread
        self.pair_state: int = 0

    def set_trading_engine(self, trading_engine: TradingEngine) -> None:
        self.trading_engine = trading_engine

    def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
        if self.trading_engine is None:
            return

        book = venue_order_book.get_book()
        symbol = book.contract_name
        self.last_book[symbol] = book

        self.evaluate_pair()

    def on_agg_trade(self, trade: AggTrade) -> None:
        pass

    def on_execution(self, order_event: OrderEvent) -> None:
        terminal_status_names = {
            "FILLED",
            "CANCELED",
            "FAILED",
            "EXPIRED",
            "EXPIRED_IN_MATCH",
        }

        if order_event.status.name in terminal_status_names:
            self.has_pending_order[order_event.contract_name] = False

    def evaluate_pair(self) -> None:
        if self.trading_engine is None:
            return

        if self._has_pending_orders():
            return

        if self.base_symbol not in self.last_book:
            return

        if self.hedge_symbol not in self.last_book:
            return

        now = time.time()
        if now - self.last_sample_time < self.sample_interval_seconds:
            return
        self.last_sample_time = now

        base_mid = self._get_mid_price(self.last_book[self.base_symbol])
        hedge_mid = self._get_mid_price(self.last_book[self.hedge_symbol])

        spread = math.log(base_mid) - self.hedge_ratio * math.log(hedge_mid)
        self.spread_window.append(spread)

        if len(self.spread_window) < self.spread_window.maxlen:
            self._publish_analytics(
                base_mid=base_mid,
                hedge_mid=hedge_mid,
                spread=spread,
                z_score=None,
                signal="WARMING_UP",
            )
            self._log_window_warmup()
            return

        z_score = self._calculate_z_score(spread)
        if z_score is None:
            return

        signal = self._get_signal(z_score)
        self._publish_analytics(
            base_mid=base_mid,
            hedge_mid=hedge_mid,
            spread=spread,
            z_score=z_score,
            signal=signal,
        )
        self._log_pair_state(base_mid, hedge_mid, spread, z_score)
        self._trade_signal(signal, z_score)

    def _trade_signal(self, signal: str, z_score: float) -> None:
        if signal == "LONG_SPREAD" and self.pair_state == 0:
            logging.info(
                "[%s] SIGNAL long spread z=%.2f | BUY %s, SELL %s",
                self.name,
                z_score,
                self.base_symbol,
                self.hedge_symbol,
            )
            self._trade_to_pair_state(1)

        elif signal == "SHORT_SPREAD" and self.pair_state == 0:
            logging.info(
                "[%s] SIGNAL short spread z=%.2f | SELL %s, BUY %s",
                self.name,
                z_score,
                self.base_symbol,
                self.hedge_symbol,
            )
            self._trade_to_pair_state(-1)

        elif signal == "EXIT" and self.pair_state != 0:
            logging.info("[%s] SIGNAL exit pair z=%.2f", self.name, z_score)
            self._trade_to_pair_state(0)

    def _trade_to_pair_state(self, target_pair_state: int) -> None:
        if self.trading_engine is None:
            return

        target_base_position = target_pair_state * self.base_quantity
        target_hedge_position = -target_pair_state * self.hedge_quantity

        base_sent = self._trade_symbol_to_target(
            symbol=self.base_symbol,
            target_position=target_base_position,
        )
        hedge_sent = self._trade_symbol_to_target(
            symbol=self.hedge_symbol,
            target_position=target_hedge_position,
        )

        if base_sent and hedge_sent:
            self.pair_state = target_pair_state
            logging.info("[%s] Pair target state updated to %s", self.name, self.pair_state)
        else:
            logging.warning(
                "[%s] Pair target state not updated because one or more legs were not sent",
                self.name,
            )

    def _trade_symbol_to_target(self, symbol: str, target_position: float) -> bool:
        if self.trading_engine is None:
            return False

        current_position = self.trading_engine.get_position(symbol)
        order_quantity = target_position - current_position

        if abs(order_quantity) < 0.00000001:
            return True

        side = Side.BUY if order_quantity > 0 else Side.SELL
        quantity = abs(order_quantity)

        order_sent = self.trading_engine.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
        )
        self.has_pending_order[symbol] = order_sent

        return order_sent

    def _calculate_z_score(self, spread: float) -> float | None:
        mean = sum(self.spread_window) / len(self.spread_window)
        variance = sum((value - mean) ** 2 for value in self.spread_window) / len(self.spread_window)
        standard_deviation = math.sqrt(variance)

        if standard_deviation == 0:
            return None

        return (spread - mean) / standard_deviation

    def _get_signal(self, z_score: float) -> str:
        if self.pair_state == 0:
            if z_score <= -self.entry_z_score:
                return "LONG_SPREAD"
            if z_score >= self.entry_z_score:
                return "SHORT_SPREAD"

        if self.pair_state == 1 and z_score >= -self.exit_z_score:
            return "EXIT"

        if self.pair_state == -1 and z_score <= self.exit_z_score:
            return "EXIT"

        return "HOLD"

    def _get_mid_price(self, book: OrderBook) -> float:
        return (book.get_best_bid() + book.get_best_ask()) / 2.0

    def _has_pending_orders(self) -> bool:
        return any(self.has_pending_order.values())

    def _log_window_warmup(self) -> None:
        now = time.time()
        if now - self.last_window_log_time < self.log_interval_seconds:
            return

        self.last_window_log_time = now
        logging.info(
            "[%s] Waiting for spread window %s/%s",
            self.name,
            len(self.spread_window),
            self.spread_window.maxlen,
        )

    def _log_pair_state(
        self,
        base_mid: float,
        hedge_mid: float,
        spread: float,
        z_score: float,
    ) -> None:
        now = time.time()
        if now - self.last_log_time < self.log_interval_seconds:
            return

        self.last_log_time = now
        logging.info(
            "[%s] PAIR %s/%s | base_mid=%.2f hedge_mid=%.2f spread=%.6f z=%.2f state=%s",
            self.name,
            self.base_symbol,
            self.hedge_symbol,
            base_mid,
            hedge_mid,
            spread,
            z_score,
            self.pair_state,
        )

    def _publish_analytics(
        self,
        base_mid: float,
        hedge_mid: float,
        spread: float,
        z_score: float | None,
        signal: str,
    ) -> None:
        if self.trading_engine is None:
            return

        analytics = {
            "strategy": self.name,
            "pair": f"{self.base_symbol}/{self.hedge_symbol}",
            "base_mid": base_mid,
            "hedge_mid": hedge_mid,
            "spread": spread,
            "signal": signal,
            "pair_state": self.pair_state,
            "window": f"{len(self.spread_window)}/{self.spread_window.maxlen}",
        }

        if z_score is not None:
            analytics["z_score"] = z_score

        self.trading_engine.update_strategy_analytics(analytics)
