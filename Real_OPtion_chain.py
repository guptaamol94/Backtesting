import requests
from config import ACCESS_TOKEN

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept"       : "application/json"
}

# ── 5 strikes ke instrument keys (humne pehle dhundhe the) ─
strikes_data = {
    23250: {"CE": "NSE_FO|51337", "PE": "NSE_FO|51338"},
    23300: {"CE": "NSE_FO|51339", "PE": "NSE_FO|51340"},
    23350: {"CE": "NSE_FO|51341", "PE": "NSE_FO|51342"},
    23400: {"CE": "NSE_FO|51343", "PE": "NSE_FO|51344"},
    23450: {"CE": "NSE_FO|51345", "PE": "NSE_FO|51346"},
}

# ── Saari keys ek list mein ───────────────────────────────
all_keys = []
for strike, opts in strikes_data.items():
    all_keys.append(opts["CE"])
    all_keys.append(opts["PE"])

# ── Ek hi call mein sab fetch karo ────────────────────────
url    = "https://api.upstox.com/v2/market-quote/quotes"
params = {"instrument_key": ",".join(all_keys)}

response = requests.get(url, headers=headers, params=params)
data     = response.json()['data']

# ── Table print karo ───────────────────────────────────────
print("=" * 60)
print(f"{'Strike':>8} | {'CE LTP':>8} | {'CE OI':>8} | {'PE LTP':>8} | {'PE OI':>8}")
print("-" * 60)

for strike, opts in strikes_data.items():
    ce_symbol = opts["CE"].replace("NSE_FO|", "NSE_FO:")
    pe_symbol = opts["PE"].replace("NSE_FO|", "NSE_FO:")

    # Data mein symbol naam se key milegi — dhundhna padega
    ce_info = None
    pe_info = None
    for sym, info in data.items():
        if info['instrument_token'] == opts["CE"]:
            ce_info = info
        if info['instrument_token'] == opts["PE"]:
            pe_info = info

    ce_ltp = ce_info['last_price'] if ce_info else "N/A"
    ce_oi  = ce_info['oi']         if ce_info else "N/A"
    pe_ltp = pe_info['last_price'] if pe_info else "N/A"
    pe_oi  = pe_info['oi']         if pe_info else "N/A"

    print(f"{strike:>8} | {str(ce_ltp):>8} | {str(ce_oi):>8} | {str(pe_ltp):>8} | {str(pe_oi):>8}")

print("=" * 60)
# ── PCR aur Support/Resistance ────────────────────────────
total_ce_oi = 0
total_pe_oi = 0
max_ce_oi_strike = None
max_pe_oi_strike = None
max_ce_oi = 0
max_pe_oi = 0

for strike, opts in strikes_data.items():
    for sym, info in data.items():
        if info['instrument_token'] == opts["CE"]:
            oi = info['oi']
            total_ce_oi += oi
            if oi > max_ce_oi:
                max_ce_oi = oi
                max_ce_oi_strike = strike
        if info['instrument_token'] == opts["PE"]:
            oi = info['oi']
            total_pe_oi += oi
            if oi > max_pe_oi:
                max_pe_oi = oi
                max_pe_oi_strike = strike

pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0

print(f"\nTotal CE OI : {total_ce_oi}")
print(f"Total PE OI : {total_pe_oi}")
print(f"PCR         : {pcr:.2f}")

if pcr > 1.2:
    sentiment = "Bearish (lekin bounce possible)"
elif pcr < 0.8:
    sentiment = "Bullish (lekin fall possible)"
else:
    sentiment = "Neutral"

print(f"Sentiment   : {sentiment}")
print(f"\nResistance (Max CE OI) : {max_ce_oi_strike} ({max_ce_oi})")
print(f"Support    (Max PE OI) : {max_pe_oi_strike} ({max_pe_oi})")