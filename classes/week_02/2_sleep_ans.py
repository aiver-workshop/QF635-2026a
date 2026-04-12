"""
EXERCISE: The Periodic Counter
Goal: Use a while-loop and time.sleep() to print an increasing series.

Note: To stop this script, press 'Ctrl + C' in your terminal.
Reference: https://www.geeksforgeeks.org/sleep-in-python/
"""
import time

number = 1

# This loop will run until manually interrupted
try:
    while True:
        # 1. Print the current value
        print(f"Counter: {number}")

        # 2. Suspend execution for 2 seconds
        # Parameters: (seconds)
        time.sleep(2)

        # 3. Increment for the next iteration
        number += 1
except KeyboardInterrupt:
    print("\nLoop stopped by user.")
