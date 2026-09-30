import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pickle
import pandas as pd
import seaborn as sns
import scipy.stats as stats

from datasets import (
    get_raw_ohlcvs,
    get_ohlcvs,
    get_closes,
    get_returns,
    get_log_returns,
)


raw_ohlcvs = get_raw_ohlcvs()
# ohlcvs = get_ohlcvs()
ohlcvs = get_ohlcvs("2023-01-01", "2024-06-31")
close_prices = get_closes(ohlcvs)
returns = get_returns(close_prices).fillna(0)
log_returns = get_log_returns(close_prices).fillna(0)

eth = ohlcvs[ohlcvs["ticker"] == "ETH"].reset_index()
# ohlcvs = ohlcvs.drop(columns=['ticker'])
df = eth

# Assuming df is your DataFrame
df["MA"] = df["close"].rolling(window=20).mean()
df["EMA"] = df["close"].ewm(span=20, adjust=False).mean()

# Bollinger Bands
df["BOLL_MID"] = df["close"].rolling(window=20).mean()
df["BOLL_STD"] = df["close"].rolling(window=20).std()
df["BOLL_UPPER"] = df["BOLL_MID"] + (df["BOLL_STD"] * 2)
df["BOLL_LOWER"] = df["BOLL_MID"] - (df["BOLL_STD"] * 2)

# Dropping temporary columns if needed
df.drop(columns=["BOLL_MID", "BOLL_STD"], inplace=True)

import talib

# SAR (Parabolic SAR)
df["SAR"] = talib.SAR(df["high"], df["low"], acceleration=0.02, maximum=0.2)

# MACD (Moving Average Convergence Divergence)
df["MACD"], df["MACD_SIGNAL"], df["MACD_HIST"] = talib.MACD(
    df["close"], fastperiod=12, slowperiod=26, signalperiod=9
)

# KDJ (Stochastic Oscillator)
df["KDJ_K"], df["KDJ_D"] = talib.STOCH(
    df["high"],
    df["low"],
    df["close"],
    fastk_period=14,
    slowk_period=3,
    slowk_matype=0,
    slowd_period=3,
    slowd_matype=0,
)
df["KDJ_J"] = 3 * df["KDJ_K"] - 2 * df["KDJ_D"]

df["RSI"] = talib.RSI(df["close"], timeperiod=14)

df.head()

import plotly.graph_objs as go

# Candlestick chart
candlestick = go.Candlestick(
    x=df["date"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Candlestick",
)

# Moving Average
ma = go.Scatter(x=df["date"], y=df["MA"], mode="lines", name="MA")

# Exponential Moving Average
ema = go.Scatter(x=df["date"], y=df["EMA"], mode="lines", name="EMA")

# Bollinger Bands
boll_upper = go.Scatter(
    x=df["date"], y=df["BOLL_UPPER"], mode="lines", name="Bollinger Upper"
)
boll_lower = go.Scatter(
    x=df["date"], y=df["BOLL_LOWER"], mode="lines", name="Bollinger Lower"
)

# SAR
sar = go.Scatter(x=df["date"], y=df["SAR"], mode="markers", name="SAR")

# MACD
macd = go.Scatter(x=df["date"], y=df["MACD"], mode="lines", name="MACD")
macd_signal = go.Scatter(
    x=df["date"], y=df["MACD_SIGNAL"], mode="lines", name="MACD Signal"
)
macd_hist = go.Bar(x=df["date"], y=df["MACD_HIST"], name="MACD Hist")

# KDJ
kdj_k = go.Scatter(x=df["date"], y=df["KDJ_K"], mode="lines", name="KDJ %K")
kdj_d = go.Scatter(x=df["date"], y=df["KDJ_D"], mode="lines", name="KDJ %D")
kdj_j = go.Scatter(x=df["date"], y=df["KDJ_J"], mode="lines", name="KDJ %J")

# Layout
layout = go.Layout(
    title="Stock Analysis with Indicators",
    xaxis={"title": "Date"},
    yaxis={"title": "Price"},
    xaxis_rangeslider_visible=False,
)

# Combine all traces into a single figure
fig = go.Figure(
    data=[
        candlestick,
        #   ma,
        ema,
        boll_upper,
        boll_lower,
        #   sar,
        #   macd,
        #   macd_signal,
        #   macd_hist,
        #   kdj_k,
        #   kdj_d,
        #   kdj_j
    ],
    layout=layout,
)
# Show plot
fig.show()

rsi = go.Scatter(x=df["date"], y=df["RSI"], mode="lines", name="RSI", yaxis="y2")

fig = go.Figure(data=[rsi], layout=layout)
# Show plot
fig.show()

raw_ohlcvs.to_csv("/home/al/.zipline/data/ccxt/eth.csv", index=False)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Optional: to make plots look nicer
plt.style.use("seaborn")

def parabolic_sar(high, low, close, af_start=0.02, af_increment=0.02, af_max=0.2):
    n = len(close)
    sar = [0] * n
    af = af_start
    ep = high[0]
    uptrend = True

    for i in range(1, n):
        if uptrend:
            sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
            if low[i] < sar[i]:
                uptrend = False
                sar[i] = ep
                ep = low[i]
                af = af_start
        else:
            sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
            if high[i] > sar[i]:
                uptrend = True
                sar[i] = ep
                ep = high[i]
                af = af_start

        if uptrend:
            if high[i] > ep:
                ep = high[i]
                af = min(af + af_increment, af_max)
        else:
            if low[i] < ep:
                ep = low[i]
                af = min(af + af_increment, af_max)

    return sar


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def macd(close, fast_period=12, slow_period=26, signal_period=9):
    macd_line = ema(close, fast_period) - ema(close, slow_period)
    signal_line = ema(macd_line, signal_period)
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram


def stochastic_k(high, low, close, period=14):
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    return k


def kdj(high, low, close, period=14):
    k = stochastic_k(high, low, close, period)
    d = k.rolling(window=3).mean()
    j = 3 * k - 2 * d
    return k, d, j


def rsi(close, period=14):
    delta = close.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

np.random.seed(42)
dates = pd.date_range(start="2023-01-01", periods=100)
close_prices = pd.Series(np.random.normal(loc=100, scale=1, size=100), index=dates)
high_prices = close_prices + np.random.normal(loc=1, scale=0.5, size=100)
low_prices = close_prices - np.random.normal(loc=1, scale=0.5, size=100)

data = pd.DataFrame({"High": high_prices, "Low": low_prices, "Close": close_prices})
data

data["SAR"] = parabolic_sar(data["High"], data["Low"], data["Close"])
data["MACD_Line"], data["Signal_Line"], data["MACD_Histogram"] = macd(data["Close"])
data["K"], data["D"], data["J"] = kdj(data["High"], data["Low"], data["Close"])
data["RSI"] = rsi(data["Close"])

fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(12, 18))

# Plot Close price and SAR
axes[0].plot(data.index, data["Close"], label="Close Price")
axes[0].plot(data.index, data["SAR"], label="SAR", color="r", linestyle="--")
axes[0].set_title("Close Price and SAR")
axes[0].legend()

# Plot MACD
axes[1].plot(data.index, data["MACD_Line"], label="MACD Line", color="b")
axes[1].plot(data.index, data["Signal_Line"], label="Signal Line", color="r")
axes[1].bar(data.index, data["MACD_Histogram"], label="MACD Histogram", color="g")
axes[1].set_title("MACD")
axes[1].legend()

# Plot KDJ
axes[2].plot(data.index, data["K"], label="%K", color="b")
axes[2].plot(data.index, data["D"], label="%D", color="r")
axes[2].plot(data.index, data["J"], label="%J", color="g")
axes[2].set_title("KDJ")
axes[2].legend()

# Plot RSI
axes[3].plot(data.index, data["RSI"], label="RSI", color="purple")
axes[3].axhline(70, color="r", linestyle="--", label="Overbought")
axes[3].axhline(30, color="g", linestyle="--", label="Oversold")
axes[3].set_title("RSI")
axes[3].legend()

plt.tight_layout()
plt.show()

## Fetch historical stock data for Apple Inc. (AAPL)
ticker = "AAPL"
data = yf.download(ticker, start="2022-01-01", end="2023-01-01")
closing_prices = data["close"].values

## Kalman Filter implementation
n_timesteps = len(closing_prices)
dt = 1.0  ## time step
A = np.array([[1, dt], [0, 1]])
H = np.array([[1, 0]])
Q = np.array([[1, 0], [0, 1]])  ## process noise covariance
R = np.array([[10]])  ## measurement noise covariance
x = np.zeros((2, n_timesteps))  ## state vector [price, drift]
P = np.zeros((2, 2, n_timesteps))  ## error covariance
filtered_price = np.zeros(n_timesteps)  ## filtered prices

## Initial estimates
x[:, 0] = [closing_prices[0], 0]  ## initial state estimate
P[:, :, 0] = np.eye(2) * 1000  ## initial error covariance

for t in range(1, n_timesteps):
    ## Prediction
    x[:, t] = A @ x[:, t - 1]
    P[:, :, t] = A @ P[:, :, t - 1] @ A.T + Q

    ## Update
    K = P[:, :, t] @ H.T @ np.linalg.inv(H @ P[:, :, t] @ H.T + R)
    x[:, t] = x[:, t] + K @ (closing_prices[t] - H @ x[:, t])
    P[:, :, t] = (np.eye(2) - K @ H) @ P[:, :, t]

    ## Store the filtered price
    filtered_price[t] = x[0, t]

## Plotting results
plt.figure(figsize=(14, 7))
plt.plot(closing_prices, label="Observed Prices")
plt.plot(filtered_price, label="Filtered Prices", linestyle="dashed")
plt.title(f"{ticker} Stock Prices: Observed vs. Filtered")
plt.xlabel("Time")
plt.ylabel("Price")
plt.legend()
plt.show()

data = pd.read_csv("eth.csv", index_col="timestamp")
data

def identify_swings(data, window=1):
    data["Swing_high"] = data["high"][
        (data["high"].shift(window) < data["high"])
        & (data["high"].shift(-window) < data["high"])
    ]
    data["Swing_low"] = data["low"][
        (data["low"].shift(window) > data["low"])
        & (data["low"].shift(-window) > data["low"])
    ]
    return data


identify_swings(data)

def find_order_blocks(data, threshold=0.01):
    data["Order_Block"] = data["close"].pct_change().abs() > threshold
    return data


find_order_blocks(data)

def identify_liquidity_pools(data):
    ## Simple method: mark previous highs/lows as liquidity pools
    data["Liquidity_Pool_low"] = data["low"].rolling(window=20).min()
    data["Liquidity_Pool_high"] = data["high"].rolling(window=20).max()
    data["Liquidity_Pool"] = (
        data["high"].rolling(window=20).max() - data["low"].rolling(window=20).min()
    )
    return data


identify_liquidity_pools(data)

def detect_bos(data):
    data["BOS"] = (data["close"] > data["high"].shift(1)) | (
        data["close"] < data["low"].shift(1)
    )
    return data


def detect_fvg(data):
    data["FVG"] = (data["high"].shift(1) - data["low"]) > 0
    return data


detect_bos(data)

detect_fvg(data)

import plotly.graph_objects as go
from plotly.subplots import make_subplots

## Initialize figure
fig = make_subplots(rows=1, cols=1)

## Add candlestick chart
fig.add_trace(
    go.Candlestick(
        x=data.index,
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
        name="Candlestick",
    )
)

## Add swing highs and lows
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["Swing_high"],
        mode="markers",
        marker=dict(color="red", symbol="triangle-up", size=10),
        name="Swing high",
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["Swing_low"],
        mode="markers",
        marker=dict(color="green", symbol="triangle-down", size=10),
        name="Swing low",
    )
)

## Customize layout
fig.update_layout(
    title="Market Data with Swing highs and lows",
    xaxis_title="Date",
    yaxis_title="Price",
    template="plotly_dark",
)

## Show the figure
fig.show()

## !wget -nc https://lazyprogrammer.me/course_files/SPY.csv

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import itertools

df = pd.read_csv("SPY.csv", index_col="Date", parse_dates=True)

df["FastSMA"] = df["Close"].rolling(16).mean()
df["SlowSMA"] = df["Close"].rolling(33).mean()

df["LogReturn"] = np.log(df["Close"]).diff()

Ntest = 1000
train = df.iloc[:-Ntest].copy()
test = df.iloc[-Ntest:].copy()

class Env:
    def __init__(self, df, feats):
        self.df = df
        self.n = len(df)
        self.current_idx = 0
        self.action_space = [0, 1, 2]  ## BUY, SELL, HOLD
        self.invested = 0

        self.states = self.df[feats].to_numpy()
        self.rewards = self.df["LogReturn"].to_numpy()
        self.total_buy_and_hold = 0

    def reset(self):
        self.current_idx = 0
        self.total_buy_and_hold = 0
        self.invested = 0
        return self.states[self.current_idx]

    def step(self, action):
        ## need to return (next_state, reward, done)
        self.current_idx += 1

        if self.current_idx >= self.n:
            raise Exception("Episode already done")

        if action == 0:  ## BUY
            self.invested = 1
        elif action == 1:  ## SELL
            self.invested = 0

        ## Compute reward
        if self.invested:
            reward = self.rewards[self.current_idx]
        else:
            reward = 0

        ## State transition
        next_state = self.states[self.current_idx]

        self.total_buy_and_hold += self.rewards[self.current_idx]

        ## Check if the episode is done
        done = self.current_idx >= self.n - 1

        return next_state, reward, done

class Agent:
    def __init__(self):
        self.is_invested = False

    def act(self, state):
        assert len(state) == 2  ## Ensure state has two elements (fast, slow)

        ## (fast, slow)
        if state[0] > state[1] and not self.is_invested:
            self.is_invested = True
            return 0  ## Buy

        if state[0] < state[1] and self.is_invested:
            self.is_invested = False
            return 1  ## Sell

        return 2  ## Do nothing

def play_one_episode(agent, env):
    state = env.reset()
    done = False
    total_reward = 0
    agent.is_invested = False

    while not done:
        action = agent.act(state)
        next_state, reward, done = env.step(action)
        total_reward += reward
        state = next_state

    return total_reward

train_env = Env(train, ["FastSMA", "SlowSMA"])
test_env = Env(test, ["FastSMA", "SlowSMA"])
agent = Agent()

train_reward = play_one_episode(agent, train_env)

test_reward = play_one_episode(agent, test_env)

train_reward, train_env.total_buy_and_hold

test_reward, test_env.total_buy_and_hold

## Download DAX data from Yahoo Finance
data = ohlcvs["eth"]
data.columns = data.columns.str.title()

import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots


## Calculate EMAs
def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()


data["EMA_Short"] = calculate_ema(data["Close"], 20)
data["EMA_Long"] = calculate_ema(data["Close"], 50)


## Calculate RSI
def calculate_rsi(data, period):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


data["RSI"] = calculate_rsi(data["Close"], 14)


## Calculate Bollinger Bands
def calculate_bollinger_bands(data, period, num_std):
    rolling_mean = data.rolling(window=period).mean()
    rolling_std = data.rolling(window=period).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return upper_band, rolling_mean, lower_band


data["BB_High"], data["BB_Mid"], data["BB_Low"] = calculate_bollinger_bands(
    data["Close"], 20, 2
)
data["BB_EMA"] = calculate_ema(data["BB_Mid"], 20)

## Create signals
data["EMA_Cross_Signal"] = np.where(data["EMA_Short"] > data["EMA_Long"], 1, 0)
data["RSI_Signal"] = np.where((data["RSI"] > 70) | (data["RSI"] < 30), 1, 0)
data["BB_EMA_Signal"] = np.where(
    (data["Close"] > data["BB_High"]) | (data["Close"] < data["BB_Low"]), 1, 0
)

## Combine signals
data["Combined_Signal"] = (
    data["EMA_Cross_Signal"] + data["RSI_Signal"] + data["BB_EMA_Signal"]
)

## Calculate performance
data["Returns"] = data["Close"].pct_change()
data["Strategy_Returns"] = data["Returns"] * data["Combined_Signal"].shift(1)

cumulative_returns = (1 + data["Returns"]).cumprod()
cumulative_strategy_returns = (1 + data["Strategy_Returns"]).cumprod()

## Create subplots
fig = make_subplots(
    rows=4,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    subplot_titles=(
        "DAX Price and EMAs",
        "RSI",
        "Bollinger Bands and BB EMA",
        "Performance Comparison",
    ),
)

## Plot 1: Price and EMAs
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["Close"],
        name="Close Price",
        line=dict(color="blue", width=2),
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["EMA_Short"],
        name="EMA Short",
        line=dict(color="orange", width=1.5),
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["EMA_Long"],
        name="EMA Long",
        line=dict(color="green", width=1.5),
    ),
    row=1,
    col=1,
)

## Plot 2: RSI
fig.add_trace(
    go.Scatter(
        x=data.index, y=data["RSI"], name="RSI", line=dict(color="purple", width=1.5)
    ),
    row=2,
    col=1,
)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

## Plot 3: Bollinger Bands
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["Close"],
        name="Close Price",
        line=dict(color="blue", width=2),
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["BB_High"],
        name="BB High",
        line=dict(color="red", width=1.5),
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["BB_Low"],
        name="BB Low",
        line=dict(color="green", width=1.5),
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["BB_EMA"],
        name="BB EMA",
        line=dict(color="orange", width=1.5),
    ),
    row=3,
    col=1,
)

## Plot 4: Performance Comparison
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=cumulative_returns,
        name="Buy and Hold",
        line=dict(color="blue", width=2),
    ),
    row=4,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=cumulative_strategy_returns,
        name="Strategy",
        line=dict(color="red", width=2),
    ),
    row=4,
    col=1,
)

## Update layout
fig.update_layout(height=1200, width=1200, title_text="DAX Trading Strategy Backtest")
fig.update_xaxes(rangeslider_visible=False)
fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="Price", row=3, col=1)
fig.update_yaxes(title_text="Cumulative Returns", row=4, col=1)

## Show the interactive plot
fig.show()

## Print performance metrics
print(f"Buy and Hold Return: {cumulative_returns.iloc[-1]:.2f}")
print(f"Strategy Return: {cumulative_strategy_returns.iloc[-1]:.2f}")

df = data.loc["2022-01-01":, :].reset_index()
df = df.rename(columns={"index": "Date"})

## Assume df has 'Date', 'Open', 'High', 'Low', 'Close', 'Volume'
## Parameters
price_step = 0.01  ## 1%
tp_target = 0.015  ## 1.5%
initial_order_amount = 1000  ## example amount in USDT
safety_order_amount = 1000  ## example amount in USDT
amount_multiplier = 1.1  ## Safety order multiplier
max_safety_orders = 8  ## Maximum number of safety orders

## Initialize variables
capital = 100000  ## Initial capital in USDT
position_size = 0
entry_price = 2000
safety_orders = 0
equity_curve = []

## df[df.index == '2024-01-01']

## Simulate the strategy
for i in range(1, len(df)):
    ## Price drop condition (Trigger safety order)
    if (df["Close"].iloc[i] < entry_price * (1 - price_step)) and (
        safety_orders < max_safety_orders
    ):
        safety_orders += 1
        entry_price = (
            entry_price * position_size + df["Close"].iloc[i] * safety_order_amount
        ) / (position_size + safety_order_amount)
        position_size += safety_order_amount * (amount_multiplier**safety_orders)

    ## Take profit condition
    if df["Close"].iloc[i] >= entry_price * (1 + tp_target):
        profit = position_size * tp_target
        capital += profit
        position_size = 0
        safety_orders = 0
        entry_price = df["Close"].iloc[i]

    equity_curve.append(capital)

equity_curve

## Convert equity curve to DataFrame for analysis
equity_curve = pd.Series(equity_curve, index=df["Date"])

## Calculate Total Return
total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1

## Calculate Daily Returns
daily_returns = equity_curve.pct_change().dropna()

## Sharpe Ratio (assuming risk-free rate is 0)
sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()

## Maximum Drawdown
rolling_max = equity_curve.cummax()
drawdown = (equity_curve - rolling_max) / rolling_max
max_drawdown = drawdown.min()

## Win Rate and Profit Factor
## Assuming we tracked all trades, not just the final equity curve
profits = []  ## list to hold profits of individual trades
losses = []  ## list to hold losses of individual trades

## You would populate profits and losses based on your trade executions
## This is a simplified representation
for trade in trades:  ## assume trades is a list of trade results
    if trade > 0:
        profits.append(trade)
    else:
        losses.append(trade)

win_rate = len([p for p in profits if p > 0]) / len(trades)
profit_factor = sum(profits) / abs(sum(losses))

## Output results
print(f"Total Return: {total_return:.2%}")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Maximum Drawdown: {max_drawdown:.2%}")
print(f"Win Rate: {win_rate:.2%}")
print(f"Profit Factor: {profit_factor:.2f}")

correlation_matrix = log_returns.corr()

## Plot the correlation of 'ETH' with other assets
eth_correlation = correlation_matrix["eth"].sort_values(ascending=False)

## Plot the correlation of 'ETH' with other assets
plt.figure(figsize=(20, 20))
sns.barplot(x=eth_correlation.values, y=eth_correlation.index, palette="coolwarm")
plt.title("Correlation of ETH with Other Assets")
plt.xlabel("Assets")
plt.ylabel("Correlation")
plt.show()

## Compute the correlation matrix
correlation_matrix = log_returns.corr()
correlation_matrix = correlation_matrix.fillna(0).sort_index(axis=0).sort_index(axis=1)
correlation_matrix
sns.clustermap(correlation_matrix, cmap="coolwarm")

eth_price = ohlcvs[ohlcvs["ticker"] == "eth"].dropna()
eth_returns = returns[["eth"]].dropna()
eth_log_returns = log_returns[["eth"]].dropna()

## Plot histograms and boxplots for both returns
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

## Histogram of stock returns
sns.histplot(eth_returns["eth"], bins=10, kde=True, ax=axes[0, 0])
axes[0, 0].set_title("Histogram of Returns")

## Boxplot of stock returns
sns.boxplot(y=eth_returns["eth"], ax=axes[0, 1])
axes[0, 1].set_title("Boxplot of Stock Returns")

## Histogram of log returns
sns.histplot(eth_log_returns["eth"], bins=10, kde=True, ax=axes[1, 0])
axes[1, 0].set_title("Histogram of Log Returns")

## Boxplot of log returns
sns.boxplot(y=eth_log_returns["eth"], ax=axes[1, 1])
axes[1, 1].set_title("Boxplot of Log Returns")

plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 10))

stats.probplot(eth_log_returns["eth"], dist="norm", plot=plt)
plt.title("QQ Plot of Ethereum Log Returns")
plt.xlabel("Theoretical Quantiles")
plt.ylabel("Sample Quantiles")
plt.grid(True)
plt.show()

## Extract the log returns series
data = eth_log_returns["eth"]

## Perform the Shapiro-Wilk test
statistic, p_value = stats.shapiro(data)

## Print the results
print(f"Shapiro-Wilk Test Statistic: {statistic}")
print(f"P-value: {p_value}")

## Interpret the result
alpha = 0.05  ## significance level
if p_value > alpha:
    print("The data looks normally distributed (fail to reject H0).")
else:
    print("The data does not look normally distributed (reject H0).")

## Extract the log returns series
data = eth_log_returns["eth"]

## Perform the Kolmogorov-Smirnov test against a normal distribution
## Assuming normal distribution with mean 0 and standard deviation 1
statistic, p_value = stats.kstest(data, "norm", args=(data.mean(), data.std()))

## Print the results
print(f"Kolmogorov-Smirnov Test Statistic: {statistic}")
print(f"P-value: {p_value}")

## Interpret the result
alpha = 0.05  ## significance level
if p_value > alpha:
    print("The data looks normally distributed (fail to reject H0).")
else:
    print("The data does not look normally distributed (reject H0).")

from scipy import stats

## Z-score method to identify outliers
z_scores = np.abs(stats.zscore(data))
outliers = (z_scores > 3).sum()
outliers

from sklearn.decomposition import PCA


def fit_pca(returns, num_factor_exposures, svd_solver):
    pca = PCA(n_components=num_factor_exposures, svd_solver=svd_solver).fit(returns)
    return pca


num_factor_exposures = 20
pca = fit_pca(returns, num_factor_exposures, "full")
pca.components_.shape

plt.bar(np.arange(20), pca.explained_variance_ratio_)

np.arange(num_factor_exposures)

def factor_betas(pca, factor_beta_indices, factor_beta_columns):
    assert len(factor_beta_indices.shape) == 1
    assert len(factor_beta_columns.shape) == 1

    return pd.DataFrame(pca.components_.T, factor_beta_indices, factor_beta_columns)


risk_model = {}
risk_model["factor_betas"] = factor_betas(
    pca, returns.columns.values, np.arange(num_factor_exposures)
)
risk_model["factor_betas"]

def factor_returns(pca, returns, factor_return_indices, factor_return_columns):
    assert len(factor_return_indices.shape) == 1
    assert len(factor_return_columns.shape) == 1
    return pd.DataFrame(
        pca.transform(returns), factor_return_indices, factor_return_columns
    )


risk_model["factor_returns"] = factor_returns(
    pca, returns, returns.index, np.arange(num_factor_exposures)
)
risk_model["factor_returns"].cumsum().plot(legend=None)

def factor_cov_matrix(factor_returns, ann_factor):
    return np.diag(factor_returns.var(axis=0, ddof=1) * ann_factor)


ann_factor = 252
risk_model["factor_cov_matrix"] = factor_cov_matrix(
    risk_model["factor_returns"], ann_factor
)
risk_model["factor_cov_matrix"].shape

def idiosyncratic_var_matrix(returns, factor_returns, factor_betas, ann_factor):
    common_returns = pd.DataFrame(
        np.dot(factor_returns, factor_betas.T), returns.index, returns.columns
    )
    idiosyncratic_returns = returns - common_returns
    return pd.DataFrame(
        factor_cov_matrix(idiosyncratic_returns, ann_factor),
        returns.columns,
        returns.columns,
    )


risk_model["idiosyncratic_var_matrix"] = idiosyncratic_var_matrix(
    returns, risk_model["factor_returns"], risk_model["factor_betas"], ann_factor
)
risk_model["idiosyncratic_var_matrix"]

def idiosyncratic_var_vector(returns, idiosyncratic_var_matrix):
    return pd.DataFrame(np.diag(idiosyncratic_var_matrix), index=returns.columns)


risk_model["idiosyncratic_var_vector"] = idiosyncratic_var_vector(
    returns, risk_model["idiosyncratic_var_matrix"]
)
risk_model["idiosyncratic_var_vector"].sort_values(by=0, ascending=False)

def predict_portfolio_risk(
    factor_betas, factor_cov_matrix, idiosyncratic_var_matrix, weights
):
    assert len(factor_cov_matrix.shape) == 2
    B = factor_betas.values
    S = idiosyncratic_var_matrix.values
    X = weights.values
    F = factor_cov_matrix
    return np.sqrt(X.T @ (B @ F @ B.T + S) @ X)[0][0]


all_weights = pd.DataFrame(
    np.repeat(1 / len(returns.columns), len(returns.columns)), returns.columns
)

predict_portfolio_risk(
    risk_model["factor_betas"],
    risk_model["factor_cov_matrix"],
    risk_model["idiosyncratic_var_matrix"],
    all_weights,
)
