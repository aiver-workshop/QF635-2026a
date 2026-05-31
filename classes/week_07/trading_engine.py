"""
Trading engine for Week 7.

The engine connects the gateway, order manager, and strategy:
    - gateway publishes market/execution events to the engine
    - engine updates position, PnL, risk, and dashboard state
    - engine forwards callbacks to the strategy
    - strategy can read shared portfolio/risk state from the engine
    - strategy asks the engine to send orders
    - engine routes orders to the active order manager

This keeps strategy logic decoupled from live exchange connectivity.
"""

from __future__ import annotations

import logging
from datetime import datetime
import json
import os
from pathlib import Path
from threading import Thread
import time
from typing import TYPE_CHECKING, Protocol

from common.interface_book import OrderBook, VenueOrderBook
from common.interface_order import ExecutionType, OrderEvent, Side
from common.interface_trade import AggTrade
from dashboard_store import DashboardStore
from position_manager import PositionManager
from risk_manager import RiskManager

if TYPE_CHECKING:
    from gateway import BinanceFutureGateway
    from order_manager import OrderManager


class Strategy(Protocol):

    def set_trading_engine(self, trading_engine: TradingEngine) -> None:
        ...

    def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
        ...

    def on_agg_trade(self, trade: AggTrade) -> None:
        ...

    def on_execution(self, order_event: OrderEvent) -> None:
        ...


class TradingEngine:

    def __init__(
        self,
        gateway: BinanceFutureGateway,
        strategy: Strategy,
        order_manager: OrderManager,
        initial_capital: float = 0.0,
        dashboard_file: str | Path | None = None,
        kill_switch_file: str | Path | None = None,
        exit_program_file: str | Path | None = None,
    ) -> None:
        self.gateway: BinanceFutureGateway = gateway
        self.strategy: Strategy = strategy
        self.order_manager: OrderManager = order_manager
        self.position_manager: PositionManager = PositionManager(
            initial_capital=initial_capital
        )
        self.risk_manager: RiskManager = RiskManager()
        self.dashboard_store: DashboardStore = DashboardStore(
            dashboard_file or Path(__file__).with_name("dashboard_state.json")
        )
        self.kill_switch_file: Path = Path(
            kill_switch_file or Path(__file__).with_name("kill_switch_state.json")
        )
        self.exit_program_file: Path = Path(
            exit_program_file or Path(__file__).with_name("exit_program_state.json")
        )
        self.last_book: dict[str, OrderBook] = {}
        self.order_history: list[dict] = []
        self.order_history_by_id: dict[str, dict] = {}
        self.strategy_analytics: dict = {}
        self.local_order_id: int = 0
        self._callbacks_registered: bool = False
        self._exit_monitor_started: bool = False

        if hasattr(self.strategy, "set_trading_engine"):
            self.strategy.set_trading_engine(self)

        self.update_risk()

    def start(self) -> None:
        self.register_callbacks()
        self.start_exit_monitor()
        logging.info("Starting trading engine")
        self.gateway.connect()

    def start_exit_monitor(self) -> None:
        if self._exit_monitor_started:
            return

        Thread(
            target=self._monitor_exit_program_forever,
            daemon=True,
            name="engine-exit",
        ).start()
        self._exit_monitor_started = True

    def _monitor_exit_program_forever(self) -> None:
        while True:
            if self.is_exit_program_requested():
                logging.critical("Exit program requested from dashboard. Terminating strategy process.")
                os._exit(0)

            time.sleep(1)

    def register_callbacks(self) -> None:
        if self._callbacks_registered:
            return

        self.gateway.register_orderbook_callback(self.on_orderbook)
        self.gateway.register_agg_trade_callback(self.on_agg_trade)
        self.gateway.register_execution_callback(self.on_execution)

        self._callbacks_registered = True

    def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
        book = venue_order_book.get_book()
        symbol = book.contract_name
        self.last_book[symbol] = book

        self.mark_to_market_from_orderbook(book)
        self.strategy.on_orderbook(venue_order_book)

    def on_agg_trade(self, trade: AggTrade) -> None:
        self.strategy.on_agg_trade(trade)

    def on_execution(self, order_event: OrderEvent) -> None:
        logging.info("[TradingEngine] on_execution | %s", order_event)
        self.record_order_event(order_event)

        if order_event.execution_type == ExecutionType.TRADE:
            self.position_manager.on_fill(
                symbol=order_event.contract_name,
                side=order_event.side,
                price=order_event.last_filled_price,
                quantity=order_event.last_filled_quantity,
            )
            self.update_risk()

            if self.position_manager.get_position(order_event.contract_name) == 0:
                self.mark_to_market_at_price(
                    symbol=order_event.contract_name,
                    mtm_price=order_event.last_filled_price,
                )

        self.publish_dashboard_state()
        self.strategy.on_execution(order_event)

    def record_order_event(self, order_event: OrderEvent) -> None:
        order_id = order_event.order_id
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if order_id not in self.order_history_by_id:
            self.order_history_by_id[order_id] = {
                "created_time": now,
                "updated_time": now,
                "symbol": order_event.contract_name,
                "order_id": order_id,
                "client_id": order_event.client_id or "-",
                "side": "-",
                "status": order_event.status.name,
                "order_type": getattr(order_event, "order_type", "-") or "-",
                "execution_type": order_event.execution_type.name,
                "average_filled_price": 0.0,
                "filled_quantity": 0.0,
                "last_filled_price": 0.0,
                "last_filled_quantity": 0.0,
                "canceled_reason": "-",
            }
            self.order_history.append(self.order_history_by_id[order_id])

        order_row = self.order_history_by_id[order_id]
        order_row["updated_time"] = now
        order_row["symbol"] = order_event.contract_name
        order_row["client_id"] = order_event.client_id or order_row["client_id"]
        order_row["side"] = order_event.side.name if order_event.side is not None else order_row["side"]
        order_row["status"] = order_event.status.name
        order_row["order_type"] = getattr(order_event, "order_type", None) or order_row["order_type"]
        order_row["execution_type"] = order_event.execution_type.name
        order_row["canceled_reason"] = order_event.canceled_reason or "-"

        if order_event.execution_type == ExecutionType.TRADE:
            fill_price = order_event.last_filled_price
            fill_quantity = order_event.last_filled_quantity
            current_quantity = order_row["filled_quantity"]
            current_average_price = order_row["average_filled_price"]
            new_quantity = current_quantity + fill_quantity

            if new_quantity > 0:
                order_row["average_filled_price"] = (
                    current_average_price * current_quantity + fill_price * fill_quantity
                ) / new_quantity

            order_row["filled_quantity"] = new_quantity
            order_row["last_filled_price"] = fill_price
            order_row["last_filled_quantity"] = fill_quantity

        self.trim_order_history()

    def trim_order_history(self) -> None:
        if len(self.order_history) <= 100:
            return

        removed_orders = self.order_history[:-100]
        self.order_history = self.order_history[-100:]

        for removed_order in removed_orders:
            self.order_history_by_id.pop(removed_order["order_id"], None)

    def mark_to_market_from_orderbook(self, book: OrderBook) -> None:
        symbol = book.contract_name
        position = self.position_manager.get_position(symbol)

        if position == 0:
            return

        if position > 0:
            mtm_price = book.get_best_bid()
        else:
            mtm_price = book.get_best_ask()

        self.mark_to_market_at_price(symbol, mtm_price)

    def mark_to_market_at_price(self, symbol: str, mtm_price: float) -> None:
        unrealized_pnl = self.position_manager.mark_to_market(symbol, mtm_price)
        pnl = self.position_manager.get_total_pnl()
        equity = self.update_risk()

        self.log_mark_to_market(symbol, mtm_price, unrealized_pnl, pnl, equity)

    def place_limit_order(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        post_only: bool = True,
    ) -> bool:
        if self.is_kill_switch_active():
            self.record_rejected_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                requested_price=price,
                order_type="LIMIT",
                rejection_reason="kill_switch_active",
            )
            logging.error(
                "[TradingEngine] LIMIT order rejected by kill switch | %s %s %.6f @ %.2f",
                symbol,
                side.name,
                quantity,
                price,
            )
            return False

        logging.info(
            "[TradingEngine] send_limit_order | %s %s %.6f @ %.2f post_only=%s",
            symbol,
            side.name,
            quantity,
            price,
            post_only,
        )
        order_sent = self.order_manager.place_limit_order(
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            post_only=post_only,
        )

        if not order_sent:
            self.record_rejected_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                requested_price=price,
                order_type="LIMIT",
            )

        return order_sent

    def place_market_order(self, symbol: str, side: Side, quantity: float) -> bool:
        if self.is_kill_switch_active():
            self.record_rejected_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                requested_price=0.0,
                order_type="MARKET",
                rejection_reason="kill_switch_active",
            )
            logging.error(
                "[TradingEngine] MARKET order rejected by kill switch | %s %s %.6f",
                symbol,
                side.name,
                quantity,
            )
            return False

        logging.info(
            "[TradingEngine] send_market_order | %s %s %.6f",
            symbol,
            side.name,
            quantity,
        )
        order_sent = self.order_manager.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
        )

        if not order_sent:
            self.record_rejected_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                requested_price=0.0,
                order_type="MARKET",
            )

        return order_sent

    def record_rejected_order(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        requested_price: float,
        order_type: str,
        rejection_reason: str | None = None,
    ) -> None:
        self.local_order_id += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rejection = self._get_order_manager_rejection()

        price = requested_price
        reason = rejection_reason or "order_manager_rejected"

        if rejection is not None and rejection_reason is None:
            price = rejection.get("price", requested_price)
            reason = rejection.get("reason", reason)

        order_id = f"local_reject_{self.local_order_id:06d}"
        order_row = {
            "created_time": now,
            "updated_time": now,
            "symbol": symbol,
            "order_id": order_id,
            "client_id": "-",
            "side": side.name,
            "status": "REJECTED",
            "order_type": order_type,
            "execution_type": order_type,
            "average_filled_price": 0.0,
            "filled_quantity": 0.0,
            "last_filled_price": 0.0,
            "last_filled_quantity": 0.0,
            "canceled_reason": reason,
            "requested_price": price,
            "requested_quantity": quantity,
        }

        self.order_history_by_id[order_id] = order_row
        self.order_history.append(order_row)
        self.trim_order_history()
        self.publish_dashboard_state()

    def _get_order_manager_rejection(self) -> dict | None:
        if hasattr(self.order_manager, "get_last_rejection"):
            return self.order_manager.get_last_rejection()

        return None

    def is_kill_switch_active(self) -> bool:
        try:
            if not self.kill_switch_file.exists():
                return False

            with open(self.kill_switch_file, "r", encoding="utf-8") as file:
                state = json.load(file)

            return bool(state.get("active", False))
        except Exception:
            logging.exception("Failed to read kill switch state")
            return True

    def is_exit_program_requested(self) -> bool:
        try:
            if not self.exit_program_file.exists():
                return False

            with open(self.exit_program_file, "r", encoding="utf-8") as file:
                state = json.load(file)

            return bool(state.get("active", False))
        except Exception:
            logging.exception("Failed to read exit program state")
            return False

    def get_position(self, symbol: str) -> float:
        return self.position_manager.get_position(symbol)

    def get_average_entry_price(self, symbol: str) -> float:
        return self.position_manager.get_average_entry_price(symbol)

    def get_mark_price(self, symbol: str) -> float:
        return self.position_manager.get_mark_price(symbol)

    def get_equity(self) -> float:
        return self.position_manager.get_equity()

    def get_risk_manager(self) -> RiskManager:
        return self.risk_manager

    def get_order_history(self) -> list[dict]:
        return self.order_history.copy()

    def update_strategy_analytics(self, analytics: dict) -> None:
        self.strategy_analytics.update(analytics)
        self.publish_dashboard_state()

    def set_strategy_analytics(self, name: str, value) -> None:
        self.strategy_analytics[name] = value
        self.publish_dashboard_state()

    def clear_strategy_analytics(self) -> None:
        self.strategy_analytics = {}
        self.publish_dashboard_state()

    def log_mark_to_market(
        self,
        symbol: str,
        mtm_price: float,
        unrealized_pnl: float,
        pnl: float,
        equity: float,
    ) -> None:
        logging.info(
            "[TradingEngine] mark_to_market | %s position=%.4f avg_entry=%.2f mtm=%.2f unrealized=%.4f realized=%.4f "
            "pnl=%.4f equity=%.4f max_drawdown=%.4f max_drawdown_pct=%.2f%%",
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
            "equity_curve": self.risk_manager.get_equity_curve()[-1000:],
        }

        self.dashboard_store.publish(
            summary=summary,
            positions=self.position_manager.get_positions_snapshot(),
            orders=self.get_order_history(),
            analytics=self.strategy_analytics,
        )
