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
df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
df.dropna(inplace=True)
df.index = pd.to_datetime(df.index)
df = df.between_time('09:15', '15:30')

# ── VWAP ──────────────────────────────────────────────────
df['Date']         = df.index.date
df['TP']           = (df['High'] + df['Low'] + df['Close']) / 3
df['TP_Vol']       = df['TP'] * df['Volume']
df['Cumul_TP_Vol'] = df.groupby('Date')['TP_Vol'].cumsum()
df['Cumul_Vol']    = df.groupby('Date')['Volume'].cumsum()
df['VWAP']         = df['Cumul_TP_Vol'] / df['Cumul_Vol']

# ── RSI only ──────────────────────────────────────────────
delta     = df['Close'].diff()
gain      = delta.clip(lower=0).rolling(14).mean()
loss_     = (-delta.clip(upper=0)).rolling(14).mean()
df['RSI'] = 100 - (100 / (1 + gain / loss_))

# ── Strategy — Sirf VWAP + RSI ───────────────────────────
# Buy  — Price VWAP se upar + RSI 35-60
# Sell — Price VWAP se neeche + RSI > 65

df['Signal'] = 0
buy_cond  = (
    (df['Close'] > df['VWAP']) &
    (df['RSI']   > 35) &
    (df['RSI']   < 60)
)
sell_cond = (
    (df['Close'] < df['VWAP']) |
    (df['RSI']   > 65)
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
else:
    win_rate = avg_profit = avg_loss = sl_hits = tgt_hits = sq_hits = 0

daily_ret = df['Portfolio'].pct_change()
sharpe    = (daily_ret.mean() / daily_ret.std()) * (252 ** 0.5) if daily_ret.std() > 0 else 0

print("=" * 52)
print("   NIFTY VWAP + RSI BACKTEST — 60 Days")
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
print("=" * 52)

if len(trades_df) > 0:
    print("\nTrade Log:")
    print(trades_df.to_string(index=False))

# ── Chart ─────────────────────────────────────────────────
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

ax1.plot(df.index, df['Portfolio'], color='blue', label='Portfolio')
ax1.axhline(CAPITAL, color='gray', linestyle='--', label='Starting Capital')
ax1.set_title('Nifty VWAP + RSI Backtest — 15 Min — 60 Days')
ax1.set_ylabel('Portfolio Value (Rs.)')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(df.index, df['Close'], color='black',  linewidth=0.8, label='Nifty Close')
ax2.plot(df.index, df['VWAP'],  color='orange', linewidth=1.5, label='VWAP')
ax2.set_ylabel('Price')
ax2.legend()
ax2.grid(True, alpha=0.3)

ax3.fill_between(df.index, drawdown, 0, color='red', alpha=0.4, label='Drawdown')
ax3.set_ylabel('Drawdown (%)')
ax3.set_xlabel('Date')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()