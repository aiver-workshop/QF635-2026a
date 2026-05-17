"""
TOPIC: Using a Class to Build a Binance Futures aggTrade WebSocket Client

KEY TEACHING POINTS:
1. Object-Oriented Design:
   A class groups related data and behaviour together.

2. Instance Attributes:
   The symbol, stream name, and websocket URL are stored as object state.

3. Instance Methods:
   Methods such as 'subscribe()', 'handle_message()', and 'handle_trade()'
   define the behaviour of the websocket client.

4. Separation of Concerns:
   Connection logic, JSON parsing, and trade handling are split into separate
   methods.

5. Reusability:
   The same class can be reused for another symbol by creating a different
   object, such as:
       BinanceAggTradeClient("ethusdt")

6. Async Methods:
   Class methods can also be asynchronous when declared with 'async def'.

7. Real-Time Trading Systems:
   This is closer to how production market data listeners are usually designed.
"""

import asyncio
import json
import logging
import websockets

logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


class BinanceAggTradeClient:
    def __init__(self, symbol: str):
        self.symbol = symbol.lower()
        self.stream = f"{self.symbol}@aggTrade"
        self.websocket_url = f"wss://fstream.binance.com/market/ws/{self.stream}"

        # To compute pressure - the imbalance between aggressive buying and aggressive selling.
        self.buy_volume = 0.0
        self.sell_volume = 0.0

    async def subscribe(self) -> None:
        logging.info("Connecting to %s", self.websocket_url)

        async with websockets.connect(self.websocket_url) as websocket:
            logging.info("Connected to Binance Futures aggTrade stream: %s", self.stream)

            async for message in websocket:
                self.handle_message(message)

    def handle_message(self, message: str) -> None:
        data = json.loads(message)
        self.handle_trade(data)

    def handle_trade(self, data: dict) -> None:
        symbol = data["s"]
        price = float(data["p"])
        quantity = float(data["q"])
        trade_time = data["T"]

        is_buyer_maker = data["m"]

        if is_buyer_maker:
            trade_side = "SELL"
            self.sell_volume += quantity
        else:
            trade_side = "BUY"
            self.buy_volume += quantity

        total_volume = self.buy_volume + self.sell_volume

        if total_volume > 0:
            pressure = self.buy_volume / total_volume
        else:
            pressure = 0.5

        logging.info(
            "%s %s | price=%.2f qty=%.4f | buyVol=%.4f sellVol=%.4f pressure=%.2f tradeTime=%s",
            symbol,
            trade_side,
            price,
            quantity,
            self.buy_volume,
            self.sell_volume,
            pressure,
            trade_time,
        )


if __name__ == "__main__":
    client = BinanceAggTradeClient("btcusdt")
    asyncio.run(client.subscribe())