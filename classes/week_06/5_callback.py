"""
TOPIC: Simple Callback Demonstration

KEY TEACHING POINTS:
1. Callback Function:
   A callback is a function passed into another part of the program to be
   invoked later.

2. Event-Driven Programming:
   The callback is triggered automatically when an event occurs.

3. Loose Coupling:
   The event source does not need to know what the callback does internally.

4. Real Trading Systems:
   Similar callback patterns are commonly used for:
       - market data handlers
       - websocket listeners
       - order gateways
       - GUI events
"""

import logging
import random
import time

logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


def strategy_callback(number: int) -> None:
    """
    Strategy logic triggered by new data.
    """
    logging.info("Strategy received number: %s",number)


def start_data_source(callback) -> None:
    """
    Simulate an external event source.
    """
    while True:
        time.sleep(1)
        # Simulate incoming event/data
        number = random.randint(1, 100)

        logging.info("Data source generated: %s",number)

        # TODO Invoke callback


if __name__ == "__main__":
    # Register callback
    start_data_source(strategy_callback)