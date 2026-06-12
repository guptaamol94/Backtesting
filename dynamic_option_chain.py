import requests
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from datetime import datetime
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

# ── Step 9: Max Pain Calculator ──────────────────────────
print("\n" + "=" * 70)
print("  MAX PAIN CALCULATION")
print("=" * 70)

max_pain_data = {}

for test_strike in nearby:
    total_pain = 0
    for strike in nearby:
        if strike in calls:
            ce_info = get_info(calls[strike]['instrument_key'])
            ce_oi   = ce_info['oi'] if ce_info else 0
            if test_strike > strike:
                total_pain += (test_strike - strike) * ce_oi
        if strike in puts:
            pe_info = get_info(puts[strike]['instrument_key'])
            pe_oi   = pe_info['oi'] if pe_info else 0
            if test_strike < strike:
                total_pain += (strike - test_strike) * pe_oi
    max_pain_data[test_strike] = total_pain

max_pain_strike = min(max_pain_data, key=max_pain_data.get)

print(f"\n{'Strike':>8} | {'Total Pain':>15}")
print("-" * 30)
for strike, pain in max_pain_data.items():
    tag = " <- MAX PAIN" if strike == max_pain_strike else ""
    print(f"{strike:>8.0f} | {pain:>15,.0f}{tag}")

print("=" * 70)
print(f"\nMax Pain Strike : {max_pain_strike}")
print(f"Current Spot    : {spot}")

distance     = spot - max_pain_strike
distance_pct = (distance / spot) * 100

print(f"Distance        : {distance:.0f} points ({distance_pct:+.2f}%)")

if distance_pct > 1:
    print("Signal          : Spot Max Pain se UPAR — neeche pull possible")
elif distance_pct < -1:
    print("Signal          : Spot Max Pain se NEECHE — upar push possible")
else:
    print("Signal          : Spot Max Pain ke PAAS — range bound likely")

# ── Step 10: IV Calculator (Black-Scholes) ───────────────
print("\n" + "=" * 70)
print("  IMPLIED VOLATILITY (IV)")
print("=" * 70)

expiry_date = datetime.strptime(EXPIRY, "%Y-%m-%d")
today       = datetime.now()
T = (expiry_date - today).days / 365
if T <= 0:
    T = 1/365

R = 0.065

def bs_price(S, K, T, r, sigma, option_type):
    d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    if option_type == 'CE':
        return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
    else:
        return K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)

def calculate_iv(market_price, S, K, T, r, option_type):
    if market_price <= 0:
        return 0
    try:
        iv = brentq(
            lambda sigma: bs_price(S, K, T, r, sigma, option_type) - market_price,
            0.001, 5.0
        )
        return iv * 100
    except:
        return 0

print(f"\nTime to Expiry  : {T*365:.1f} days")
print(f"\n{'Strike':>8} | {'CE LTP':>8} | {'CE IV%':>8} | {'PE LTP':>8} | {'PE IV%':>8}")
print("-" * 70)

for strike in nearby:
    ce_info = get_info(calls[strike]['instrument_key']) if strike in calls else None
    pe_info = get_info(puts[strike]['instrument_key'])  if strike in puts  else None

    ce_ltp = ce_info['last_price'] if ce_info else 0
    pe_ltp = pe_info['last_price'] if pe_info else 0

    ce_iv = calculate_iv(ce_ltp, spot, strike, T, R, 'CE') if ce_ltp > 0 else 0
    pe_iv = calculate_iv(pe_ltp, spot, strike, T, R, 'PE') if pe_ltp > 0 else 0

    atm_tag = " <- ATM" if strike == atm_strike else ""
    print(f"{strike:>8.0f} | {ce_ltp:>8} | {ce_iv:>7.1f}% | {pe_ltp:>8} | {pe_iv:>7.1f}%{atm_tag}")

print("=" * 70)