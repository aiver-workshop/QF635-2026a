"""
LESSON: The Call Stack (The "Trail of Crumbs")
Goal: Understand how Python remembers its way back home after calling a function.

Mission:
1. Set a breakpoint on 'print("chopping")'.
2. Open the 'Call Stack' or 'Frames' window in your debugger.
3. Observe how the stack grows as dinner -> cook -> chop.
4. Use 'Step Out' to see how each function is "popped" off the stack.
"""


def chop():
    # --- BREAKPOINT HERE ---
    print("Step 3: Chopping the ingredients...")


def cook():
    print("Step 2: Preparing to cook...")
    chop()
    print("Step 4: Everything is cooked!")


def dinner():
    print("Step 1: Starting the dinner process...")
    cook()
    print("Step 5: Dinner is served.")


if __name__ == '__main__':
    # This is where the stack starts
    dinner()
