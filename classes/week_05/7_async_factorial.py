"""
TOPIC: Concurrent Factorial Calculation with asyncio.gather()

KEY TEACHING POINTS:
1. Calling 'factorial(10)' creates a coroutine object.
2. 'asyncio.gather()' schedules both coroutine objects concurrently.
3. 'await asyncio.gather(...)' waits until both coroutines complete.
4. 'await asyncio.sleep(1)' allows the event loop to switch between coroutines.
5. Total runtime is about 15 seconds, not 25 seconds.
"""

import asyncio
import logging


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


async def factorial(n: int) -> int:
    result = 1

    logging.info("Started calculation for n=%s", n)

    for i in range(1, n + 1):
        await asyncio.sleep(1)

        logging.info("Calculating factorial[%s] step = %s", n, i)

        result *= i

    return result


async def concurrent_calculation() -> None:
    # TODO calculate 10! and 15! concurrently and print the results
    pass


if __name__ == "__main__":
    asyncio.run(concurrent_calculation())