import requests

url = "https://www.nseindia.com/api/fiidiiTradeReact"

headers = {
    "User-Agent"     : "Mozilla/5.0",
    "Accept"         : "application/json",
    "Referer"        : "https://www.nseindia.com",
    "Accept-Language": "en-US,en;q=0.9"
}

session  = requests.Session()
session.get("https://www.nseindia.com", headers=headers)
response = session.get(url, headers=headers)
data     = response.json()

print("=" * 50)
print(f"  FII/DII TRACKER — {data[0]['date']}")
print("=" * 50)

for item in data:
    category = item['category']
    buy      = float(item['buyValue'])
    sell     = float(item['sellValue'])
    net      = float(item['netValue'])
    action   = "BUYING" if net > 0 else "SELLING"

    print(f"\n{category}:")
    print(f"  Buy Value  : Rs. {buy:,.2f} Cr")
    print(f"  Sell Value : Rs. {sell:,.2f} Cr")
    print(f"  Net Value  : Rs. {net:,.2f} Cr")
    print(f"  Action     : {action}")

print("\n" + "=" * 50)

fii_net = float([x for x in data if 'FII' in x['category']][0]['netValue'])
dii_net = float([x for x in data if x['category'] == 'DII'][0]['netValue'])

print("\nMarket Signal:")
if fii_net > 0 and dii_net > 0:
    print("  FII + DII dono BUYING = Strong Bullish!")
elif fii_net > 0 and dii_net < 0:
    print("  FII BUYING, DII SELLING = Cautious Bullish")
elif fii_net < 0 and dii_net > 0:
    print("  FII SELLING, DII BUYING = Supported market")
else:
    print("  FII + DII dono SELLING = Bearish!")

print("=" * 50)