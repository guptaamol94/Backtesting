import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ── Settings ──────────────────────────────────────────────
STOCKS    = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "WIPRO.NS"]
CAPITAL   = 100000
STOP_LOSS = 0.03
TARGET    = 0.06

results        = []
all_portfolios = {}

for STOCK in STOCKS:
    try:
        # ── Data ──────────────────────────────────────────
        df = yf.Ticker(STOCK).history(period="1y", interval="1d")
        df = df[['Close']].copy()

        # ── Indicators ────────────────────────────────────
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        delta       = df['Close'].diff()
        gain        = delta.clip(lower=0).rolling(14).mean()
        loss_       = (-delta.clip(upper=0)).rolling(14).mean()
        df['RSI']   = 100 - (100 / (1 + gain / loss_))

        # ── Signals ───────────────────────────────────────
        df['Signal'] = 0
        df.loc[(df['SMA20'] > df['SMA50']) & (df['RSI'] > 30) & (df['RSI'] < 70), 'Signal'] = 1
        df.loc[(df['SMA20'] < df['SMA50']) | (df['RSI'] > 70), 'Signal'] = -1
        df['Trade'] = df['Signal'].diff()

        # ── Backtest Loop ─────────────────────────────────
        capital     = CAPITAL
        position    = 0
        portfolio   = []
        trades      = []
        entry_price = 0
        in_trade    = False

        for i, row in df.iterrows():

            # Stop Loss aur Target — continue ki jagah flag use karo
            exited = False
            if in_trade and position > 0:
                change = (row['Close'] - entry_price) / entry_price
                if change <= -STOP_LOSS or change >= TARGET:
                    exit_value = position * row['Close']
                    trades.append(exit_value - (position * entry_price))
                    capital    = exit_value
                    position   = 0
                    in_trade   = False
                    exited     = True

            # Normal signal — sirf tabhi check karo jab abhi exit nahi hua
            if not exited:
                if row['Trade'] == 2 and capital > 0 and not in_trade:
                    position    = capital / row['Close']
                    entry_price = row['Close']
                    capital     = 0
                    in_trade    = True

                elif row['Trade'] == -2 and position > 0:
                    exit_value = position * row['Close']
                    trades.append(exit_value - (position * entry_price))
                    capital    = exit_value
                    position   = 0
                    in_trade   = False

            # Har row ke liye portfolio value save karo
            portfolio.append(capital + position * row['Close'])

        df['Portfolio'] = portfolio
        all_portfolios[STOCK.replace('.NS', '')] = df['Portfolio']

        # ── Metrics ───────────────────────────────────────
        final        = df['Portfolio'].iloc[-1]
        total_return = (final - CAPITAL) / CAPITAL * 100
        rolling_max  = df['Portfolio'].cummax()
        drawdown     = (df['Portfolio'] - rolling_max) / rolling_max * 100
        max_dd       = drawdown.min()
        win_rate     = (len([t for t in trades if t > 0]) / len(trades) * 100) if trades else 0
        daily_ret    = df['Portfolio'].pct_change()
        sharpe       = (daily_ret.mean() / daily_ret.std()) * (252 ** 0.5)

        results.append({
            'Stock'       : STOCK.replace('.NS', ''),
            'Final Value' : f"Rs. {final:,.0f}",
            'Return %'    : f"{total_return:.1f}%",
            'Max Drawdown': f"{max_dd:.1f}%",
            'Trades'      : len(trades),
            'Win Rate'    : f"{win_rate:.0f}%",
            'Sharpe'      : f"{sharpe:.2f}"
        })

        print(f"{STOCK} done!")

    except Exception as e:
        print(f"{STOCK} error: {e}")

# ── Results Table ─────────────────────────────────────────
results_df = pd.DataFrame(results)
print("\n")
print("=" * 75)
print("         COMPARISON WITH STOP LOSS (3%) + TARGET (6%)")
print("=" * 75)
print(results_df.to_string(index=False))
print("=" * 75)

# ── Chart ─────────────────────────────────────────────────
plt.figure(figsize=(12, 6))
for name, portfolio in all_portfolios.items():
    plt.plot(portfolio.index, portfolio.values, label=name)
plt.axhline(CAPITAL, color='gray', linestyle='--', label='Starting Capital')
plt.title('All Stocks - SMA + RSI + Stop Loss Backtest')
plt.ylabel('Portfolio Value (Rs.)')
plt.xlabel('Date')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()