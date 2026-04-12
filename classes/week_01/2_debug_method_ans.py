"""
The Monotonicity Mystery
"""


# This function checks if a list of numbers is monotonic increasing or decreasing
def mysterious_method(nums: [float]) -> bool:
    a = []  # Stores True if current element <= next element
    b = []  # Stores True if current element >= next element

    # iterate over the list, starting from first element
    for i in range(len(nums) - 1):
        # monotone increasing check: i.e. this element equal or larger than next element
        a.append(nums[i] <= nums[i + 1])

        # monotone decreasing check: i.e. this element equal or smaller than next element
        b.append(nums[i] >= nums[i + 1])

    # If the entire list 'a' is True, it's non-decreasing.
    # If the entire list 'b' is True, it's non-increasing.
    # return true if either monotone increasing or decreasing; false otherwise
    return all(a) or all(b)


# The "Pro" One-Liner
def is_monotonic(nums: list[float]) -> bool:
    # This does exactly what your loop does, but in one line!
    return all(nums[i] <= nums[i+1] for i in range(len(nums)-1)) or \
           all(nums[i] >= nums[i+1] for i in range(len(nums)-1))


# Entry point where execution enters the program.
if __name__ == '__main__':
    x = [6, 5, 4, 4]
    y = [1, 1, 1, 3, 3, 4, 3, 2, 4, 2]
    z = [1, 1, 2, 3, 7]

    result_x = mysterious_method(x)
    result_y = mysterious_method(y)
    result_z = mysterious_method(z)

    print(result_x)
    print(result_y)
    print(result_z)


