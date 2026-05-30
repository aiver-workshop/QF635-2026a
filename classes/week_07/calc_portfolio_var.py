import numpy as np

# Portfolio weights
w = np.array([0.5, 0.3, 0.2])

# Covariance matrix
cov_matrix = np.array([
    [0.040, 0.012, 0.008],
    [0.012, 0.090, 0.018],
    [0.008, 0.018, 0.160]
])

# Portfolio value
portfolio_value = 100_000_000   # $100 million

# 95% Z-score
z_95 = 1.65

# Portfolio variance
portfolio_variance = w.T @ cov_matrix @ w

# Portfolio standard deviation
portfolio_std = np.sqrt(portfolio_variance)

# 1-Day 95% VaR
var_95 = z_95 * portfolio_std * portfolio_value

print(f"Portfolio Variance: {portfolio_variance:.5f}")
print(f"Portfolio Standard Deviation: {portfolio_std:.4f} ({portfolio_std*100:.2f}%)")
print(f"1-Day 95% VaR: ${var_95:,.0f}")