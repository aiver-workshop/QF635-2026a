"""
TOPIC: Understanding Synchronous Execution in Python

KEY TEACHING POINTS:
1. Sequential Execution:
   By default, Python functions execute one after another in sequence.
   “Synchronous” means operations happen in sequence, and the caller waits for each operation
   to finish before continuing.

2. Blocking Behaviour:
   A synchronous function blocks the caller until the function completes execution.

3. Runtime Accumulation:
   When two slow functions are executed sequentially, the total runtime becomes
   the sum of both execution times.

5. Logging and Observability:
   Logging timestamps help visualize execution order and identify blocking
   behaviour in synchronous programs.

6. Foundation for Concurrency:
   Understanding synchronous execution is important before learning threading,
   multiprocessing, asyncio, or event-driven systems.
"""

import time
import logging


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


def factorial(n: int) -> int:
    """
    Calculate factorial of n synchronously.
    This function deliberately sleeps for 1 second during each step so students
    can observe that execution is sequential.
    """
    # TODO
    return 0


if __name__ == "__main__":
    start_time = time.perf_counter()

    logging.info("Program started")

    result_10 = factorial(10)
    logging.info("Factorial of 10 = %s", result_10)

    result_15 = factorial(15)
    logging.info("Factorial of 15 = %s", result_15)

    elapsed = time.perf_counter() - start_time

    logging.info("Program completed")
    logging.info("Total runtime = %.2f seconds", elapsed)