import pickle
import pandas as pd
import numpy as np
from datetime import date

exclude_list = [
    "steth",
    "weeth",
    "ezeth",
    "reth",
    "meth",
    "eeth",
    "rseth",
    "wbtc",
    "dai",
]


def get_raw_ohlcvs(start_date=None, end_date=None):
    # Example usage
    df = pd.read_csv("data.csv")
    return df


def get_ohlcvs(start_date=None, end_date=None):
    # Example usage
    df = pd.read_csv("data.csv", index_col="date")

    # print(ohlcvs)
    df = df[~df["ticker"].isin(exclude_list)]
    df = df[~df["ticker"].str.contains("usd", case=False, na=False)]

    if start_date != None:
        if end_date == None:
            end_date = date.today()

        df = df[(df.index >= start_date) & (df.index <= end_date)]

    return df


def get_closes(df):
    return df.pivot_table(index=df.index, columns="ticker", values="close")


def get_returns(closes_df: pd.DataFrame):
    return closes_df.pct_change(fill_method=None)


def get_log_returns(closes_df: pd.DataFrame):
    return np.log(closes_df / closes_df.shift(1))


# print(get_closes(get_ohlcvs()))
