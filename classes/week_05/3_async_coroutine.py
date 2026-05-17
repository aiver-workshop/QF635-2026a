"""
TOPIC: Introduction to Python asyncio and Coroutines

KEY TEACHING POINTS:
1. Synchronous vs Asynchronous Execution:
   A normal function blocks execution until completion, while an async coroutine
   can pause and resume later.

2. Coroutines:
   A coroutine is defined using the 'async def' syntax and represents an
   asynchronous task.

3. Suspension Points:
   The 'await' keyword marks places where a coroutine can suspend execution,
   allowing other tasks to run.

4. Non-Blocking Waiting:
   'await asyncio.sleep()' pauses the coroutine without blocking the entire
   program, unlike 'time.sleep()'.

5. Event Loop:
   'asyncio.run()' creates and manages the asyncio event loop which schedules
   and executes coroutines.

6. Foundation for High-Concurrency Systems:
   asyncio is commonly used for network servers, trading gateways, APIs,
   websocket handlers, and high-performance I/O systems.

7. Important Limitation:
   asyncio improves concurrency for waiting tasks (I/O-bound work), but it does
   not make CPU-heavy computations faster.
"""

import asyncio
import time
import logging


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


def fetch_data() -> str:
    """
    A normal synchronous function.

    The caller is blocked during time.sleep().
    """
    logging.info("Starting synchronous fetch")

    for i in range(3):
        logging.info("[sync] fetching data step=%s", i)

        # Blocks the entire thread
        time.sleep(1)

    logging.info("Completed synchronous fetch")

    return "data_a"


async def fetch_data_async() -> str:
    """
    An asynchronous coroutine.

    Execution can pause at 'await' statements and later resume.
    """
    logging.info("Starting async fetch")

    for i in range(3):
        logging.info("[asyncio] fetching data step=%s", i)

        # Non-blocking sleep
        await asyncio.sleep(1)

    logging.info("Completed async fetch")

    return "data_b"


if __name__ == "__main__":

    logging.info("Running synchronous function")

    start = time.perf_counter()

    data = fetch_data()

    elapsed = time.perf_counter() - start

    # TODO print result and elapsed time

    logging.info("Running async coroutine")

    start = time.perf_counter()

    # Run the coroutine inside an asyncio event loop
    data = asyncio.run(fetch_data_async())

    elapsed = time.perf_counter() - start

    logging.info("Async result = %s", data)
    logging.info("Async runtime = %.2f seconds", elapsed)