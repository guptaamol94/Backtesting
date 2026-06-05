import yfinance as yf
import pandas as pd

# Nifty 50 data download
df = yf.Ticker("^NSEI").history(period="1y", interval="1d")
df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()

print("Total rows:", len(df))
print("\nNifty Last 5 days:")
print(df[['Close']].tail())