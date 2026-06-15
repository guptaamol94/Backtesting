# Step 1 — Function define karo
def check_trade_status(entry_price, current_price, sl_pct, target_pct):
    
    # Step 2 — SL aur Target calculate karo
    sl     = entry_price - (entry_price * sl_pct)
    target = entry_price + (entry_price * target_pct)
    
    # Step 3 — Check karo
    if current_price <= sl:
        return "SL HIT"
    elif current_price >= target:
        return "TARGET HIT"
    else:
        return "TRADE OPEN"

# Step 4 — Use karo
status = check_trade_status(23400, 23250, 0.006, 0.012)
print(f"Status: {status}")

# Aur test karo different scenarios
print(check_trade_status(23400, 23600, 0.006, 0.012))  # Target hit?
print(check_trade_status(23400, 23400, 0.006, 0.012))  # Open?