import requests
import json
from config import ACCESS_TOKEN

# ── Settings ──────────────────────────────────────────────
EXPIRY    = "2026-07-14"
SPOT      = 23345  # Approximate Nifty spot

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept"       : "application/json"
}

# ── Step 1: Contracts fetch karo ──────────────────────────
url    = "https://api.upstox.com/v2/option/contract"
params = {"instrument_key": "NSE_INDEX|Nifty 50"}

response = requests.get(url, headers=headers, params=params)
data     = response.json()
contracts = data['data']

# ── Step 2: Expiry filter karo ────────────────────────────
filtered = [c for c in contracts if c['expiry'] == EXPIRY]

# CE aur PE alag karo
calls = {c['strike_price']: c for c in filtered if c['instrument_type'] == 'CE'}
puts  = {c['strike_price']: c for c in filtered if c['instrument_type'] == 'PE'}

# Common strikes
strikes = sorted(set(calls.keys()) & set(puts.keys()))

# ── Step 3: ATM ke aas paas strikes dhundho ───────────────
atm_strike = min(strikes, key=lambda x: abs(x - SPOT))
atm_index  = strikes.index(atm_strike)

# ATM ke 5 upar aur 5 neeche
nearby_strikes = strikes[max(0, atm_index-5) : atm_index+6]

print("=" * 65)
print(f"  NIFTY OPTION CHAIN — Expiry: {EXPIRY}")
print(f"  Spot: {SPOT}  |  ATM Strike: {atm_strike}")
print("=" * 65)
print(f"{'Strike':>10} | {'CE Key':>20} | {'PE Key':>20}")
print("-" * 65)

for strike in nearby_strikes:
    ce_key = calls[strike]['instrument_key'] if strike in calls else "N/A"
    pe_key = puts[strike]['instrument_key']  if strike in puts  else "N/A"
    atm    = " ← ATM" if strike == atm_strike else ""
    print(f"{strike:>10.0f} | {ce_key:>20} | {pe_key:>20}{atm}")

print("=" * 65)
print(f"\nTotal CE strikes : {len(calls)}")
print(f"Total PE strikes : {len(puts)}")
print(f"ATM Strike       : {atm_strike}")
print(f"Lot Size         : {filtered[0]['lot_size']}")