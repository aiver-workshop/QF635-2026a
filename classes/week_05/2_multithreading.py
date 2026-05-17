"""
TOPIC: Running Tasks Concurrently with Python Threads

KEY TEACHING POINTS:
1. Thread Creation:
   'Thread(target=..., args=...)' creates a separate thread to execute a function.

2. Concurrent Execution:
   Calling 'start()' allows both factorial calculations to progress at the same time.

3. Waiting for Completion:
   Calling 'join()' blocks the main thread until the worker thread has finished.

4. Returning Results from Threads:
   A thread function does not directly return a value to the caller, so a shared
   mutable object, such as a list, can be used as a result placeholder.

5. I/O Waiting and the GIL:
   'time.sleep()' releases the Global Interpreter Lock (GIL), allowing another
   thread to run while one thread is sleeping.

6. Runtime Reduction:
   The synchronous version takes about 25 seconds, but this threaded version
   takes about 15 seconds because both tasks overlap.
"""

import time
from threading import Thread
import logging


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


def factorial(n: int, result: list[int | None]) -> None:
    """
    Calculate factorial of n in a worker thread.

    The result is written into result[0] because Thread does not directly return
    the function's return value to the main thread.
    """
    calculated_result = 1

    logging.info("Started calculation for n=%s", n)

    for i in range(1, n + 1):
        # Simulate a slow task.
        # During sleep, Python can switch to another thread.
        time.sleep(1)

        logging.info("Calculating factorial[%s], step=%s", n, i)

        calculated_result *= i

    result[0] = calculated_result

    logging.info("Completed calculation for n=%s", n)


if __name__ == "__main__":
    start_time = time.perf_counter()

    result_1 = [None]
    result_2 = [None]

    thread_1 = Thread(
        target=factorial,
        args=(10, result_1),
        name="thread-1",
    )

    # TODO create second thread to run 15!

    logging.info("Starting both threads")

    # TODO start second thread
    thread_1.start()

    logging.info("Main thread is waiting for both threads to finish")

    # TODO wait for second thread to finish calculation
    thread_1.join()

    elapsed = time.perf_counter() - start_time

    logging.info("Factorial of 10 = %s", result_1[0])

    # TODO print result of 15!
    logging.info("Factorial of 15 = %s", result_2[0])

    logging.info("Total runtime = %.2f seconds", elapsed)