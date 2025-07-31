import requests
import pandas as pd
import json

url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
response = requests.get(url)

data = json.loads(response.content)
top100 = pd.DataFrame(data)

top100.to_csv("top_100_cmc.csv")
