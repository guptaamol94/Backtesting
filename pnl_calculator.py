import sys
sys.stdout.reconfigure(encoding='utf-8')

# ── Multiple Trades P&L ───────────────────────────────────
trades = [
    {"entry": 23500, "exit": 23700, "qty": 65, "type": "BUY"},
    {"entry": 23800, "exit": 23600, "qty": 65, "type": "SELL"},
    {"entry": 23600, "exit": 23550, "qty": 65, "type": "BUY"},
    {"entry": 23900, "exit": 24000, "qty": 65, "type": "SELL"},
]

print("=" * 55)
print("         TRADE P&L SUMMARY")
print("=" * 55)
print(f"{'#':>2} | {'Type':>4} | {'Entry':>6} | {'Exit':>6} | {'P&L':>10} | {'Result':>6}")
print("-" * 55)

total_pnl    = 0
total_profit = 0
total_loss   = 0
win_count    = 0

for i, trade in enumerate(trades):
    if trade['type'] == "BUY":
        pnl = (trade['exit'] - trade['entry']) * trade['qty']
    else:
        pnl = (trade['entry'] - trade['exit']) * trade['qty']

    total_pnl += pnl

    if pnl > 0:
        result       = "WIN"
        total_profit += pnl
        win_count    += 1
    else:
        result      = "LOSS"
        total_loss  += pnl

    print(f"{i+1:>2} | {trade['type']:>4} | {trade['entry']:>6} | {trade['exit']:>6} | Rs.{pnl:>8,.0f} | {result:>6}")

print("=" * 55)
print(f"Total Trades  : {len(trades)}")
print(f"Win Rate      : {win_count}/{len(trades)} = {win_count/len(trades)*100:.0f}%")
print(f"Total Profit  : Rs. {total_profit:,.0f}")
print(f"Total Loss    : Rs. {total_loss:,.0f}")
print(f"Net P&L       : Rs. {total_pnl:,.0f}")
print("=" * 55)