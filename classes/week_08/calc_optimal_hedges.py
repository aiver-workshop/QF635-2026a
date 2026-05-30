import numpy as np
import pandas as pd

# ---------------------------------------------------
# Portfolio setup
# ---------------------------------------------------

# Portfolio weights
w = np.array([0.5, 0.3, 0.2])

# Covariance matrix
Sigma = np.array([
    [0.040, 0.012, 0.008],
    [0.012, 0.090, 0.018],
    [0.008, 0.018, 0.160]
])

# Portfolio variance
portfolio_variance = w.T @ Sigma @ w

print(f"Portfolio Variance = {portfolio_variance:.6f}")
print()

# ---------------------------------------------------
# Compute hedge statistics for each asset
# ---------------------------------------------------

results = []

n_assets = len(w)

for i in range(n_assets):

    # Basis vector e_i
    e_i = np.zeros(n_assets)
    e_i[i] = 1.0

    # Cov(P, H_i)
    cov_PH = w.T @ Sigma @ e_i

    # Var(H_i)
    var_H = Sigma[i, i]

    # Optimal hedge size
    b_star = -cov_PH / var_H

    # Variance reduction
    variance_reduction = (cov_PH ** 2) / var_H

    # Hedge score
    hedge_score = variance_reduction / var_H

    # Hedged portfolio variance
    hedged_variance = portfolio_variance - variance_reduction

    results.append([
        f"Asset {i+1}",
        cov_PH,
        var_H,
        b_star,
        variance_reduction,
        hedge_score,
        hedged_variance
    ])

# ---------------------------------------------------
# Display results
# ---------------------------------------------------

columns = [
    "Asset",
    "Cov(P,H)",
    "Var(H)",
    "Optimal Hedge b*",
    "Variance Reduction",
    "Hedge Score",
    "Hedged Variance"
]

df = pd.DataFrame(results, columns=columns)

# Format output
pd.set_option("display.float_format", "{:.6f}".format)

print(df)