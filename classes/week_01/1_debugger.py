"""
Exercise: Debugging with Breakpoints
1. Set a breakpoint on line 11 (a = 5).
2. Step through line-by-line using 'Step Over'.
3. Watch the 'Variables' window to see 'c' and 'd' update.
4. Highlight 'ln(2 * 5)' and right-click to 'Evaluate Expression'.
"""

from numpy import log as ln  # Creating a math-friendly alias

a = 5
b = 8
c = a + b
d = 5 * c
print(f'd is {d}')  # Modern f-string syntax

n1 = ln(2)
n2 = ln(5)

print(f'ln(2) is {n1:.4f}')
print(f'ln(5) is {n2:.4f}')

# Does ln(2) + ln(5) equal ln(10)?
sum_logs = n1 + n2
log_product = ln(2 * 5)

print(f'Sum: {sum_logs:.4f}')
print(f'Product Log: {log_product:.4f}')

# Challenge: Can you evaluate if (sum_logs == log_product) in the Debug Console?
