import requests
import json

# Config import
from config import ACCESS_TOKEN

# Nifty 50 ka latest market data fetch karo
url = "https://api.upstox.com/v2/market-quote/quotes"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json"
}

params = {
    "instrument_key": "NSE_INDEX|Nifty 50"
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print("Status:", response.status_code)
print(json.dumps(data, indent=2))