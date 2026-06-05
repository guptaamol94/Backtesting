import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ── Settings ──────────────────────────────────────────────
SYMBOL    = "^NSEI"
CAPITAL   = 100000
STOP_LOSS = 0.005
TARGET    = 0.01

# ── Data ──────────────────────────────────────────────────
df = yf.Ticker(SYMBOL).history(period="60d", interval="15m")
df = df[['Open', 'High', 'Low', 'Close']].copy()
df.dropna(inplace=True)
df.index = pd.to_datetime(df.index)
df = df.between_time('09:15', '15:30')

# ── Indicators ────────────────────────────────────────────
# EMA — Exponential Moving Average
# Simple MA se better — recent prices ko zyada weight deta hai
df['EMA9']  = df['Close'].ewm(span=9,  adjust=False).mean()
df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

# RSI
delta     = df['Close'].diff()
gain      = delta.clip(lower=0).rolling(14).mean()
loss_     = (-delta.clip(upper=0)).rolling(14).mean()
df['RSI'] = 100 - (100 / (1 + gain / loss_))

# ── Strategy Logic ────────────────────────────────────────
# Buy  — EMA9 > EMA21 > EMA50 (sab aligned) + RSI 40-65
# Sell — EMA9 < EMA21 ya RSI > 70

df['Signal'] = 0
buy_cond = (
    (df['EMA9']  > df['EMA21']) &   # Fast > Medium
    (df['EMA21'] > df['EMA50']) &   # Medium > Slow
    (df['RSI']   > 40) &            # Oversold nahi
    (df['RSI']   < 65)              # Overbought nahi
)
sell_cond = (
    (df['EMA9'] < df['EMA21']) |    # Fast < Medium
    (df['RSI']  > 70)               # Overbought
)

df.loc[buy_cond,  'Signal'] = 1
df.loc[sell_cond, 'Signal'] = -1
df['Trade'] = df['Signal'].diff()

print(f"Buy signals  : {(df['Trade'] == 2).sum()}")
print(f"Sell signals : {(df['Trade'] == -2).sum()}")

# ── Backtest ──────────────────────────────────────────────
capital     = CAPITAL
position    = 0
portfolio   = []
trades      = []
entry_price = 0
entry_time  = None
in_trade    = False

for i, row in df.iterrows():
    exited       = False
    current_time = i.time()
    square_off   = pd.Timestamp('15:15').time()
    no_entry     = pd.Timestamp('15:00').time()

    # Same day square off
    if in_trade and position > 0:
        same_day = (entry_time.date() == i.date())
        if current_time >= square_off and same_day:
            exit_value = position * row['Close']
            trades.append({
                'Entry Time' : entry_time,
                'Exit Time'  : i,
                'PnL'        : exit_value - (position * entry_price),
                'Return %'   : (row['Close'] - entry_price) / entry_price * 100,
                'Exit Reason': 'Square Off'
            })
            capital  = exit_value
            position = 0
            in_trade = False
            exited   = True
        elif not same_day:
            exit_value = position * row['Open']
            trades.append({
                'Entry Time' : entry_time,
                'Exit Time'  : i,
                'PnL'        : exit_value - (position * entry_price),
                'Return %'   : (row['Open'] - entry_price) / entry_price * 100,
                'Exit Reason': 'Force Close'
            })
            capital  = exit_value
            position = 0
            in_trade = False
            exited   = True

    # Stop Loss / Target
    if in_trade and not exited and position > 0:
        change = (row['Close'] - entry_price) / entry_price
        if change <= -STOP_LOSS:
            exit_value = position * row['Close']
            trades.append({
                'Entry Time' : entry_time,
                'Exit Time'  : i,
                'PnL'        : exit_value - (position * entry_price),
                'Return %'   : change * 100,
                'Exit Reason': 'Stop Loss'
            })
            capital  = exit_value
            position = 0
            in_trade = False
            exited   = True
        elif change >= TARGET:
            exit_value = position * row['Close']
            trades.append({
                'Entry Time' : entry_time,
                'Exit Time'  : i,
                'PnL'        : exit_value - (position * entry_price),
                'Return %'   : change * 100,
                'Exit Reason': 'Target'
            })
            capital  = exit_value
            position = 0
            in_trade = False
            exited   = True

    # Entry
    if not exited and not in_trade and capital > 0:
        if current_time <= no_entry and row['Trade'] == 2:
            position    = capital / row['Close']
            entry_price = row['Close']
            entry_time  = i
            capital     = 0
            in_trade    = True

    portfolio.append(capital + position * row['Close'])

df['Portfolio'] = portfolio

# ── Metrics ───────────────────────────────────────────────
final        = df['Portfolio'].iloc[-1]
total_return = (final - CAPITAL) / CAPITAL * 100
rolling_max  = df['Portfolio'].cummax()
drawdown     = (df['Portfolio'] - rolling_max) / rolling_max * 100
max_dd       = drawdown.min()
trades_df    = pd.DataFrame(trades)

if len(trades_df) > 0:
    win_rate   = len(trades_df[trades_df['PnL'] > 0]) / len(trades_df) * 100
    avg_profit = trades_df[trades_df['PnL'] > 0]['PnL'].mean() if len(trades_df[trades_df['PnL'] > 0]) > 0 else 0
    avg_loss   = trades_df[trades_df['PnL'] < 0]['PnL'].mean() if len(trades_df[trades_df['PnL'] < 0]) > 0 else 0
    sl_hits    = len(trades_df[trades_df['Exit Reason'] == 'Stop Loss'])
    tgt_hits   = len(trades_df[trades_df['Exit Reason'] == 'Target'])
    sq_hits    = len(trades_df[trades_df['Exit Reason'] == 'Square Off'])
    fc_hits    = len(trades_df[trades_df['Exit Reason'] == 'Force Close'])
else:
    win_rate = avg_profit = avg_loss = sl_hits = tgt_hits = sq_hits = fc_hits = 0

daily_ret = df['Portfolio'].pct_change()
sharpe    = (daily_ret.mean() / daily_ret.std()) * (252 ** 0.5) if daily_ret.std() > 0 else 0

print("\n" + "=" * 52)
print("   NIFTY EMA + RSI BACKTEST — 60 Days")
print("=" * 52)
print(f"Starting Capital  : Rs. {CAPITAL:,}")
print(f"Final Value       : Rs. {final:,.0f}")
print(f"Total Return      : {total_return:.1f}%")
print(f"Max Drawdown      : {max_dd:.1f}%")
print(f"Total Trades      : {len(trades_df)}")
print(f"Win Rate          : {win_rate:.0f}%")
print(f"Sharpe Ratio      : {sharpe:.2f}")
print(f"Avg Profit/Trade  : Rs. {avg_profit:,.0f}")
print(f"Avg Loss/Trade    : Rs. {avg_loss:,.0f}")
print(f"Stop Loss hits    : {sl_hits}")
print(f"Target hits       : {tgt_hits}")
print(f"Square Off hits   : {sq_hits}")
print(f"Force Close hits  : {fc_hits}")
print("=" * 52)

if len(trades_df) > 0:
    print("\nTrade Log:")
    print(trades_df.to_string(index=False))

# ── Chart ─────────────────────────────────────────────────
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

# Portfolio
ax1.plot(df.index, df['Portfolio'], color='blue', label='Portfolio')
ax1.axhline(CAPITAL, color='gray', linestyle='--', label='Starting Capital')
ax1.set_title('Nifty EMA + RSI Backtest — 15 Min — 60 Days')
ax1.set_ylabel('Portfolio Value (Rs.)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Price + EMAs
ax2.plot(df.index, df['Close'], color='black',  linewidth=0.8, label='Nifty Close')
ax2.plot(df.index, df['EMA9'],  color='blue',   linewidth=1.2, label='EMA9')
ax2.plot(df.index, df['EMA21'], color='orange', linewidth=1.2, label='EMA21')
ax2.plot(df.index, df['EMA50'], color='red',    linewidth=1.2, label='EMA50')
ax2.set_ylabel('Price')
ax2.legend()
ax2.grid(True, alpha=0.3)

# RSI
ax3.plot(df.index, df['RSI'], color='purple', label='RSI')
ax3.axhline(70, color='red',   linestyle='--', alpha=0.7, label='Overbought 70')
ax3.axhline(40, color='green', linestyle='--', alpha=0.7, label='Oversold 40')
ax3.set_ylabel('RSI')
ax3.set_xlabel('Date')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()