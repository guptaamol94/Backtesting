import time

def check_market(spot, max_pain, pcr):
    
    # PCR check
    if pcr > 1.2:
        sentiment = "Bearish"
    elif pcr < 0.8:
        sentiment = "Bullish"
    else:
        sentiment = "Neutral"
    
    # Max Pain distance
    distance = spot - max_pain
    distance_pct = (distance / spot) * 100
    
    if distance_pct > 1.5:
        signal = "Neeche aa sakta hai"
    elif distance_pct < -1.5:
        signal = "Upar ja sakta hai"
    else:
        signal = "Range bound"
    
    return sentiment, signal

# ── Simulate karo 3 baar ─────────────────────────────────
spots = [23500, 23600, 23700]

for i, spot in enumerate(spots):
    sentiment, signal = check_market(spot, 23500, 0.61)
    print(f"Check {i+1}:")
    print(f"  Spot      : {spot}")
    print(f"  Sentiment : {sentiment}")
    print(f"  Signal    : {signal}")
    print()
    time.sleep(1)