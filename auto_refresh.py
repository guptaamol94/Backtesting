import requests
import time
from config import ACCESS_TOKEN

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept"       : "application/json"
}

def get_spot():
    url      = "https://api.upstox.com/v2/market-quote/quotes"
    response = requests.get(url, headers=headers,
                            params={"instrument_key": "NSE_INDEX|Nifty 50"})
    data     = response.json()['data']
    key      = list(data.keys())[0]
    return data[key]['last_price']

def check_market(spot, max_pain, pcr):
    if pcr > 1.2:
        sentiment = "Bearish"
    elif pcr < 0.8:
        sentiment = "Bullish"
    else:
        sentiment = "Neutral"

    distance_pct = (spot - max_pain) / spot * 100

    if distance_pct > 1.5:
        signal = "Neeche aa sakta hai"
    elif distance_pct < -1.5:
        signal = "Upar ja sakta hai"
    else:
        signal = "Range bound"

    return sentiment, signal

# ── Main loop ─────────────────────────────────────────────
MAX_PAIN = 23500   # Manually set karo
PCR      = 0.61    # Manually set karo
CHECK    = 1       # Counter

print("Auto Refresh shuru ho gaya! (Ctrl+C se band karo)")
print("=" * 50)

while True:
    spot = get_spot()
    sentiment, signal = check_market(spot, MAX_PAIN, PCR)

    print(f"\nCheck #{CHECK} — {time.strftime('%H:%M:%S')}")
    print(f"  Spot      : {spot}")
    print(f"  Sentiment : {sentiment}")
    print(f"  Signal    : {signal}")

    CHECK += 1
    time.sleep(300)  # 5 minute = 300 seconds
    