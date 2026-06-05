import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ── Settings ──────────────────────────────────────────────
SYMBOL  = "^NSEI"
CAPITAL = 100000
STOP_LOSS = 0.02   # Nifty pe 2% stop loss
TARGET    = 0.04   # 4% target

# ── Data ──────────────────────────────────────────────────
df = yf.Ticker(SYMBOL).history(period="2y", interval="1d")
df = df[['Open', 'High', 'Low', 'Close']].copy()

# ── Indicators ────────────────────────────────────────────
df['SMA20'] = df['Close'].rolling(20).mean()
df['SMA50'] = df['Close'].rolling(50).mean()
delta       = df['Close'].diff()
gain        = delta.clip(lower=0).rolling(14).mean()
loss_       = (-delta.clip(upper=0)).rolling(14).mean()
df['RSI']   = 100 - (100 / (1 + gain / loss_))

# ── Signals ───────────────────────────────────────────────
df['Signal'] = 0
df.loc[(df['SMA20'] > df['SMA50']) & (df['RSI'] > 30) & (df['RSI'] < 70), 'Signal'] = 1
df.loc[(df['SMA20'] < df['SMA50']) | (df['RSI'] > 70), 'Signal'] = -1
df['Trade'] = df['Signal'].diff()

# ── Backtest ──────────────────────────────────────────────
capital     = CAPITAL
position    = 0
portfolio   = []
trades      = []
entry_price = 0
in_trade    = False

for i, row in df.iterrows():
    exited = False
    if in_trade and position > 0:
        change = (row['Close'] - entry_price) / entry_price
        if change <= -STOP_LOSS or change >= TARGET:
            exit_value = position * row['Close']
            trades.append({
                'Exit'   : i,
                'PnL'    : exit_value - (position * entry_price),
                'Return' : change * 100
            })
            capital  = exit_value
            position = 0
            in_trade = False
            exited   = True

    if not exited:
        if row['Trade'] == 2 and capital > 0 and not in_trade:
            position    = capital / row['Close']
            entry_price = row['Close']
            capital     = 0
            in_trade    = True
        elif row['Trade'] == -2 and position > 0:
            exit_value = position * row['Close']
            trades.append({
                'Exit'   : i,
                'PnL'    : exit_value - (position * entry_price),
                'Return' : (row['Close'] - entry_price) / entry_price * 100
            })
            capital  = exit_value
            position = 0
            in_trade = False

    portfolio.append(capital + position * row['Close'])

df['Portfolio'] = portfolio

# ── Metrics ───────────────────────────────────────────────
final        = df['Portfolio'].iloc[-1]
total_return = (final - CAPITAL) / CAPITAL * 100
rolling_max  = df['Portfolio'].cummax()
drawdown     = (df['Portfolio'] - rolling_max) / rolling_max * 100
max_dd       = drawdown.min()
trades_df    = pd.DataFrame(trades)
win_rate     = (len(trades_df[trades_df['PnL'] > 0]) / len(trades_df) * 100) if len(trades_df) > 0 else 0
daily_ret    = df['Portfolio'].pct_change()
sharpe       = (daily_ret.mean() / daily_ret.std()) * (252 ** 0.5)

print("=" * 50)
print("      NIFTY 50 BACKTEST RESULTS (2 Years)")
print("=" * 50)
print(f"Starting Capital  : Rs. {CAPITAL:,}")
print(f"Final Value       : Rs. {final:,.0f}")
print(f"Total Return      : {total_return:.1f}%")
print(f"Max Drawdown      : {max_dd:.1f}%")
print(f"Total Trades      : {len(trades_df)}")
print(f"Win Rate          : {win_rate:.0f}%")
print(f"Sharpe Ratio      : {sharpe:.2f}")
print("=" * 50)

if len(trades_df) > 0:
    print("\nTrade wise summary:")
    print(trades_df.to_string(index=False))

# ── Chart ─────────────────────────────────────────────────
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

ax1.plot(df.index, df['Portfolio'], color='blue', label='Portfolio')
ax1.axhline(CAPITAL, color='gray', linestyle='--', label='Starting Capital')
ax1.set_title('Nifty 50 - SMA + RSI + Stop Loss Backtest (2 Years)')
ax1.set_ylabel('Portfolio Value (Rs.)')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(df.index, df['RSI'], color='purple', label='RSI')
ax2.axhline(70, color='red',   linestyle='--', alpha=0.7, label='Overbought 70')
ax2.axhline(30, color='green', linestyle='--', alpha=0.7, label='Oversold 30')
ax2.set_ylabel('RSI')
ax2.legend()
ax2.grid(True, alpha=0.3)

ax3.fill_between(df.index, drawdown, 0, color='red', alpha=0.4, label='Drawdown')
ax3.set_ylabel('Drawdown (%)')
ax3.set_xlabel('Date')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()