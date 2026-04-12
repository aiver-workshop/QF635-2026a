"""
Running your first program

"""
import time


def print_christmas_tree(height):
    row = 0
    # The loop runs until it reaches the specified height
    while row < height:
        # Calculate spaces to center the stars
        spaces = " " * (height - row - 1)
        # Calculate stars (odd numbers: 1, 3, 5...)
        stars = "*" * (2 * row + 1)

        print(spaces + stars)
        row += 1

        time.sleep(1)

    # Print the trunk at the very end
    trunk_spaces = " " * (height - 1)
    print(trunk_spaces + "|")


print('Welcome to QF635: Market Microstructure & Algorithmic Trading')
print_christmas_tree(10)
