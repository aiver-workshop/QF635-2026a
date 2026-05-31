"""
Moving average crossover strategy for Week 7.

This strategy is intentionally small and focused on trading logic. TradingEngine
owns the shared runtime services: order routing, position tracking, PnL, risk,
and dashboard publishing.

Signal logic:
    - calculate the mid price from each order book update
    - keep short and long moving average windows per symbol
    - target long when short MA is above long MA
    - target short when short MA is below long MA
    - send only the order needed to move from current position to target
"""

from __future__ import annotations

from collections import deque
import logging
import time
from typing import TYPE_CHECKING

from common.interface_book import VenueOrderBook
from common.interface_order import OrderEvent, Side
from common.interface_trade import AggTrade

if TYPE_CHECKING:
    from trading_engine import TradingEngine


class MovingAverageCrossoverStrategy:

    def __init__(
        self,
        name: str = "MovingAverageCrossoverStrategy",
        short_window: int = 10,
        long_window: int = 30,
        trade_quantity: float = 0.001,
        trade_on_first_signal: bool = True,
        log_interval_seconds: float = 1.0,
    ) -> None:
        if short_window <= 0:
            raise ValueError("short_window must be positive")
        if long_window <= short_window:
            raise ValueError("long_window must be larger than short_window")
        if trade_quantity <= 0:
            raise ValueError("trade_quantity must be positive")

        self.name: str = name
        self.short_window: int = short_window
        self.long_window: int = long_window
        self.trade_quantity: float = trade_quantity
        self.trade_on_first_signal: bool = trade_on_first_signal
        self.log_interval_seconds: float = log_interval_seconds

        self.trading_engine: TradingEngine | None = None
        self.mid_prices: dict[str, deque[float]] = {}
        self.last_signal: dict[str, int] = {}
        self.has_pending_order: dict[str, bool] = {}
        self.last_log_time: dict[str, float] = {}

    def set_trading_engine(self, trading_engine: TradingEngine) -> None:
        self.trading_engine = trading_engine

    def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
        if self.trading_engine is None:
            return

        book = venue_order_book.get_book()
        symbol = book.contract_name
        mid_price = (book.get_best_bid() + book.get_best_ask()) / 2.0

        if symbol not in self.mid_prices:
            self.mid_prices[symbol] = deque(maxlen=self.long_window)

        prices = self.mid_prices[symbol]
        prices.append(mid_price)

        if len(prices) < self.long_window:
            self.trading_engine.update_strategy_analytics(
                {
                    "symbol": symbol,
                    "window": f"{len(prices)}/{self.long_window}",
                    "mid_price": mid_price,
                    "signal": "WARMING_UP",
                }
            )
            self._log_waiting_for_window(symbol, len(prices))
            return

        short_ma = self._calculate_average(list(prices)[-self.short_window:])
        long_ma = self._calculate_average(prices)
        signal = self._get_signal(short_ma, long_ma)
        previous_signal = self.last_signal.get(symbol)
        current_position = self.trading_engine.get_position(symbol)
        target_position = signal * self.trade_quantity

        self.trading_engine.update_strategy_analytics(
            {
                "symbol": symbol,
                "mid_price": mid_price,
                "short_ma": short_ma,
                "long_ma": long_ma,
                "signal": self._format_signal(signal),
                "current_position": current_position,
                "target_position": target_position,
            }
        )

        if previous_signal is None:
            self.last_signal[symbol] = signal
            if not self.trade_on_first_signal:
                return

        if signal == 0 or signal == previous_signal:
            return

        self.last_signal[symbol] = signal
        self._trade_to_signal(symbol, signal, short_ma, long_ma, mid_price)

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

    def _trade_to_signal(
        self,
        symbol: str,
        signal: int,
        short_ma: float,
        long_ma: float,
        mid_price: float,
    ) -> None:
        if self.trading_engine is None:
            return

        if self.has_pending_order.get(symbol, False):
            logging.info("[%s] signal ignored while order is pending | %s", self.name, symbol)
            return

        target_position = signal * self.trade_quantity
        current_position = self.trading_engine.get_position(symbol)
        order_quantity = target_position - current_position

        if order_quantity == 0:
            return

        side = Side.BUY if order_quantity > 0 else Side.SELL
        quantity = abs(order_quantity)

        logging.info(
            "[%s] SIGNAL %s | %s mid=%.2f short_ma=%.2f long_ma=%.2f current_position=%.6f target_position=%.6f",
            self.name,
            "LONG" if signal > 0 else "SHORT",
            symbol,
            mid_price,
            short_ma,
            long_ma,
            current_position,
            target_position,
        )

        order_sent = self.trading_engine.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
        )
        self.has_pending_order[symbol] = order_sent

    def _log_waiting_for_window(self, symbol: str, current_size: int) -> None:
        now = time.time()
        last_log_time = self.last_log_time.get(symbol, 0.0)

        if now - last_log_time < self.log_interval_seconds:
            return

        self.last_log_time[symbol] = now
        logging.info(
            "[%s] Waiting for MA window | %s %s/%s",
            self.name,
            symbol,
            current_size,
            self.long_window,
        )

    def _get_signal(self, short_ma: float, long_ma: float) -> int:
        if short_ma > long_ma:
            return 1
        if short_ma < long_ma:
            return -1
        return 0

    def _calculate_average(self, values: deque[float] | list[float]) -> float:
        return sum(values) / len(values)

    def _format_signal(self, signal: int) -> str:
        if signal > 0:
            return "LONG"
        if signal < 0:
            return "SHORT"

        return "FLAT"
