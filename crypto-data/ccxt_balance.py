import ccxt
import json
import os
from datetime import datetime

# Initialize Binance exchange
binance = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
    'enableRateLimit': True,  # helps avoid being rate-limited
    'options': {'defaultType': 'spot'}  # or 'future', 'margin' if needed
})

tko = ccxt.tokocrypto({
    'apiKey': os.getenv('TKO_API_KEY'),
    'secret': os.getenv('TKO_SECRET'),
    'enableRateLimit': True,  # helps avoid being rate-limited
    'options': {'defaultType': 'spot'}  # or 'future', 'margin' if needed
})

# Fetch account balance
balance = binance.fetch_balance()

# balance['total'] to json
totals = balance.get('total', {}) or {}

# Convert any non-JSON-serializable values (e.g., Decimal) to float
def _to_serializable(val):
    try:
        if isinstance(val, (str, int, float, bool)) or val is None:
            return val
        return float(val)
    except Exception:
        return str(val)

serializable_totals = {symbol: _to_serializable(amount) for symbol, amount in totals.items() if _to_serializable(amount) > 0}

output = {
    "exchange": "binance",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "totals": serializable_totals
}

# Determine output path (defaults to current dir)
out_dir = os.getenv("CRYPTO_OUT_DIR", ".")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "balance_totals.json")

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Wrote totals to {out_path}")