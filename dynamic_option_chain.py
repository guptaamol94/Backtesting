import requests
from config import ACCESS_TOKEN

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept"       : "application/json"
}

# ── SETTINGS ──────────────────────────────────────────────
UNDERLYING_KEY = "NSE_INDEX|Nifty 50"
EXPIRY         = "2026-07-14"
NUM_STRIKES    = 5

# ── Step 1: Spot price ────────────────────────────────────
quote_url = "https://api.upstox.com/v2/market-quote/quotes"
spot_resp = requests.get(quote_url, headers=headers, params={"instrument_key": UNDERLYING_KEY})
spot_data = spot_resp.json()['data']
spot_key  = list(spot_data.keys())[0]
spot      = spot_data[spot_key]['last_price']

print(f"Spot Price: {spot}")

# ── Step 2: Contracts ─────────────────────────────────────
contract_url  = "https://api.upstox.com/v2/option/contract"
contract_resp = requests.get(contract_url, headers=headers, params={"instrument_key": UNDERLYING_KEY})
contracts = contract_resp.json()['data']

# ── Step 3: Filter ─────────────────────────────────────────
filtered = [c for c in contracts if c['expiry'] == EXPIRY]
calls    = {c['strike_price']: c for c in filtered if c['instrument_type'] == 'CE'}
puts     = {c['strike_price']: c for c in filtered if c['instrument_type'] == 'PE'}
strikes  = sorted(set(calls.keys()) & set(puts.keys()))

# ── Step 4: ATM ──────────────────────────────────────────
atm_strike = min(strikes, key=lambda x: abs(x - spot))
atm_index  = strikes.index(atm_strike)
nearby     = strikes[max(0, atm_index-NUM_STRIKES) : atm_index+NUM_STRIKES+1]

print(f"ATM Strike: {atm_strike}")
print(f"Strikes selected: {nearby}\n")

# ── Step 5: Keys collect ──────────────────────────────────
all_keys = []
for strike in nearby:
    if strike in calls: all_keys.append(calls[strike]['instrument_key'])
    if strike in puts:  all_keys.append(puts[strike]['instrument_key'])

# ── Step 6: Live data ──────────────────────────────────────
data_resp  = requests.get(quote_url, headers=headers, params={"instrument_key": ",".join(all_keys)})
quote_data = data_resp.json()['data']

def get_info(instrument_key):
    for sym, info in quote_data.items():
        if info['instrument_token'] == instrument_key:
            return info
    return None

# ── Step 7: Table ────────────────────────────────────────
print("=" * 70)
print(f"  OPTION CHAIN — {UNDERLYING_KEY}  |  Expiry: {EXPIRY}")
print(f"  Spot: {spot}  |  ATM: {atm_strike}")
print("=" * 70)
print(f"{'Strike':>8} | {'CE LTP':>8} | {'CE OI':>8} | {'PE LTP':>8} | {'PE OI':>8}")
print("-" * 70)

total_ce_oi = 0
total_pe_oi = 0
max_ce_oi_strike = max_pe_oi_strike = None
max_ce_oi = max_pe_oi = 0

for strike in nearby:
    ce_info = get_info(calls[strike]['instrument_key']) if strike in calls else None
    pe_info = get_info(puts[strike]['instrument_key'])  if strike in puts  else None

    ce_ltp = ce_info['last_price'] if ce_info else 0
    ce_oi  = ce_info['oi']         if ce_info else 0
    pe_ltp = pe_info['last_price'] if pe_info else 0
    pe_oi  = pe_info['oi']         if pe_info else 0

    total_ce_oi += ce_oi
    total_pe_oi += pe_oi

    if ce_oi > max_ce_oi:
        max_ce_oi, max_ce_oi_strike = ce_oi, strike
    if pe_oi > max_pe_oi:
        max_pe_oi, max_pe_oi_strike = pe_oi, strike

    atm_tag = " <- ATM" if strike == atm_strike else ""
    print(f"{strike:>8.0f} | {ce_ltp:>8} | {ce_oi:>8} | {pe_ltp:>8} | {pe_oi:>8}{atm_tag}")

print("=" * 70)

# ── Step 8: PCR + Support/Resistance ──────────────────────
pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0

if pcr > 1.2:
    sentiment = "Bearish (bounce possible)"
elif pcr < 0.8:
    sentiment = "Bullish (fall possible)"
else:
    sentiment = "Neutral"

print(f"\nTotal CE OI : {total_ce_oi}")
print(f"Total PE OI : {total_pe_oi}")
print(f"PCR         : {pcr:.2f}")
print(f"Sentiment   : {sentiment}")
print(f"\nResistance (Max CE OI) : {max_ce_oi_strike} ({max_ce_oi})")
print(f"Support    (Max PE OI) : {max_pe_oi_strike} ({max_pe_oi})")