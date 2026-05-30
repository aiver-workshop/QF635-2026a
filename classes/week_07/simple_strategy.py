"""
Simple callback-driven strategy for Week 7.

This strategy demonstrates how a trading strategy connects to the gateway by
registering callback methods:
    - on_orderbook(...) receives market data and marks positions to market.
    - on_agg_trade(...) receives public trade flow and updates net volume.
    - on_execution(...) receives private fills and updates positions/PnL.

The strategy does not own exchange connectivity. BinanceFutureGateway owns the
REST and websocket connections, then calls these methods whenever events arrive.

PositionManager tracks positions, average entry price, realized PnL,
unrealized PnL, and equity. RiskManager consumes portfolio equity updates after
both fills and mark-to-market updates, then tracks drawdown.
"""

import logging
from pathlib import Path

from common.interface_book import VenueOrderBook
from common.interface_order import ExecutionType, OrderEvent
from common.interface_trade import AggTrade
from dashboard_store import DashboardStore
from position_manager import PositionManager
from risk_manager import RiskManager


class SimpleStrategy:

    def __init__(
        self,
        name: str = "SimpleStrategy",
        initial_capital: float = 10000.0,
        dashboard_file: str | Path = None,
    ):
        self.name = name
        self.last_book = {}
        self.net_volume = {}
        self.position_manager = PositionManager(initial_capital=initial_capital)
        self.risk_manager = RiskManager()
        self.dashboard_store = DashboardStore(
            dashboard_file or Path(__file__).with_name("dashboard_state.json")
        )

        # initial risk
        self.update_risk()

    def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
        book = venue_order_book.get_book()
        symbol = book.contract_name

        self.last_book[symbol] = book

        best_bid = book.get_best_bid()
        best_ask = book.get_best_ask()
        position = self.position_manager.get_position(symbol)

        if position == 0:
            return

        if position > 0:
            mtm_price = best_bid
        else:
            mtm_price = best_ask

        unrealized_pnl = self.position_manager.mark_to_market(symbol, mtm_price)

        pnl = self.position_manager.get_total_pnl()
        equity = self.update_risk()

        self.log_mark_to_market(symbol, mtm_price, unrealized_pnl, pnl, equity)

    def on_agg_trade(self, trade: AggTrade) -> None:
        symbol = trade.contract_name

        if symbol not in self.net_volume:
            self.net_volume[symbol] = 0.0

        if trade.is_buy():
            self.net_volume[symbol] += trade.size
        else:
            self.net_volume[symbol] -= trade.size

    def on_execution(self, order_event: OrderEvent) -> None:
        symbol = order_event.contract_name
        logging.info("[%s] on_execution | %s", self.name, order_event)

        if order_event.execution_type != ExecutionType.TRADE:
            return

        self.position_manager.on_fill(
            symbol=symbol,
            side=order_event.side,
            price=order_event.last_filled_price,
            quantity=order_event.last_filled_quantity,
        )
        equity = self.update_risk()

        if self.position_manager.get_position(symbol) == 0:
            unrealized_pnl = self.position_manager.mark_to_market(
                symbol=symbol,
                mark_price=order_event.last_filled_price,
            )
            equity = self.update_risk()

            self.log_mark_to_market(
                symbol=symbol,
                mtm_price=order_event.last_filled_price,
                unrealized_pnl=unrealized_pnl,
                pnl=self.position_manager.get_total_pnl(),
                equity=equity,
            )

    def log_mark_to_market(
        self,
        symbol: str,
        mtm_price: float,
        unrealized_pnl: float,
        pnl: float,
        equity: float,
    ) -> None:
        logging.info(
            "[%s] mark_to_market | %s position=%.4f avg_entry=%.2f mtm=%.2f unrealized=%.4f realized=%.4f "
            "pnl=%.4f equity=%.4f max_drawdown=%.4f max_drawdown_pct=%.2f%%",
            self.name,
            symbol,
            self.position_manager.get_position(symbol),
            self.position_manager.get_average_entry_price(symbol),
            mtm_price,
            unrealized_pnl,
            self.position_manager.get_realized_pnl(symbol),
            pnl,
            equity,
            self.risk_manager.get_max_drawdown(),
            self.risk_manager.get_max_drawdown_pct() * 100,
        )

    def update_risk(self) -> float:
        equity = self.position_manager.get_equity()
        self.risk_manager.on_equity_update(equity)
        self.publish_dashboard_state()
        return equity

    def publish_dashboard_state(self) -> None:
        summary = {
            "initial_capital": self.position_manager.initial_capital,
            "equity": self.position_manager.get_equity(),
            "total_pnl": self.position_manager.get_total_pnl(),
            "realized_pnl": self.position_manager.total_realized_pnl,
            "unrealized_pnl": self.position_manager.total_unrealized_pnl,
            "current_drawdown": self.risk_manager.get_current_drawdown(),
            "current_drawdown_pct": self.risk_manager.get_current_drawdown_pct(),
            "max_drawdown": self.risk_manager.get_max_drawdown(),
            "max_drawdown_pct": self.risk_manager.get_max_drawdown_pct(),
        }

        self.dashboard_store.publish(
            summary=summary,
            positions=self.position_manager.get_positions_snapshot(),
        )
