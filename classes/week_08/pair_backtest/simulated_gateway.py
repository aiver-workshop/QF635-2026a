"""
Simulated gateway for event-driven backtesting.

This class exposes the same callback shape that TradingEngine expects from the
live Binance gateway:
    - register_orderbook_callback(...)
    - register_agg_trade_callback(...)
    - register_execution_callback(...)
    - get_order_book(symbol)
    - place_market_order(...)

Market data is replayed from a simulated price table. Market orders are filled
immediately against the current simulated top of book.
"""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from common.interface_book import OrderBook, PriceLevel, VenueOrderBook
from common.interface_order import ExecutionType, OrderEvent, OrderStatus, Side
from common.interface_trade import AggTrade


class SimulatedGateway:

    def __init__(
        self,
        market_data: pd.DataFrame,
        symbols: list[str],
        exchange_name: str = "SIM",
        spread_bps: float = 2.0,
    ) -> None:
        self.market_data: pd.DataFrame = market_data
        self.symbols: list[str] = [symbol.upper() for symbol in symbols]
        self.exchange_name: str = exchange_name
        self.spread_bps: float = spread_bps

        self.orderbook_callbacks = []
        self.agg_trade_callbacks = []
        self.execution_callbacks = []

        self.order_books: dict[str, OrderBook] = {}
        self.current_bar_index: int = -1
        self.current_time = None
        self.next_order_id: int = 1

    def register_orderbook_callback(self, callback) -> None:
        self.orderbook_callbacks.append(callback)

    def register_agg_trade_callback(self, callback) -> None:
        self.agg_trade_callbacks.append(callback)

    def register_execution_callback(self, callback) -> None:
        self.execution_callbacks.append(callback)

    def connect(self) -> None:
        self.run_backtest()

    def run_backtest(self) -> None:
        logging.info("[SimulatedGateway] starting replay | bars=%s", len(self.market_data))

        for bar_index, row in self.market_data.iterrows():
            self.current_bar_index += 1
            self.current_time = row.get("timestamp", bar_index)

            for symbol in self.symbols:
                mid_price = float(row[symbol])
                book = self._build_order_book(
                    symbol=symbol,
                    mid_price=mid_price,
                    timestamp=float(self.current_bar_index),
                )
                self.order_books[symbol] = book
                venue_order_book = VenueOrderBook(self.exchange_name, book)

                for callback in self.orderbook_callbacks:
                    callback(venue_order_book)

                trade = AggTrade(
                    contract_name=symbol,
                    price=mid_price,
                    size=1.0,
                    is_buyer_maker=False,
                )
                for callback in self.agg_trade_callbacks:
                    callback(trade)

        logging.info("[SimulatedGateway] replay finished")

    def get_order_book(self, symbol: str) -> OrderBook:
        symbol = symbol.upper()
        if symbol not in self.order_books:
            raise KeyError(f"No order book available for {symbol}")

        return self.order_books[symbol]

    def place_market_order(self, symbol: str, side: Side, quantity: float) -> bool:
        symbol = symbol.upper()
        book = self.get_order_book(symbol)

        if side == Side.BUY:
            fill_price = book.get_best_ask()
        else:
            fill_price = book.get_best_bid()

        order_id = self._next_order_id()
        self._emit_order_event(
            symbol=symbol,
            order_id=order_id,
            side=side,
            price=0.0,
            quantity=0.0,
            execution_type=ExecutionType.NEW,
            status=OrderStatus.NEW,
            order_type="MARKET",
        )
        self._emit_order_event(
            symbol=symbol,
            order_id=order_id,
            side=side,
            price=fill_price,
            quantity=quantity,
            execution_type=ExecutionType.TRADE,
            status=OrderStatus.FILLED,
            order_type="MARKET",
        )
        return True

    def place_limit_order(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        post_only: bool = True,
    ) -> bool:
        symbol = symbol.upper()
        book = self.get_order_book(symbol)

        if post_only:
            logging.warning("[SimulatedGateway] post-only resting limit orders are not simulated")
            return False

        is_marketable = (
            side == Side.BUY and price >= book.get_best_ask()
        ) or (
            side == Side.SELL and price <= book.get_best_bid()
        )
        if not is_marketable:
            logging.warning("[SimulatedGateway] non-marketable limit orders are not simulated")
            return False

        return self.place_market_order(symbol=symbol, side=side, quantity=quantity)

    def _build_order_book(self, symbol: str, mid_price: float, timestamp: float) -> OrderBook:
        half_spread = mid_price * self.spread_bps / 10000.0 / 2.0
        bid = mid_price - half_spread
        ask = mid_price + half_spread

        return OrderBook(
            timestamp=timestamp,
            contract_name=symbol,
            bids=[PriceLevel(price=bid, size=100.0)],
            asks=[PriceLevel(price=ask, size=100.0)],
        )

    def _emit_order_event(
        self,
        symbol: str,
        order_id: str,
        side: Side,
        price: float,
        quantity: float,
        execution_type: ExecutionType,
        status: OrderStatus,
        order_type: str,
    ) -> None:
        order_event = OrderEvent(
            contract_name=symbol,
            order_id=order_id,
            execution_type=execution_type,
            status=status,
            client_id=order_id,
        )
        order_event.side = side
        order_event.last_filled_time = datetime.now()
        order_event.last_filled_price = price
        order_event.last_filled_quantity = quantity
        order_event.order_type = order_type

        for callback in self.execution_callbacks:
            callback(order_event)

    def _next_order_id(self) -> str:
        order_id = f"sim_{self.next_order_id:06d}"
        self.next_order_id += 1
        return order_id
