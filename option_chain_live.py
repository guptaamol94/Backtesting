import requests
from config import ACCESS_TOKEN

EXPIRY = "2026-07-14"
SPOT   = 23345
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}

contracts = requests.get("https://api.upstox.com/v2/option/contract",
    headers=headers, params={"instrument_key": "NSE_INDEX|Nifty 50"}).json()["data"]

filtered = [c for c in contracts if c["expiry"] == EXPIRY]
calls    = {c["strike_price"]: c for c in filtered if c["instrument_type"] == "CE"}
puts     = {c["strike_price"]: c for c in filtered if c["instrument_type"] == "PE"}
strikes  = sorted(set(calls.keys()) & set(puts.keys()))
atm      = min(strikes, key=lambda x: abs(x - SPOT))
atm_idx  = strikes.index(atm)
nearby   = strikes[max(0, atm_idx-5): atm_idx+6]
lot_size = filtered[0]["lot_size"]

keys = []
for s in nearby:
    if s in calls: keys.append(calls[s]["instrument_key"])
    if s in puts:  keys.append(puts[s]["instrument_key"])

q_data = requests.get("https://api.upstox.com/v2/market-quote/quotes",
    headers=headers, params={"instrument_key": ",".join(keys)}).json().get("data", {})

token_map = {q["instrument_token"]: q for q in q_data.values()}

def get_price(key):
    q = token_map.get(key, {})
    if not q: return 0
    ltp = q.get("last_price", 0)
    if ltp == 0:
        buys  = q.get("depth", {}).get("buy", [])
        sells = q.get("depth", {}).get("sell", [])
        b = buys[0]["price"]  if buys  else 0
        a = sells[0]["price"] if sells else 0
        ltp = round((b + a) / 2, 2) if b and a else (b or a)
    return ltp

print("=" * 65)
print(f"  NIFTY CHAIN | Spot: {SPOT} | ATM: {atm} | Lot: {lot_size}")
print(f"  Expiry: {EXPIRY} | Market band = Bid/Ask Mid")
print("=" * 65)
print(f"  {'Strike':>8} | {'CE':>10} | {'PE':>10} | {'Straddle':>10}")
print("-" * 65)

for s in nearby:
    ce = get_price(calls[s]["instrument_key"]) if s in calls else 0
    pe = get_price(puts[s]["instrument_key"])  if s in puts  else 0
    tag = " ATM" if s == atm else ""
    print(f"  {s:>8.0f} | {ce:>10.2f} | {pe:>10.2f} | {ce+pe:>10.2f}{tag}")

print("=" * 65)
ce_atm = get_price(calls[atm]["instrument_key"])
pe_atm = get_price(puts[atm]["instrument_key"])
total  = ce_atm + pe_atm
cost   = total * lot_size
print(f"  ATM Straddle : {ce_atm:.2f} + {pe_atm:.2f} = {total:.2f}")
print(f"  Cost per lot : Rs. {cost:,.0f}")