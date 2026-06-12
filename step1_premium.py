import requests
from config import ACCESS_TOKEN

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept"       : "application/json"
}

ce_key = "NSE_FO|51341"   # 23350 CE
pe_key = "NSE_FO|51342"   # 23350 PE

url    = "https://api.upstox.com/v2/market-quote/quotes"
params = {"instrument_key": f"{ce_key},{pe_key}"}

response = requests.get(url, headers=headers, params=params)
data     = response.json()['data']

# ── Clean Output ──────────────────────────────────────────
print("=" * 50)
print("   NIFTY 23350 — ATM Option Data")
print("=" * 50)

for symbol, info in data.items():
    option_type = "CALL (CE)" if "CE" in symbol else "PUT (PE)"
    
    print(f"\n{option_type}")
    print(f"  Symbol      : {symbol}")
    print(f"  LTP         : Rs. {info['last_price']}")
    print(f"  Open        : Rs. {info['ohlc']['open']}")
    print(f"  High        : Rs. {info['ohlc']['high']}")
    print(f"  Low         : Rs. {info['ohlc']['low']}")
    print(f"  OI          : {info['oi']}")
    print(f"  Volume      : {info['volume']}")
    print(f"  Net Change  : {info['net_change']}")
    
    best_bid = info['depth']['buy'][0]['price']
    best_ask = info['depth']['sell'][0]['price']
    print(f"  Best Bid    : Rs. {best_bid}")
    print(f"  Best Ask    : Rs. {best_ask}")

print("\n" + "=" * 50)