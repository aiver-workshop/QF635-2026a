"""
EXERCISE: By using an AI assistant, learn how to simulate stock prices using a Geometric Brownian Model.

"""

import numpy as np
import matplotlib.pyplot as plt

# Parameters
S0 = 100          # initial stock price
mu = 0.1          # expected return (drift)
sigma = 0.2       # volatility
T = 1.0           # total time in years
N = 252           # number of time steps
dt = T / N        # time step
t = np.linspace(0, T, N)

# Prepare the array
S = [S0]

# Random seed for reproducibility
np.random.seed(42)

# Iterative simulation (discrete time version)
for i in range(1, N):
    Z = np.random.normal(0, 1)  # standard normal random variable
    dS = S[-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)
    S.append(dS)

# Plot the result
plt.plot(t, S)
plt.title("Iterative Geometric Brownian Motion Simulation")
plt.xlabel("Time (years)")
plt.ylabel("Stock Price")
plt.grid(True)
plt.show()
