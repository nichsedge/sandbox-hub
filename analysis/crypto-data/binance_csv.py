import ccxt
import pandas as pd
import time
import os
import json

top100 = pd.read_csv("data/coingecko/top_100_cmc.csv")
exchange = ccxt.binance()


def fetch_ohlcv(exchange, symbol, timeframe, since=None, limit=1000):
    """Fetch historical OHLCV data from the exchange."""
    return exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)


def fetch_data_in_batches(exchange, symbol, timeframe, start_date, limit=1000):
    print(f"--- Start {symbol} ---")

    """Fetch data in batches from a date range."""
    start_timestamp = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_timestamp = int(pd.Timestamp.now().timestamp() * 1000)

    all_data = []
    while start_timestamp < end_timestamp:
        batch_data = fetch_ohlcv(
            exchange, symbol, timeframe, since=start_timestamp, limit=limit
        )

        if not batch_data:
            break

        # Update the start_timestamp to the timestamp of the last entry in the batch
        start_timestamp = batch_data[-1][0] + 1
        print(f"Downloading {pd.Timestamp(start_timestamp)}")

        # Append batch data to the overall list
        all_data.extend(batch_data)

        # Sleep to avoid rate limits
        time.sleep(1)

    return all_data


def save_to_csv(data, filename):
    """Save the data to a CSV file."""
    df = pd.DataFrame(data, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"], unit="ms")
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")


# Path to the folder containing the CSV files
def combine_data(folder_path="data"):
    # List all CSV files in the folder
    files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    # Initialize an empty list to hold DataFrames
    dfs = []

    # Loop through the files and read them into DataFrames
    for file in files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path)
        # Optionally, add a column for the ticker if needed
        df["ticker"] = file.split("_")[
            0
        ]  # Assumes ticker is the filename without extension
        dfs.append(df)

    # Concatenate all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)

    # Save the combined DataFrame to a new CSV file
    combined_df.to_csv("data.csv", index=False)


def main(symbol):
    timeframe = "1d"
    start_date = "2017-08-17"

    data = fetch_data_in_batches(exchange, symbol, timeframe, start_date)

    # Save to CSV
    save_to_csv(data, f"data/{symbol.replace('/', '_')}_{timeframe}.csv")


if __name__ == "__main__":
    markets = exchange.load_markets()

    with open("result.json", "w") as fp:
        json.dump(markets, fp)
    # for sym in list(top100['symbol']):
    #     try:
    #         main(f'{sym.upper()}/USDT')
    #     except Exception as e:
    #         print(f"An unexpected error occurred: {sym} - {e}")
