"""
TOPIC: Subscribing to Binance USD-M Futures aggTrade Stream with asyncio

REFERENCE:
https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Aggregate-Trade-Streams

KEY TEACHING POINTS:
1. Public Market Data:
   aggTrade is a public market data stream, so no API key or signature is needed.

2. Futures WebSocket URL:
   USD-M Futures market streams use:
       wss://fstream.binance.com/market/ws/<streamName>

3. Stream Name:
   For BTCUSDT perpetual futures aggregate trades:
       btcusdt@aggTrade

4. Async WebSocket Client:
   'websockets.connect()' opens a websocket connection asynchronously.

5. Continuous Message Processing:
   'async for message in websocket' keeps receiving messages until the connection
   is closed or an error occurs.

6. Non-Blocking I/O:
   While waiting for websocket messages, the asyncio event loop is free to run
   other async tasks.

7. Real-Time Trading Systems:
   This pattern is commonly used for market data listeners, trading gateways,
   quote engines, and event-driven trading systems.
"""

import asyncio
import json
import logging
import websockets


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


SYMBOL = "btcusdt"
STREAM = f"{SYMBOL}@aggTrade"
WEBSOCKET_URL = f"wss://fstream.binance.com/market/ws/{STREAM}"


async def subscribe_agg_trade() -> None:
    logging.info("Connecting to %s", WEBSOCKET_URL)

    async with websockets.connect(WEBSOCKET_URL) as websocket:
        logging.info("Connected to Binance Futures aggTrade stream: %s", STREAM)

        # The websocket object is an asynchronous iterator.
        # Internally, Python repeatedly performs:
        #     message = await websocket.recv()
        # and automatically waits asynchronously for the next websocket message.
        # This provides a clean and Pythonic way to process continuous websocket streams.
        async for message in websocket:
            data = json.loads(message)
            handle_trade(data)


def handle_trade(data):
    event_time = data["E"]
    symbol = data["s"]
    agg_trade_id = data["a"]
    price = data["p"]
    quantity = data["q"]
    trade_time = data["T"]
    is_buyer_maker = data["m"]

    # Binance convention:
    # m=True  -> buyer is maker -> aggressive seller
    # m=False -> seller is maker -> aggressive buyer
    trade_side = "SELL aggressor" if is_buyer_maker else "BUY aggressor"

    logging.info(
        "%s %s | price=%s qty=%s aggTradeId=%s eventTime=%s tradeTime=%s",
        symbol,
        trade_side,
        price,
        quantity,
        agg_trade_id,
        event_time,
        trade_time,
    )


if __name__ == "__main__":
    asyncio.run(subscribe_agg_trade())