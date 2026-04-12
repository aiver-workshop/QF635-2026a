"""
Goal: Use the debugger to uncover the hidden logic of this function.

Mission:
1. Set a breakpoint on the first line of 'mysterious_method'.
2. Use 'Step Over' to watch list 'a' and 'b' grow.
3. When the loop finishes, highlight 'all(a)' -> Right Click -> 'Evaluate Expression'.
4. Document the function: Replace the docstring with what you discovered.
"""


def mysterious_method(nums: [float]) -> bool:
    """
        TODO: Students should try to discover the purpose of a and b variables
        (e.g., what does true or false means?)
    """
    a = []
    b = []
    for i in range(len(nums) - 1):
        a.append(nums[i] <= nums[i + 1])
        b.append(nums[i] >= nums[i + 1])

    return all(a) or all(b)


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
