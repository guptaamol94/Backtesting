import time
import requests
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from datetime import datetime
from config import ACCESS_TOKEN, BOT_TOKEN, CHAT_ID

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept"       : "application/json"
}

UNDERLYING_KEY = "NSE_INDEX|Nifty 50"
EXPIRY         = "2026-07-14"
NUM_STRIKES    = 5

def get_info(instrument_key, quote_data):
    for sym, info in quote_data.items():
        if info['instrument_token'] == instrument_key:
            return info
    return None

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

def calculate_greeks(S, K, T, r, sigma, option_type):
    if sigma <= 0 or T <= 0:
        return 0, 0, 0, 0
    d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    if option_type == 'CE':
        delta = norm.cdf(d1)
    else:
        delta = norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    if option_type == 'CE':
        theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365
    else:
        theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(-d2)) / 365
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100
    return delta, gamma, theta, vega

def send_telegram(message):
    url     = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

# ── Main Loop — har 15 min ────────────────────────────────
print("Auto Refresh shuru! Ctrl+C se band karo.")

while True:
    try:
        # Step 1: Spot
        quote_url = "https://api.upstox.com/v2/market-quote/quotes"
        spot_resp = requests.get(quote_url, headers=headers, params={"instrument_key": UNDERLYING_KEY})
        spot_data = spot_resp.json()['data']
        spot_key  = list(spot_data.keys())[0]
        spot      = spot_data[spot_key]['last_price']

        # Step 2: Contracts
        contract_url  = "https://api.upstox.com/v2/option/contract"
        contract_resp = requests.get(contract_url, headers=headers, params={"instrument_key": UNDERLYING_KEY})
        contracts     = contract_resp.json()['data']

        # Step 3: Filter
        filtered = [c for c in contracts if c['expiry'] == EXPIRY]
        calls    = {c['strike_price']: c for c in filtered if c['instrument_type'] == 'CE'}
        puts     = {c['strike_price']: c for c in filtered if c['instrument_type'] == 'PE'}
        strikes  = sorted(set(calls.keys()) & set(puts.keys()))

        # Step 4: ATM
        atm_strike = min(strikes, key=lambda x: abs(x - spot))
        atm_index  = strikes.index(atm_strike)
        nearby     = strikes[max(0, atm_index-NUM_STRIKES) : atm_index+NUM_STRIKES+1]

        # Step 5: Keys
        all_keys = []
        for strike in nearby:
            if strike in calls: all_keys.append(calls[strike]['instrument_key'])
            if strike in puts:  all_keys.append(puts[strike]['instrument_key'])

        # Step 6: Live data
        data_resp  = requests.get(quote_url, headers=headers, params={"instrument_key": ",".join(all_keys)})
        quote_data = data_resp.json()['data']

        # Step 7: OI
        total_ce_oi = total_pe_oi = 0
        max_ce_oi = max_pe_oi = 0
        max_ce_oi_strike = max_pe_oi_strike = None

        for strike in nearby:
            ce_info = get_info(calls[strike]['instrument_key'], quote_data) if strike in calls else None
            pe_info = get_info(puts[strike]['instrument_key'],  quote_data) if strike in puts  else None
            ce_oi   = ce_info['oi'] if ce_info else 0
            pe_oi   = pe_info['oi'] if pe_info else 0
            total_ce_oi += ce_oi
            total_pe_oi += pe_oi
            if ce_oi > max_ce_oi: max_ce_oi, max_ce_oi_strike = ce_oi, strike
            if pe_oi > max_pe_oi: max_pe_oi, max_pe_oi_strike = pe_oi, strike

        # Step 8: PCR
        pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
        if pcr > 1.2:   sentiment = "Bearish"
        elif pcr < 0.8: sentiment = "Bullish"
        else:           sentiment = "Neutral"

        # Step 9: Max Pain
        max_pain_data = {}
        for test_strike in nearby:
            total_pain = 0
            for strike in nearby:
                if strike in calls:
                    ce_info = get_info(calls[strike]['instrument_key'], quote_data)
                    ce_oi   = ce_info['oi'] if ce_info else 0
                    if test_strike > strike: total_pain += (test_strike - strike) * ce_oi
                if strike in puts:
                    pe_info = get_info(puts[strike]['instrument_key'], quote_data)
                    pe_oi   = pe_info['oi'] if pe_info else 0
                    if test_strike < strike: total_pain += (strike - test_strike) * pe_oi
            max_pain_data[test_strike] = total_pain

        max_pain_strike = min(max_pain_data, key=max_pain_data.get)
        distance        = spot - max_pain_strike
        distance_pct    = (distance / spot) * 100

        # Step 10: IV
        expiry_date = datetime.strptime(EXPIRY, "%Y-%m-%d")
        T = max((expiry_date - datetime.now()).days / 365, 1/365)
        R = 0.065

        # Step 11: ATM IV
        atm_ce_ltp = atm_pe_ltp = atm_ce_iv = atm_pe_iv = 0
        for strike in nearby:
            if strike == atm_strike:
                ce_info    = get_info(calls[strike]['instrument_key'], quote_data) if strike in calls else None
                pe_info    = get_info(puts[strike]['instrument_key'],  quote_data) if strike in puts  else None
                atm_ce_ltp = ce_info['last_price'] if ce_info else 0
                atm_pe_ltp = pe_info['last_price'] if pe_info else 0
                atm_ce_iv  = calculate_iv(atm_ce_ltp, spot, strike, T, R, 'CE')
                atm_pe_iv  = calculate_iv(atm_pe_ltp, spot, strike, T, R, 'PE')

        # Step 12: Telegram
        if distance_pct > 1:   signal = "Spot Max Pain se UPAR"
        elif distance_pct < -1: signal = "Spot Max Pain se NEECHE"
        else:                   signal = "Max Pain ke PAAS — Range Bound"

        message = f"""
<b>NIFTY OPTION CHAIN ALERT</b>
<b>Time       :</b> {datetime.now().strftime('%H:%M:%S')}
<b>Spot       :</b> {spot}
<b>ATM Strike :</b> {atm_strike}
<b>Max Pain   :</b> {max_pain_strike}
<b>Distance   :</b> {distance:.0f} pts ({distance_pct:+.2f}%)
<b>PCR        :</b> {pcr:.2f} — {sentiment}
<b>Resistance :</b> {max_ce_oi_strike} (OI: {max_ce_oi})
<b>Support    :</b> {max_pe_oi_strike} (OI: {max_pe_oi})
<b>ATM CE LTP :</b> {atm_ce_ltp} | IV: {atm_ce_iv:.1f}%
<b>ATM PE LTP :</b> {atm_pe_ltp} | IV: {atm_pe_iv:.1f}%
<b>Signal     :</b> {signal}"""

        send_telegram(message)
        print(f"Alert bheja! {datetime.now().strftime('%H:%M:%S')} — 15 min baad dobara.")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(900)  # 15 minutes