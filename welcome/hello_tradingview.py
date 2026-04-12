"""
Using a community-built Python library: https://github.com/shner-elmo/TradingView-Screener
"""

from tradingview_screener import Query, col

# 1. Unpack the tuple into two variables (count and df)
count, df = (Query()
             .select('name', 'close')
             .where(col('name') == 'NVDA')
             .get_scanner_data())

# 2. Access the 'close' column for the first row (index 0)
if not df.empty:
    price = df['close'].iloc[0]
    print(f"NVIDIA Close Price: ${price:.2f}")
else:
    print("No data found.")
