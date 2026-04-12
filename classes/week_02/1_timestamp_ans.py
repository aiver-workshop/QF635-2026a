"""
LESSON: Computer Time vs. Human Time
Goal: Understand how to convert raw system 'ticks' into meaningful dates.

Reference: https://realpython.com/python-time-module/
"""
import time
from datetime import datetime

# 1. Get current time in seconds (float)
# Useful for calculating time differences (performance)
ts = time.time()

# 2. Get current time in nanoseconds (integer)
# Useful for high-precision logging
tn = time.time_ns()

print(f"Seconds since Epoch: {ts}")
print(f"Nanoseconds since Epoch: {tn}")

# 3. Convert epoch time to a human-readable datetime object
# This accounts for your local time zone by default
dt_obj = datetime.fromtimestamp(ts)

print(f"Human Readable: {dt_obj}")

# --- EXTRA CHALLENGE FOR STUDENTS ---
# How many seconds have passed since the start of this script?
time.sleep(1.5) # Pause for 1.5 seconds
elapsed = time.time() - ts
print(f"Elapsed time: {elapsed:.2f} seconds")
