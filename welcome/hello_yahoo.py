import yfinance as yf
import requests

# 1. Create a "Session" to look like a real browser
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

ticker_symbol = "NVDA"

# 2. Pass the session into the Ticker object
nvda_data = yf.Ticker(ticker_symbol, session=session)

# 3. Fetch data
try:
    history = nvda_data.history(period="1d")
    if not history.empty:
        current_price = history['Close'].iloc[-1]
        print(f"The latest daily closing price for NVIDIA ({ticker_symbol}) is: ${current_price:.2f}")
    else:
        print("No data found. The market might be closed or the limit is still active.")
except Exception as e:
    print(f"An error occurred: {e}")
