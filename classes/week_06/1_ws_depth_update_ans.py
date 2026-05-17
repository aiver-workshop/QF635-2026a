"""
TOPIC: Subscribing Directly to Binance Futures Depth Updates

REFERENCE:
https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Diff-Book-Depth-Streams
https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/How-to-manage-a-local-order-book-correctly

KEY TEACHING POINTS:
1. Depth Stream:
   Binance depth streams publish incremental order book updates (deltas),
   NOT full order book snapshots.

2. Incremental Updates:
   Each websocket message only contains price levels that changed.

3. Bid and Ask Updates:
   - 'b' contains bid updates
   - 'a' contains ask updates

4. Price Level Format:
   Each price level is represented as:
       [price, quantity]

5. Quantity Semantics:
   quantity = 0 means the price level should be removed from the local book.

6. Local Book Simulation:
   This example maintains a small in-memory order book so students can observe:
       - ADD
       - MODIFY
       - DELETE
   operations.

7. Algorithms to maintain local order book:
    1. Open websocket depth stream.
    2. Buffer all incoming depth updates.
    3. Fetch REST order book snapshot.
    4. Read snapshot lastUpdateId.
    5. Drop any buffered update where:
       update.u <= lastUpdateId
    6. Find the first buffered update where:
       update.U <= lastUpdateId + 1 <= update.u
    7. Apply that update to the snapshot.
    8. Apply all later buffered updates in sequence.
    9. For every new websocket update after that:
       previous update ID + 1 must match the new update range.
    10. If sequence breaks:
       discard book and restart from step 1.
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
STREAM = f"{SYMBOL}@depth@100ms"
WEBSOCKET_URL = (f"wss://fstream.binance.com/public/ws/{STREAM}")

# Simple local order book representation
local_bids = {}
local_asks = {}


async def subscribe_depth_updates() -> None:

    logging.info("Connecting to %s", WEBSOCKET_URL)

    async with websockets.connect(WEBSOCKET_URL) as websocket:
        logging.info("Connected to Binance Futures depth stream: %s", STREAM)

        async for message in websocket:
            data = json.loads(message)
            handle_depth_update(data)


def handle_depth_update(data: dict) -> None:
    event_time = data["E"]
    logging.info(
        "Depth Update | eventTime=%s",
        event_time,
    )

    # Process bid updates
    for bid in data["b"]:
        process_book_update(
            side="BID",
            book=local_bids,
            update=bid,
        )

    # Process ask updates
    for ask in data["a"]:
        process_book_update(
            side="ASK",
            book=local_asks,
            update=ask,
        )

    logging.info("-" * 80)


def process_book_update(side: str, book: dict, update: list) -> None:
    price = float(update[0])
    quantity = float(update[1])
    existing_quantity = book.get(price)

    # DELETE level
    if quantity == 0:
        if price in book:
            del book[price]
            logging.info(
                "%s DELETE | price=%.2f",
                side,
                price,
            )
        return

    # ADD level
    if existing_quantity is None:
        book[price] = quantity
        logging.info(
            "%s ADD | price=%.2f quantity=%.4f",
            side,
            price,
            quantity,
        )
        return

    # MODIFY existing level
    if existing_quantity != quantity:
        book[price] = quantity
        logging.info(
            "%s MODIFY | price=%.2f oldQty=%.4f newQty=%.4f",
            side,
            price,
            existing_quantity,
            quantity,
        )


if __name__ == "__main__":
    asyncio.run(subscribe_depth_updates())