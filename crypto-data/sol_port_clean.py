import pandas as pd
import json
from pathlib import Path

p = Path('wallet_holdings_raw.json')
with p.open('r', encoding='utf-8') as f:
    data = json.load(f)

tokens = data["data"]["tokens"]

rows = []
for token in tokens:
    raw_balance = int(token.get("tokenBalance", "0"), 16)  # hex -> int
    
    # metadata (no logo)
    meta = token.get("tokenMetadata", {}) or {}
    decimals = meta.get("decimals", 9) or 9  # default to 9 if None
    
    base = {
        "address": token.get("address"),
        "network": token.get("network"),
        "tokenAddress": token.get("tokenAddress"),
        "tokenBalance": raw_balance,
        "decimals": decimals,
        "symbol": meta.get("symbol"),
        "name": meta.get("name"),
    }
    
    # human-readable balance
    base["balance_adj"] = raw_balance / (10 ** decimals)
    
    # token prices (can be multiple, so one row per price)
    if token.get("tokenPrices"):
        for price in token["tokenPrices"]:
            row = base.copy()
            row.update({
                "currency": price.get("currency"),
                "price_value": float(price.get("value")),
                "lastUpdatedAt": price.get("lastUpdatedAt"),
            })
            # add USD value (adjusted balance * price)
            row["value_usd"] = row["balance_adj"] * row["price_value"]
            rows.append(row)
    else:
        row = base.copy()
        row.update({
            "currency": None,
            "price_value": None,
            "lastUpdatedAt": None,
            "value_usd": None,
        })
        rows.append(row)

# Create DataFrame
df = pd.DataFrame(rows)
df.to_csv('wallet_holdings_analysis.csv', index=False)

# Display table
print(df)
