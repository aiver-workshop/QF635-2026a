"""
LESSON: Debugging a Loop
Goal: Watch the 'Total' accumulate in the Variables View.

Step-by-Step:
1. Set a breakpoint on 'a = 1'.
2. Click 'Step Over' repeatedly.
3. Observe how 'a' increases and 'total' grows each time the loop restarts.
4. Try to 'Evaluate Expression' on 'a * a' before the line executes.
"""

a = 1
total = 0
limit = 10

while a < limit:
    b = a * a
    total = total + b

    # CRITICAL STEP: Incrementing the counter
    a = a + 1

# Why is the total different from expected sum of 385?
print(f'The sum of squares from 1 to {limit} is: {total}')