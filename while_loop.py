import time

count = 1

while count <= 5:
    print(f"Check {count}: Nifty data fetch ho raha hai...")
    count = count + 1
    time.sleep(1)

print("Done!")
import time

# ── Yeh hamesha chalta rahega ─────────────────────────────
while True:
    print("Nifty data check ho raha hai...")
    time.sleep(5)    # 5 second baad dobara