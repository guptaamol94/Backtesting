import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from config import ACCESS_TOKEN

# ── Settings ──────────────────────────────────────────────
EXPIRY = "2026-07-14"
SPOT   = 23345
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}

# ── Fetch chain ───────────────────────────────────────────
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

# ── Fetch quotes ──────────────────────────────────────────
keys = []
for s in nearby:
    if s in calls: keys.append(calls[s]["instrument_key"])
    if s in puts:  keys.append(puts[s]["instrument_key"])

q_data    = requests.get("https://api.upstox.com/v2/market-quote/quotes",
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

# ── Get ATM prices ────────────────────────────────────────
ce_atm = get_price(calls[atm]["instrument_key"])
pe_atm = get_price(puts[atm]["instrument_key"])

# OTM strikes (2 away)
otm_ce_strike = strikes[atm_idx + 2]
otm_pe_strike = strikes[atm_idx - 2]
ce_otm = get_price(calls[otm_ce_strike]["instrument_key"])
pe_otm = get_price(puts[otm_pe_strike]["instrument_key"])

# Wing strikes (4 away) for Iron Condor
wing_ce_strike = strikes[min(atm_idx + 4, len(strikes)-1)]
wing_pe_strike = strikes[max(atm_idx - 4, 0)]
ce_wing = get_price(calls[wing_ce_strike]["instrument_key"])
pe_wing = get_price(puts[wing_pe_strike]["instrument_key"])

print(f"ATM: {atm}  |  CE: {ce_atm}  |  PE: {pe_atm}")
print(f"OTM CE ({otm_ce_strike}): {ce_otm}  |  OTM PE ({otm_pe_strike}): {pe_otm}")

# ── Payoff functions ──────────────────────────────────────
spot_range = np.linspace(atm - 1500, atm + 1500, 1000)

def call_payoff(S, strike, premium, action):
    intrinsic = np.maximum(S - strike, 0)
    return (intrinsic - premium) if action == "BUY" else (premium - intrinsic)

def put_payoff(S, strike, premium, action):
    intrinsic = np.maximum(strike - S, 0)
    return (intrinsic - premium) if action == "BUY" else (premium - intrinsic)

# Strategy 1: Short Straddle
straddle = call_payoff(spot_range, atm, ce_atm, "SELL") + \
           put_payoff(spot_range, atm, pe_atm, "SELL")

# Strategy 2: Short Strangle
strangle = call_payoff(spot_range, otm_ce_strike, ce_otm, "SELL") + \
           put_payoff(spot_range, otm_pe_strike, pe_otm, "SELL")

# Strategy 3: Iron Condor
iron_condor = call_payoff(spot_range, otm_ce_strike, ce_otm, "SELL") + \
              call_payoff(spot_range, wing_ce_strike, ce_wing, "BUY") + \
              put_payoff(spot_range, otm_pe_strike, pe_otm, "SELL") + \
              put_payoff(spot_range, wing_pe_strike, pe_wing, "BUY")

# ── Plot ──────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor("#0f0f1a")

strategies = [
    ("Short Straddle",  straddle,    "#00d4ff", f"Sell {atm} CE @ {ce_atm:.0f} + PE @ {pe_atm:.0f}"),
    ("Short Strangle",  strangle,    "#00ff88", f"Sell {otm_ce_strike} CE @ {ce_otm:.0f} + {otm_pe_strike} PE @ {pe_otm:.0f}"),
    ("Iron Condor",     iron_condor, "#ff9500", f"Sell {otm_ce_strike}C/{otm_pe_strike}P | Buy {wing_ce_strike}C/{wing_pe_strike}P"),
]

for ax, (name, pnl, color, subtitle) in zip(axes, strategies):
    ax.set_facecolor("#1a1a2e")

    # Fill profit/loss zones
    ax.fill_between(spot_range, pnl, 0,
                    where=(pnl >= 0), color="#00ff88", alpha=0.15, label="Profit zone")
    ax.fill_between(spot_range, pnl, 0,
                    where=(pnl < 0),  color="#ff4444", alpha=0.15, label="Loss zone")

    # PnL line
    ax.plot(spot_range, pnl, color=color, linewidth=2.5)

    # Zero line
    ax.axhline(0, color="#ffffff", linewidth=0.8, linestyle="--", alpha=0.5)

    # Spot line
    ax.axvline(SPOT, color="#ffff00", linewidth=1.2, linestyle=":", alpha=0.8, label=f"Spot {SPOT}")

    # ATM line
    ax.axvline(atm, color="#aaaaaa", linewidth=0.8, linestyle="--", alpha=0.5)

    # Breakeven points
    sign_changes = np.where(np.diff(np.sign(pnl)))[0]
    for idx in sign_changes:
        be = spot_range[idx]
        ax.axvline(be, color="#ff88ff", linewidth=1, linestyle="--", alpha=0.7)
        ax.text(be, ax.get_ylim()[0] if ax.get_ylim()[0] != 0 else -100,
                f"BE\n{be:.0f}", color="#ff88ff", fontsize=7,
                ha="center", va="bottom")

    # Max profit annotation
    max_pnl = np.max(pnl)
    ax.text(0.5, 0.97, f"Max Profit: ₹{max_pnl * lot_size:,.0f}/lot",
            transform=ax.transAxes, color="#00ff88",
            fontsize=9, ha="center", va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#003322", edgecolor="#00ff88", alpha=0.8))

    # Styling
    ax.set_title(f"{name}\n{subtitle}", color="white", fontsize=10, pad=10)
    ax.set_xlabel("Nifty at Expiry", color="#aaaaaa", fontsize=9)
    ax.set_ylabel("P&L per unit (₹)", color="#aaaaaa", fontsize=9)
    ax.tick_params(colors="#aaaaaa", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333355")

    profit_patch = mpatches.Patch(color="#00ff88", alpha=0.4, label="Profit")
    loss_patch   = mpatches.Patch(color="#ff4444", alpha=0.4, label="Loss")
    ax.legend(handles=[profit_patch, loss_patch], loc="lower right",
              facecolor="#1a1a2e", edgecolor="#333355", labelcolor="white", fontsize=8)

plt.suptitle(f"NIFTY Option Strategy Payoff  |  Expiry: {EXPIRY}  |  Spot: {SPOT}  |  Lot: {lot_size}",
             color="white", fontsize=13, fontweight="bold", y=1.02)

plt.tight_layout()
plt.savefig("payoff_chart.png", dpi=150, bbox_inches="tight",
            facecolor="#0f0f1a", edgecolor="none")
plt.show()

print("\nChart save hua: payoff_chart.png")
print(f"\nSummary:")
print(f"  Short Straddle  — Max Profit: Rs.{np.max(straddle) * lot_size:,.0f}/lot")
print(f"  Short Strangle  — Max Profit: Rs.{np.max(strangle) * lot_size:,.0f}/lot")
print(f"  Iron Condor     — Max Profit: Rs.{np.max(iron_condor) * lot_size:,.0f}/lot")