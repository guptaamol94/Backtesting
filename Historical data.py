import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ── 1. Data Download ──────────────────────────────────────
df = yf.Ticker("RELIANCE.NS").history(period="1y", interval="1d")
df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()

# ── 2. Strategy: SMA Crossover ───────────────────────────
df['SMA20'] = df['Close'].rolling(20).mean()  # Fast line
df['SMA50'] = df['Close'].rolling(50).mean()  # Slow line

df['Signal'] = 0
df.loc[df['SMA20'] > df['SMA50'], 'Signal'] = 1   # Bullish
df.loc[df['SMA20'] < df['SMA50'], 'Signal'] = -1  # Bearish
df['Trade'] = df['Signal'].diff()

# ── 3. Backtest Loop ──────────────────────────────────────
capital   = 100000  # Starting capital ₹1 lakh
position  = 0       # Kitne shares hain abhi
portfolio = []      # Har din ki value

for i, row in df.iterrows():
    if row['Trade'] == 2 and capital > 0:       # Buy signal
        position = capital / row['Close']
        capital  = 0
    elif row['Trade'] == -2 and position > 0:   # Sell signal
        capital  = position * row['Close']
        position = 0

    total = capital + (position * row['Close'])
    portfolio.append(total)

df['Portfolio'] = portfolio

# ── 4. Results ────────────────────────────────────────────
final   = df['Portfolio'].iloc[-1]
returns = (final - 100000) / 100000 * 100

print("=" * 40)
print(f"Starting Capital : ₹1,00,000")
print(f"Final Value      : ₹{final:,.0f}")
print(f"Total Return     : {returns:.1f}%")
print("=" * 40)

# ── 5. Chart ──────────────────────────────────────────────
df['Portfolio'].plot(figsize=(12, 5), title='Reliance SMA Crossover Backtest', color='blue')
plt.axhline(100000, color='gray', linestyle='--', label='Starting Capital')
plt.ylabel('Portfolio Value (₹)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()