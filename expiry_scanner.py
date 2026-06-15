import requests
import time
from config import ACCESS_TOKEN, BOT_TOKEN, CHAT_ID
from datetime import datetime

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept"       : "application/json"
}

UNDERLYING_KEY = "NSE_INDEX|Nifty 50"
EXPIRY         = "2026-07-14"
NUM_STRIKES    = 5

def get_spot():
    url      = "https://api.upstox.com/v2/market-quote/quotes"
    response = requests.get(url, headers=headers,
                            params={"instrument_key": UNDERLYING_KEY})
    data     = response.json()['data']
    key      = list(data.keys())[0]
    return data[key]['last_price']

def get_contracts():
    url      = "https://api.upstox.com/v2/option/contract"
    response = requests.get(url, headers=headers,
                            params={"instrument_key": UNDERLYING_KEY})
    return response.json()['data']

def get_oi_data(calls, puts, nearby):
    all_keys = []
    for strike in nearby:
        if strike in calls: all_keys.append(calls[strike]['instrument_key'])
        if strike in puts:  all_keys.append(puts[strike]['instrument_key'])

    url      = "https://api.upstox.com/v2/market-quote/quotes"
    response = requests.get(url, headers=headers,
                            params={"instrument_key": ",".join(all_keys)})
    return response.json()['data']

def send_telegram(message):
    url     = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def get_info(instrument_key, quote_data):
    for sym, info in quote_data.items():
        if info['instrument_token'] == instrument_key:
            return info
    return None

# ── Previous OI store karo ────────────────────────────────
prev_oi = {}

print("Expiry Day Scanner shuru! Ctrl+C se band karo.")
print("=" * 60)

while True:
    try:
        now = datetime.now().strftime('%H:%M:%S')

        # Data fetch
        spot      = get_spot()
        contracts = get_contracts()

        filtered = [c for c in contracts if c['expiry'] == EXPIRY]
        calls    = {c['strike_price']: c for c in filtered if c['instrument_type'] == 'CE'}
        puts     = {c['strike_price']: c for c in filtered if c['instrument_type'] == 'PE'}
        strikes  = sorted(set(calls.keys()) & set(puts.keys()))

        atm_strike = min(strikes, key=lambda x: abs(x - spot))
        atm_index  = strikes.index(atm_strike)
        nearby     = strikes[max(0, atm_index-NUM_STRIKES) : atm_index+NUM_STRIKES+1]

        quote_data = get_oi_data(calls, puts, nearby)

        print(f"\nTime: {now} | Spot: {spot} | ATM: {atm_strike}")
        print(f"{'Strike':>8} | {'CE OI':>8} | {'CE Chg':>8} | {'PE OI':>8} | {'PE Chg':>8}")
        print("-" * 60)

        alerts = []

        for strike in nearby:
            ce_info = get_info(calls[strike]['instrument_key'], quote_data) if strike in calls else None
            pe_info = get_info(puts[strike]['instrument_key'],  quote_data) if strike in puts  else None

            ce_oi = ce_info['oi'] if ce_info else 0
            pe_oi = pe_info['oi'] if pe_info else 0

            # OI change calculate karo
            ce_key    = f"CE_{strike}"
            pe_key    = f"PE_{strike}"
            ce_change = ce_oi - prev_oi.get(ce_key, ce_oi)
            pe_change = pe_oi - prev_oi.get(pe_key, pe_oi)

            # Store karo
            prev_oi[ce_key] = ce_oi
            prev_oi[pe_key] = pe_oi

            atm_tag = " ATM" if strike == atm_strike else ""
            print(f"{strike:>8.0f} | {ce_oi:>8.0f} | {ce_change:>+8.0f} | {pe_oi:>8.0f} | {pe_change:>+8.0f}{atm_tag}")

            # Alert condition — 500 se zyada OI change
            if abs(ce_change) > 500:
                alerts.append(f"CE {strike:.0f}: OI change {ce_change:+.0f}")
            if abs(pe_change) > 500:
                alerts.append(f"PE {strike:.0f}: OI change {pe_change:+.0f}")

        # Telegram alert bhejo agar unusual activity
        if alerts:
            msg = f"<b>UNUSUAL OI ACTIVITY!</b>\n"
            msg += f"Time: {now} | Spot: {spot}\n\n"
            for alert in alerts:
                msg += f"• {alert}\n"
            send_telegram(msg)
            print(f"\nALERT bheja! {alerts}")

        print(f"\n1 min baad dobara check karega...")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(60)  # 1 minutes