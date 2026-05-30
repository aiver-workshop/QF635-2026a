"""
Position manager for fills and mark-to-market PnL.

This class keeps average entry price, current position, realized PnL, and
mark-to-market unrealized PnL per symbol. It is intentionally exchange-agnostic:
callers pass in normalized fill fields from OrderEvent and mark prices from
market data.
"""

import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from common.interface_order import Side


class PositionManager:

    def __init__(self, initial_capital: float = 0.0):
        self.initial_capital = initial_capital
        self.position = {}
        self.average_entry_price = {}
        self.realized_pnl = {}
        self.mark_price = {}
        self.unrealized_pnl = {}
        self.total_realized_pnl = 0.0
        self.total_unrealized_pnl = 0.0

    def on_fill(self, symbol: str, side: Side, price: float, quantity: float) -> float:
        symbol = symbol.upper()
        self._ensure_symbol(symbol)

        old_position = self.position[symbol]
        old_average_price = self.average_entry_price[symbol]
        signed_quantity = quantity if side == Side.BUY else -quantity

        if old_position == 0 or old_position * signed_quantity > 0:
            self._increase_position(
                symbol=symbol,
                old_position=old_position,
                old_average_price=old_average_price,
                fill_price=price,
                fill_quantity=quantity,
                signed_quantity=signed_quantity,
            )
            self._refresh_unrealized_pnl(symbol)
            self._log_fill(symbol, side, price, quantity, 0.0)
            return 0.0

        closed_quantity = min(abs(old_position), quantity)
        fill_pnl = self._calculate_closed_pnl(
            old_position=old_position,
            average_price=old_average_price,
            fill_price=price,
            closed_quantity=closed_quantity,
        )

        self._apply_closing_fill(
            symbol=symbol,
            old_position=old_position,
            signed_quantity=signed_quantity,
            fill_price=price,
        )

        self.realized_pnl[symbol] += fill_pnl
        self.total_realized_pnl += fill_pnl
        self._refresh_unrealized_pnl(symbol)
        self._log_fill(symbol, side, price, quantity, fill_pnl)

        return fill_pnl

    def get_position(self, symbol: str) -> float:
        symbol = symbol.upper()
        self._ensure_symbol(symbol)
        return self.position[symbol]

    def get_average_entry_price(self, symbol: str) -> float:
        symbol = symbol.upper()
        self._ensure_symbol(symbol)
        return self.average_entry_price[symbol]

    def get_realized_pnl(self, symbol: str) -> float:
        symbol = symbol.upper()
        self._ensure_symbol(symbol)
        return self.realized_pnl[symbol]

    def mark_to_market(self, symbol: str, mark_price: float) -> float:
        symbol = symbol.upper()
        self._ensure_symbol(symbol)

        self.mark_price[symbol] = mark_price

        position = self.position[symbol]
        average_price = self.average_entry_price[symbol]

        if position > 0:
            unrealized_pnl = (mark_price - average_price) * position
        elif position < 0:
            unrealized_pnl = (average_price - mark_price) * abs(position)
        else:
            unrealized_pnl = 0.0

        self.unrealized_pnl[symbol] = unrealized_pnl
        self.total_unrealized_pnl = sum(self.unrealized_pnl.values())

        return unrealized_pnl

    def _refresh_unrealized_pnl(self, symbol: str) -> None:
        position = self.position[symbol]
        mark_price = self.mark_price[symbol]
        average_price = self.average_entry_price[symbol]

        if position == 0 or mark_price == 0:
            self.unrealized_pnl[symbol] = 0.0
        elif position > 0:
            self.unrealized_pnl[symbol] = (mark_price - average_price) * position
        else:
            self.unrealized_pnl[symbol] = (average_price - mark_price) * abs(position)

        self.total_unrealized_pnl = sum(self.unrealized_pnl.values())

    def get_unrealized_pnl(self, symbol: str) -> float:
        symbol = symbol.upper()
        self._ensure_symbol(symbol)
        return self.unrealized_pnl[symbol]

    def get_mark_price(self, symbol: str) -> float:
        symbol = symbol.upper()
        self._ensure_symbol(symbol)
        return self.mark_price[symbol]

    def get_total_pnl(self) -> float:
        return self.total_realized_pnl + self.total_unrealized_pnl

    def get_equity(self) -> float:
        return self.initial_capital + self.get_total_pnl()

    def get_symbol_equity(self, symbol: str) -> float:
        symbol = symbol.upper()
        self._ensure_symbol(symbol)

        position_value = abs(self.position[symbol]) * self.average_entry_price[symbol]
        symbol_pnl = self.realized_pnl[symbol] + self.unrealized_pnl[symbol]

        return position_value + symbol_pnl

    def get_positions_snapshot(self) -> list[dict]:
        snapshots = []

        for symbol in sorted(self.position.keys()):
            snapshots.append(
                {
                    "symbol": symbol,
                    "position": self.position[symbol],
                    "average_entry_price": self.average_entry_price[symbol],
                    "mark_price": self.mark_price[symbol],
                    "realized_pnl": self.realized_pnl[symbol],
                    "unrealized_pnl": self.unrealized_pnl[symbol],
                    "symbol_pnl": self.realized_pnl[symbol] + self.unrealized_pnl[symbol],
                }
            )

        return snapshots

    def _ensure_symbol(self, symbol: str) -> None:
        if symbol not in self.position:
            self.position[symbol] = 0.0
            self.average_entry_price[symbol] = 0.0
            self.realized_pnl[symbol] = 0.0
            self.mark_price[symbol] = 0.0
            self.unrealized_pnl[symbol] = 0.0

    def _increase_position(
        self,
        symbol: str,
        old_position: float,
        old_average_price: float,
        fill_price: float,
        fill_quantity: float,
        signed_quantity: float,
    ) -> None:
        new_position = old_position + signed_quantity
        new_average_price = (
            (abs(old_position) * old_average_price) + (fill_quantity * fill_price)
        ) / abs(new_position)

        self.position[symbol] = new_position
        self.average_entry_price[symbol] = new_average_price

    def _calculate_closed_pnl(
        self,
        old_position: float,
        average_price: float,
        fill_price: float,
        closed_quantity: float,
    ) -> float:
        if old_position > 0:
            return (fill_price - average_price) * closed_quantity

        return (average_price - fill_price) * closed_quantity

    def _apply_closing_fill(
        self,
        symbol: str,
        old_position: float,
        signed_quantity: float,
        fill_price: float,
    ) -> None:
        new_position = old_position + signed_quantity

        if abs(new_position) < 0.00000001:
            self.position[symbol] = 0.0
            self.average_entry_price[symbol] = 0.0
        elif old_position * new_position > 0:
            self.position[symbol] = new_position
        else:
            self.position[symbol] = new_position
            self.average_entry_price[symbol] = fill_price

    def _log_fill(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        fill_pnl: float,
    ) -> None:
        logging.info(
            "PositionManager fill | %s %s %.6f @ %.2f | position=%.6f avg_entry=%.2f "
            "fill_pnl=%.4f realized=%.4f unrealized=%.4f total=%.4f",
            symbol,
            side.name,
            quantity,
            price,
            self.get_position(symbol),
            self.get_average_entry_price(symbol),
            fill_pnl,
            self.get_realized_pnl(symbol),
            self.get_unrealized_pnl(symbol),
            self.get_total_pnl(),
        )


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s [%(levelname)-5.5s] %(message)s",
        level=logging.INFO,
        stream=sys.stdout,
    )

    position_manager = PositionManager(initial_capital=10000.0)
    symbol = "BTCUSDT"

    print("Test 1: open long")
    fill_price = 100.00
    fill_pnl = position_manager.on_fill(
        symbol=symbol,
        side=Side.BUY,
        price=fill_price,
        quantity=2.0,
    )
    print("fill_price =", fill_price)
    print("fill_pnl =", fill_pnl)
    print("position =", position_manager.get_position(symbol))
    print("avg_entry =", position_manager.get_average_entry_price(symbol))
    print("symbol_equity =", position_manager.get_symbol_equity(symbol))
    print()

    print("Test 2: mark to market higher")
    mtm_price = 105.00
    unrealized_pnl = position_manager.mark_to_market(symbol, mtm_price)
    print("mtm_price =", position_manager.get_mark_price(symbol))
    print("unrealized_pnl =", unrealized_pnl)
    print("total_pnl =", position_manager.get_total_pnl())
    print("equity =", position_manager.get_equity())
    print("symbol_equity =", position_manager.get_symbol_equity(symbol))
    print()

    print("Test 3: partially close long")
    fill_price = 106.00
    fill_pnl = position_manager.on_fill(
        symbol=symbol,
        side=Side.SELL,
        price=fill_price,
        quantity=1.0,
    )
    print("fill_price =", fill_price)
    print("fill_pnl =", fill_pnl)
    print("position =", position_manager.get_position(symbol))
    print("realized_pnl =", position_manager.get_realized_pnl(symbol))
    print("unrealized_pnl =", position_manager.get_unrealized_pnl(symbol))
    print("total_pnl =", position_manager.get_total_pnl())
    print("equity =", position_manager.get_equity())
    print("symbol_equity =", position_manager.get_symbol_equity(symbol))
    print()

    print("Test 4: close remaining long")
    fill_price = 103.00
    fill_pnl = position_manager.on_fill(
        symbol=symbol,
        side=Side.SELL,
        price=fill_price,
        quantity=1.0,
    )
    print("fill_price =", fill_price)
    print("fill_pnl =", fill_pnl)
    print("position =", position_manager.get_position(symbol))
    print("realized_pnl =", position_manager.get_realized_pnl(symbol))
    print("unrealized_pnl =", position_manager.get_unrealized_pnl(symbol))
    print("total_pnl =", position_manager.get_total_pnl())
    print("equity =", position_manager.get_equity())
    print("symbol_equity =", position_manager.get_symbol_equity(symbol))
