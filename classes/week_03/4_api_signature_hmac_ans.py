"""
TOPIC: API Authentication and HMAC Signing
REFERENCE: https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info

KEY TEACHING POINTS:
1. Message Integrity: Signing ensures that the order details (price, quantity)
   haven't been tampered with during transit.
2. HMAC SHA256: A cryptographic hash function that combines a secret key
   with a message string to produce a unique, 64-character hex signature.
3. urlencode: Standardizes the order of parameters. Changing the order
   of parameters after signing will result in an invalid signature.
4. Binary Encoding: 'hmac' requires data in bytes. We use '.encode("utf-8")'
   to convert our strings into a format the crypto library understands.
"""
import hmac
import hashlib
from urllib.parse import urlencode

# 1. Credentials (Teaching Note: In production, load these from your vault!)
api_secret = '2b5eb11e18796d12d88f13dc27dbbd02c2cc51ff7059765ed9821957d82bb4d9'

# 2. Define the Order Parameters
# Parameters must include a 'timestamp' in milliseconds
params = {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "LIMIT",
    "quantity": 1,
    "price": "9000",
    "timeInForce": "GTC",
    "recvWindow": 5000,
    "timestamp": 1591702613943
}

# 3. Create the Query String
# This joins the dict into: symbol=BTCUSDT&side=BUY...
query_string = urlencode(params)
print(f"Payload for Signing: {query_string}")

# 4. Generate the HMAC SHA256 Signature
# We hash the query_string using the api_secret as the key
signature = hmac.new(
    api_secret.encode("utf-8"),
    query_string.encode("utf-8"),
    hashlib.sha256
).hexdigest()

print(f"Generated Signature: {signature}")

# 5. Validation Check
expected = '3c661234138461fcc7a7d8746c6558c9842d4e10870d2ecbedf7777cad694af9'
if signature == expected:
    print("✅ Signature Match! Ready to send to Exchange.")
else:
    print("❌ Signature Mismatch. Check your encoding or secret.")


