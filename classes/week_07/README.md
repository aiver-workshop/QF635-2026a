# Week 7 Trading Engine Design

This folder demonstrates a modular trading system for live Binance Futures
strategies. The main goal is to decouple strategy logic from exchange
connectivity, order routing, position tracking, risk, and dashboard publishing.

## File Layout

```text
week_07/
  gateway.py              Binance Futures websocket/REST gateway
  trading_engine.py       Central event router and shared runtime services
  order_manager.py        Order submission abstraction
  position_manager.py     Position, average entry, realized/unrealized PnL
  risk_manager.py         Portfolio equity curve and drawdown
  dashboard.py            Dash web dashboard
  dashboard_store.py      JSON publisher used by the dashboard

  strategy_simple.py      Empty callback strategy template
  strategy_ma.py          Moving average crossover strategy
  strategy_pair.py        BTC/ETH pair trading strategy

  main_simple.py          Runs SimpleStrategy
  main_ma.py              Runs MovingAverageCrossoverStrategy
  main_pair.py            Runs PairTradingStrategy

  state/
    dashboard_state.json
    kill_switch_state.json
    exit_program_state.json
```

## Design Summary

The strategy does not talk to Binance directly. Binance connectivity is handled
by `BinanceFutureGateway`. The strategy receives normalized callbacks from
`TradingEngine`, and sends orders by calling methods on `TradingEngine`.

```text
                 market data / executions
 Binance Futures -----------------------> BinanceFutureGateway
                                                |
                                                | callbacks
                                                v
                                         TradingEngine
                                      /      |       \
                                     /       |        \
                                    v        v         v
                              Strategy  PositionMgr  RiskMgr
                                    |
                                    | place order request
                                    v
                              TradingEngine
                                    |
                                    v
                              OrderManager
                                    |
                                    v
                           BinanceFutureGateway
```

### Main Classes

`BinanceFutureGateway`

- Connects to Binance Futures websocket streams.
- Publishes order book, aggregate trade, and execution callbacks.
- Sends live market and limit orders through Binance REST.
- Keeps latest order book per symbol.
- Handles Binance precision formatting for price and quantity.

`TradingEngine`

- Registers callbacks with the gateway.
- Receives all gateway callbacks first.
- Updates position, PnL, mark-to-market, risk, dashboard, and order history.
- Forwards callbacks to the strategy.
- Exposes strategy-facing APIs such as:
  - `place_market_order(symbol, side, quantity)`
  - `place_limit_order(symbol, side, price, quantity, post_only=True)`
  - `get_position(symbol)`
  - `get_average_entry_price(symbol)`
  - `get_mark_price(symbol)`
  - `get_equity()`
  - `get_risk_manager()`
  - `update_strategy_analytics({...})`

`OrderManager`

- Defines the order-sending interface.
- `LiveOrderManager` sends orders to the live gateway.
- A future backtest order manager can implement the same methods and simulate
  fills without changing strategy code.
- Performs pre-trade checks such as max order notional.

`PositionManager`

- Updates position from actual execution fills.
- Tracks average entry price, realized PnL, unrealized PnL, mark price, and
  total equity.
- Uses actual filled prices from execution events.

`RiskManager`

- Consumes portfolio equity updates.
- Tracks equity curve, current drawdown, and max drawdown.
- This is portfolio-level risk; it does not need to know which strategy or
  symbol produced the PnL.

`Dashboard`

- Reads state from `state/dashboard_state.json`.
- Displays equity summary, equity curve, live positions, order history, and
  strategy analytics.
- Start/Stop Trading writes to `state/kill_switch_state.json`.
- Kill Switch writes to `state/exit_program_state.json`.

## Callback Flow

### Order Book Update

```text
Binance websocket depth update
  -> BinanceFutureGateway builds VenueOrderBook
  -> TradingEngine.on_orderbook(...)
       -> stores latest order book
       -> marks open position using conservative MTM
          - long position uses best bid
          - short position uses best ask
       -> updates risk and dashboard
       -> strategy.on_orderbook(...)
```

### Execution Update

```text
Binance user data execution update
  -> BinanceFutureGateway builds OrderEvent
  -> TradingEngine.on_execution(...)
       -> records or updates one order-history row
       -> if execution_type == TRADE:
            -> PositionManager.on_fill(...)
            -> RiskManager.on_equity_update(...)
            -> dashboard update
       -> strategy.on_execution(...)
```

### Strategy Sends Order

```text
strategy decides to trade
  -> strategy calls TradingEngine.place_market_order(...)
  -> TradingEngine checks kill switch
  -> LiveOrderManager checks max order notional
  -> BinanceFutureGateway sends order to Binance
  -> later, execution callback updates position/PnL
```

## Existing Strategies

### `strategy_simple.py`

`SimpleStrategy` is the smallest callback example. It implements:

```python
def set_trading_engine(self, trading_engine: TradingEngine) -> None:
    ...

def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
    ...

def on_agg_trade(self, trade: AggTrade) -> None:
    ...

def on_execution(self, order_event: OrderEvent) -> None:
    ...
```

Use this file as the starting template for a new strategy.

### `strategy_ma.py`

`MovingAverageCrossoverStrategy`:

- Calculates mid price from order book updates.
- Maintains short and long moving average windows.
- Goes long when short MA is above long MA.
- Goes short when short MA is below long MA.
- Sends only the quantity needed to move from current position to target
  position.
- Publishes strategy analytics to the dashboard.

### `strategy_pair.py`

`PairTradingStrategy`:

- Trades BTCUSDT and ETHUSDT together.
- Builds a rolling log-price spread.
- Enters long spread when z-score is low.
- Enters short spread when z-score is high.
- Exits when the z-score mean reverts.
- Uses current positions to avoid repeatedly buying the same spread.

## How To Create A New Strategy

### 1. Create A Strategy File

Use the naming pattern:

```text
strategy_your_name.py
```

Start from this structure:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from common.interface_book import VenueOrderBook
from common.interface_order import OrderEvent, Side
from common.interface_trade import AggTrade

if TYPE_CHECKING:
    from trading_engine import TradingEngine


class YourStrategy:

    def __init__(self, name: str = "YourStrategy") -> None:
        self.name: str = name
        self.trading_engine: TradingEngine | None = None

    def set_trading_engine(self, trading_engine: TradingEngine) -> None:
        self.trading_engine = trading_engine

    def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
        if self.trading_engine is None:
            return

        book = venue_order_book.get_book()
        symbol = book.contract_name
        best_bid = book.get_best_bid()
        best_ask = book.get_best_ask()
        mid_price = (best_bid + best_ask) / 2.0

        self.trading_engine.update_strategy_analytics(
            {
                "strategy": self.name,
                "symbol": symbol,
                "mid_price": mid_price,
                "signal": "HOLD",
            }
        )

    def on_agg_trade(self, trade: AggTrade) -> None:
        pass

    def on_execution(self, order_event: OrderEvent) -> None:
        pass
```

### 2. Use Engine APIs Instead Of Direct Managers

Inside a strategy, use `self.trading_engine` for shared services:

```python
current_position = self.trading_engine.get_position("BTCUSDT")
equity = self.trading_engine.get_equity()
risk_manager = self.trading_engine.get_risk_manager()
```

Send orders through the engine:

```python
self.trading_engine.place_market_order(
    symbol="BTCUSDT",
    side=Side.BUY,
    quantity=0.001,
)
```

Do not call the gateway, position manager, or risk manager directly unless you
are intentionally extending the engine design.

### 3. Add A Main File

Use the naming pattern:

```text
main_your_name.py
```

Minimal structure:

```python
import logging
import time

from gateway import BinanceFutureGateway
from order_manager import LiveOrderManager
from strategy_your_name import YourStrategy
from trading_engine import TradingEngine


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


if __name__ == "__main__":
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    USE_TESTNET = True
    INITIAL_CAPITAL = 10000.0
    MAX_ORDER_NOTIONAL = 10000.0
    SYMBOLS = ["BTCUSDT"]

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
    strategy = YourStrategy()
    engine = TradingEngine(
        gateway=gateway,
        strategy=strategy,
        order_manager=order_manager,
        initial_capital=INITIAL_CAPITAL,
    )

    engine.start()

    while True:
        time.sleep(1)
```

### 4. Run The Strategy

From `classes/week_07`:

```text
python main_simple.py
python main_ma.py
python main_pair.py
python main_your_name.py
```

Run the dashboard in a separate terminal:

```text
python dashboard.py
```

Then open:

```text
http://127.0.0.1:8052
```

## Strategy Rules Of Thumb

- Keep signal logic inside the strategy.
- Keep execution, PnL, risk, dashboard publishing, and order history inside the
  engine.
- Use current position from the engine before sending a new order.
- Track pending orders if a strategy should not send another order before the
  previous one finishes.
- Publish useful dashboard analytics with `update_strategy_analytics`.
- Use small quantities on testnet and set `MAX_ORDER_NOTIONAL` explicitly in
  the main file.
- Treat order fills as the source of truth for position and realized PnL.

## Dashboard State Files

Runtime JSON files are kept in `state/`:

```text
state/dashboard_state.json       latest dashboard snapshot
state/kill_switch_state.json     Stop/Start Trading control
state/exit_program_state.json    Kill Switch control
```

These are runtime files, not strategy logic.
