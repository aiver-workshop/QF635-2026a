"""
TOPIC: Iterating Through Multi-Asset Account Balances
REFERENCE: https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Futures-Account-Balance-V2

KEY TEACHING POINTS:
1. Data Structures: The API returns a list of dictionaries. Each dictionary
   is a "row" containing data for one specific asset.
2. List Iteration: Use a 'for' loop to step through every asset in the account.
3. Formatting: Professional logs use padding (e.g., :8) to ensure columns
   align vertically, making the output easier to read.
4. Filtering: You can use a conditional (if) inside the loop to skip
   assets with a zero balance to reduce "noise" in your logs.
"""

import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

# 1. Configuration (Use your Testnet Keys)
API_KEY = 'CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz'
API_SECRET = 'cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC'
BASE_URL = 'https://testnet.binancefuture.com'
BALANCE_PATH = '/fapi/v2/balance'


def get_signature(params: dict, secret: str) -> str:
    query_string = urlencode(params)
    return hmac.new(
        secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def print_all_balances():
    # Setup parameters and signature
    params = {
        "timestamp": int(time.time() * 1000),
        "recvWindow": 5000
    }

    sig = get_signature(params, API_SECRET)
    url = f"{BASE_URL}{BALANCE_PATH}?{urlencode(params)}&signature={sig}"
    headers = {"X-MBX-APIKEY": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        asset_list = response.json()

        print(f"{'ASSET':<8} | {'BALANCE':<15} | {'WITHDRAWABLE':<15}")
        print("-" * 45)

        for item in asset_list:
            asset = item['asset']
            balance = float(item['balance'])
            withdrawable = float(item['availableBalance'])

            # Only print assets where you actually have a balance (optional filter)
            if balance > 0:
                print(f"{asset:<8} | {balance:<15,.4f} | {withdrawable:<15,.4f}")

    except Exception as e:
        print(f"Error fetching account data: {e}")


if __name__ == '__main__':
    print_all_balances()
