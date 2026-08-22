import requests
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- Your initial script ---
SOL_ADDRESS = os.getenv("SOL_ADDRESS")
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
url = f"https://api.g.alchemy.com/data/v1/{ALCHEMY_API_KEY}/assets/tokens/balances/by-address"

payload = {"addresses": [{"address": SOL_ADDRESS, "networks": ["solana-mainnet"]}]}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)

    # --- Step 1: Get the JSON data from the response ---
    data = response.json()

except requests.exceptions.RequestException as e:
    print(f"Error during API request: {e}")
except (KeyError, TypeError) as e:
    print(f"Error parsing JSON data: {e}")

# Save the original JSON to a file for reference
original_json_filename = "token_balances_by_wallet.json"
with open(original_json_filename, "w") as f:
    json.dump(data, f, indent=4)
print(f"Original JSON response saved to {original_json_filename}")
