import yfinance as yf
import pandas as pd

df = yf.Ticker("^NSEI").history(period="60d", interval="15m")
df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
df.dropna(inplace=True)
df.index = pd.to_datetime(df.index)
df = df.between_time('09:15', '15:30')

# VWAP
df['Date']         = df.index.date
df['TP']           = (df['High'] + df['Low'] + df['Close']) / 3
df['TP_Vol']       = df['TP'] * df['Volume']
df['Cumul_TP_Vol'] = df.groupby('Date')['TP_Vol'].cumsum()
df['Cumul_Vol']    = df.groupby('Date')['Volume'].cumsum()
df['VWAP']         = df['Cumul_TP_Vol'] / df['Cumul_Vol']

# RSI
delta     = df['Close'].diff()
gain      = delta.clip(lower=0).rolling(14).mean()
loss_     = (-delta.clip(upper=0)).rolling(14).mean()
df['RSI'] = 100 - (100 / (1 + gain / loss_))

# Debug
print("Volume sample:")
print(df['Volume'].head(10))
print("\nVWAP sample:")
print(df['VWAP'].head(10))
print("\nRSI sample:")
print(df['RSI'].head(20))
print("\nClose vs VWAP:")
print(df[['Close', 'VWAP']].head(10))