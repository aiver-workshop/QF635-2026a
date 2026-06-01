"""
Simple callback-driven strategy for Week 7.

This strategy demonstrates how a trading strategy connects to the gateway by
receiving callback methods from TradingEngine:
    - on_orderbook(...) receives market data.
    - on_agg_trade(...) receives public trade flow.
    - on_execution(...) receives private order events.

The strategy does not own exchange connectivity. BinanceFutureGateway owns the
REST and websocket connections. TradingEngine owns common runtime logic such as
position, PnL, risk, dashboard updates, and order routing. If the strategy
needs to trade, it asks TradingEngine to place orders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.interface_book import VenueOrderBook
from common.interface_order import OrderEvent
from common.interface_trade import AggTrade

if TYPE_CHECKING:
    from trading_engine import TradingEngine


class SimpleStrategy:

    def __init__(
        self,
        name: str = "SimpleStrategy",
    ) -> None:
        self.name: str = name
        self.trading_engine: TradingEngine | None = None

    def set_trading_engine(self, trading_engine: TradingEngine) -> None:
        self.trading_engine = trading_engine

    def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
        pass

    def on_agg_trade(self, trade: AggTrade) -> None:
        pass

    def on_execution(self, order_event: OrderEvent) -> None:
        pass
