# Week 06: Event-Driven Pair Trading

This week builds from raw Binance Futures websocket streams into an event-driven
gateway and a BTC/ETH pair trading strategy.

The final example is:

- `7_pair_trading_ans.py`

It subscribes to `BTCUSDT` and `ETHUSDT`, maintains the latest order book for
each symbol, computes a rolling log-price spread, and sends pair entry/exit
orders when the spread z-score crosses strategy thresholds.

## Main Classes

Plain-text version for IntelliJ Markdown preview:

```text
BinanceFutureGateway
    owns Binance REST + websocket clients
    owns callback lists
    publishes VenueOrderBook, AggTrade, and OrderEvent
    sends market and limit orders

PairTradingStrategy
    registers callback methods with the gateway
    stores latest BTCUSDT and ETHUSDT books
    calculates spread z-score
    sends pair entry/exit orders through the gateway
    tracks position and PnL from execution fills

Shared event objects
    VenueOrderBook -> wraps OrderBook with exchange name
    OrderBook      -> best bid/ask and depth levels
    AggTrade       -> public trade with contract_name
    OrderEvent     -> private order/fill update
```

Mermaid version for renderers that support it:

```mermaid
classDiagram
    class BinanceFutureGateway {
        -list[str] _symbols
        -Client _client
        -AsyncClient _async_client
        -dict _depth_caches
        -list _orderbook_callbacks
        -list _execution_callbacks
        -list _agg_trade_callbacks
        +connect() None
        +get_order_book(symbol) OrderBook
        +place_limit_order(symbol, side, price, quantity, post_only) bool
        +place_market_order(symbol, side, quantity) bool
        +register_orderbook_callback(callback) None
        +register_execution_callback(callback) None
        +register_agg_trade_callback(callback) None
    }

    class PairTradingStrategy {
        +str base_symbol
        +str hedge_symbol
        +dict last_book
        +deque spread_window
        +float entry_z_score
        +float exit_z_score
        +int pair_state
        +bool enable_trading
        +dict position
        +dict average_entry_price
        +float realized_pnl
        +on_orderbook(order_book) None
        +on_agg_trade(trade) None
        +on_execution(order_event) None
        +evaluate_pair() None
        +send_pair_orders(base_side, hedge_side) dict
    }

    class VenueOrderBook {
        +str exchange_name
        +OrderBook book
        +get_book() OrderBook
    }

    class OrderBook {
        +str contract_name
        +float timestamp
        +list bids
        +list asks
        +get_best_bid()
        +get_best_ask()
    }

    class AggTrade {
        +str contract_name
        +float price
        +float size
        +bool is_buyer_maker
        +is_buy() bool
        +is_sell() bool
    }

    class OrderEvent {
        +str contract_name
        +str order_id
        +ExecutionType execution_type
        +OrderStatus status
        +Side side
        +float last_filled_price
        +float last_filled_quantity
    }

    BinanceFutureGateway --> VenueOrderBook : publishes
    BinanceFutureGateway --> AggTrade : publishes
    BinanceFutureGateway --> OrderEvent : publishes
    PairTradingStrategy --> BinanceFutureGateway : sends orders through
    VenueOrderBook --> OrderBook : wraps
```

## Callback Design

The gateway owns the Binance connections. The strategy does not read directly
from Binance. Instead, the strategy registers callback methods with the gateway:

```python
gateway.register_orderbook_callback(strategy.on_orderbook)
gateway.register_execution_callback(strategy.on_execution)
gateway.register_agg_trade_callback(strategy.on_agg_trade)
```

When a websocket message arrives, the gateway converts the raw Binance message
into a course-level event object, then calls every registered callback.

Plain-text version for IntelliJ Markdown preview:

```text
Startup
-------
PairTradingStrategy                  BinanceFutureGateway
        |                                      |
        | register_orderbook_callback(...)     |
        | register_agg_trade_callback(...)     |
        | register_execution_callback(...)     |
        |                                      |

Order book update
-----------------
Binance Futures -> BinanceFutureGateway -> PairTradingStrategy
 depth update       build OrderBook         on_orderbook(...)
                    wrap VenueOrderBook     store latest book
                                            evaluate_pair()

Agg trade update
----------------
Binance Futures -> BinanceFutureGateway -> PairTradingStrategy
 aggTrade          build AggTrade           on_agg_trade(...)
                                            update net_volume

Execution update
----------------
Binance Futures -> BinanceFutureGateway -> PairTradingStrategy
 ORDER_TRADE_      build OrderEvent         on_execution(...)
 UPDATE                                     update position
                                            update realized PnL
```

Mermaid version for renderers that support it:

```mermaid
sequenceDiagram
    participant Binance
    participant Gateway as BinanceFutureGateway
    participant Strategy as PairTradingStrategy

    Note over Strategy,Gateway: Register callbacks once during startup
    Strategy->>Gateway: register_orderbook_callback(strategy.on_orderbook)
    Strategy->>Gateway: register_agg_trade_callback(strategy.on_agg_trade)
    Strategy->>Gateway: register_execution_callback(strategy.on_execution)

    Note over Binance,Gateway: Market data event
    Binance->>Gateway: BTCUSDT / ETHUSDT depth update
    Gateway->>Gateway: update local depth cache
    Gateway->>Gateway: build OrderBook
    Gateway->>Strategy: on_orderbook(VenueOrderBook)
    Strategy->>Strategy: store latest book
    Strategy->>Strategy: evaluate_pair()

    Note over Binance,Gateway: Public trade event
    Binance->>Gateway: aggTrade message
    Gateway->>Gateway: build AggTrade
    Gateway->>Strategy: on_agg_trade(AggTrade)
    Strategy->>Strategy: update net_volume

    Note over Binance,Gateway: Private execution event
    Binance->>Gateway: ORDER_TRADE_UPDATE
    Gateway->>Gateway: build OrderEvent
    Gateway->>Strategy: on_execution(OrderEvent)
    Strategy->>Strategy: update position and realized PnL from fills
```

## Pair Trading Flow

The pair strategy waits until it has both BTCUSDT and ETHUSDT books. On each
book update it calculates mid prices:

```python
base_mid = (btc_best_bid + btc_best_ask) / 2
hedge_mid = (eth_best_bid + eth_best_ask) / 2
```

Then it calculates a rolling spread:

```python
spread = log(base_mid) - hedge_ratio * log(hedge_mid)
```

Once the spread window is full, the strategy calculates a z-score:

```python
z_score = (spread - mean) / standard_deviation
```

The strategy state machine is:

```mermaid
stateDiagram-v2
    [*] --> Flat
    Flat --> LongSpread: z <= -entry_z_score
    Flat --> ShortSpread: z >= entry_z_score
    LongSpread --> Exiting: z >= -exit_z_score
    ShortSpread --> Exiting: z <= exit_z_score
    Exiting --> Flat: both legs flat after fills
```

Where:

- `LongSpread` means buy BTCUSDT and sell ETHUSDT.
- `ShortSpread` means sell BTCUSDT and buy ETHUSDT.
- `Exiting` means exit orders have been sent and the strategy is waiting for
  execution fills.

## PnL Callback

PnL is not calculated from submitted order prices. It is calculated from actual
execution fills received in `on_execution`.

```mermaid
sequenceDiagram
    participant Strategy as PairTradingStrategy
    participant Gateway as BinanceFutureGateway
    participant Binance

    Strategy->>Gateway: place_market_order(BTCUSDT)
    Strategy->>Gateway: place_market_order(ETHUSDT)
    Gateway->>Binance: futures_create_order(type="MARKET")
    Binance-->>Gateway: ORDER_TRADE_UPDATE with fill price and quantity
    Gateway->>Strategy: on_execution(OrderEvent)
    Strategy->>Strategy: update_position_from_fill()
    Strategy->>Strategy: realized_pnl += fill_pnl
```

After both legs are flat on exit, the strategy logs:

```text
EXIT PNL from actual fills | trade=... cumulative=...
TOTAL PNL = ...
```

## Important Safety Notes

- `USE_TESTNET = True` sends orders to Binance Futures testnet.
- `ENABLE_TRADING = True` allows the strategy to submit orders.
- For live market data without order submission, use `USE_TESTNET = False` and
  `ENABLE_TRADING = False`.
- This teaching version does not tag orders with custom client IDs yet, so a
  production version should filter execution events to only count fills created
  by this strategy.
