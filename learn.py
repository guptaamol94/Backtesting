print("Mera Pehla Code")
print("Abc")
print("Nifty")  
print(23900)

apka_naam="Amol"
stock="Nifty"
spot_price=23900
lot_size=65

print(apka_naam)
print(stock)
print(spot_price)
print(lot_size)

print(f"mera naam hai {apka_naam}")
print(f"main {stock} mai trade karta hu")
print(f"aaj ka spot price {spot_price} hai")
print(f"Nifty ka lot {lot_size} hai")

entry_price=23500
lot_size=65
# target entry se 1% upr
target = entry_price + (entry_price * 0.01)
# stop_loss nikalo entry se .6% neeche 
stop_loss = entry_price - (entry_price * 0.006)
# max_profit nikalo
max_profit = (target - entry_price ) * lot_size

max_loss = (entry_price- stop_loss) * lot_size


print(f"Entry_price : {entry_price}")
print(f"target : {target}")
print(f"stop_loss : {stop_loss}")
print(f"max_profit : {max_profit}")
print(f"max_loss : {max_loss}")

