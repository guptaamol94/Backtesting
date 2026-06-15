# ── If/Else — condition pe decision ──────────────────────
import sys
sys.stdout.reconfigure(encoding='utf-8')

spot      = 23622.9
max_pain  = 23500.0
pcr       = 0.61

# ── PCR Analysis ─────────────────────────────────────────
print("PCR Analysis:")
if pcr > 1.2:
    print("  Bearish — Puts zyada hain")
elif pcr > 0.8:
    print("  Neutral — Balanced market")
else:
    print("  Bullish — Calls zyada hain")

# ── Max Pain Analysis ─────────────────────────────────────
distance     = spot - max_pain
distance_pct = (distance / spot) * 100

print(f"\nMax Pain Analysis:")
print(f"  Distance: {distance:.0f} pts ({distance_pct:.2f}%)")

if distance_pct > 1.5:
    signal   = "BEARISH — Neeche aa sakta hai"
    strategy = "CE Sell ya Bear Spread"
elif distance_pct < -1.5:
    signal   = "BULLISH — Upar ja sakta hai"
    strategy = "PE Sell ya Bull Spread"
else:
    signal   = "RANGE BOUND"
    strategy = "Straddle ya Strangle Sell"

print(f"  Signal  : {signal}")
print(f"  Strategy: {strategy}")

# ── Stop Loss Check ───────────────────────────────────────
entry_price  = 23500
current      = 23622.9
sl_pct       = 0.006
target_pct   = 0.012

sl     = entry_price - (entry_price * sl_pct)
target = entry_price + (entry_price * target_pct)
change = (current - entry_price) / entry_price * 100

print(f"\nTrade Status:")
print(f"  Entry  : {entry_price}")
print(f"  Current: {current}")
print(f"  SL     : {sl:.0f}")
print(f"  Target : {target:.0f}")
print(f"  Change : {change:.2f}%")

if current <= sl:
    print("  Status : STOP LOSS HIT ❌")
elif current >= target:
    print("  Status : TARGET HIT ✅")
else:
    print("  Status : TRADE OPEN (Open)")