import numpy as np
import matplotlib.pyplot as plt

# Generate data for fat-tailed distribution (e.g., power-law distribution)
fat_tail_data = np.random.zipf(2, 1000)  # Zipf distribution with parameter 2

# Generate data for thin-tailed distribution (e.g., normal distribution)
thin_tail_data = np.random.normal(
    0, 1, 1000
)  # Normal distribution with mean 0 and standard deviation 1

# Create histogram
plt.figure(figsize=(10, 5))

# Fat-tailed distribution
plt.subplot(1, 2, 1)
plt.hist(fat_tail_data, bins=50, color="blue", alpha=0.7)
plt.title("Fat-tailed Distribution")

# Thin-tailed distribution
plt.subplot(1, 2, 2)
plt.hist(thin_tail_data, bins=50, color="green", alpha=0.7)
plt.title("Thin-tailed Distribution")

plt.tight_layout()
plt.show()

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


def plot_distribution_comparison(sample_sizes):
    fig, axes = plt.subplots(len(sample_sizes), 3, figsize=(15, 5 * len(sample_sizes)))
    fig.suptitle("Comparison of Distributions Approaching Normal", fontsize=16)

    for i, n in enumerate(sample_sizes):
        # Uniform Distribution
        uniform_samples = np.random.uniform(0, 1, n)
        axes[i, 0].hist(uniform_samples, bins=50, density=True, alpha=0.7)
        axes[i, 0].set_title(f"Uniform (n={n})")

        # Binomial Distribution
        binomial_samples = np.random.binomial(100, 0.5, n)
        axes[i, 1].hist(binomial_samples, bins=50, density=True, alpha=0.7)
        axes[i, 1].set_title(f"Binomial (n={n})")

        # Pareto Distribution
        pareto_samples = stats.pareto.rvs(3, size=n)  # shape parameter = 3
        axes[i, 2].hist(pareto_samples, bins=50, density=True, alpha=0.7)
        axes[i, 2].set_title(f"Pareto (n={n})")

        for ax in axes[i]:
            ax.set_ylabel("Density")
            ax.set_xlabel("Value")

    plt.tight_layout()
    plt.show()


# Sample sizes to visualize
sample_sizes = [100, 1000, 10000, 100000]

# Generate and plot the distributions
plot_distribution_comparison(sample_sizes)

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

# Set random seed for reproducibility
np.random.seed(42)

# Sample size
sample_size = 10000

# Generate samples from different distributions
pareto_samples = np.random.pareto(a=3, size=sample_size)  # Pareto distribution
uniform_samples = np.random.uniform(
    low=0, high=1, size=sample_size
)  # Uniform distribution
binomial_samples = np.random.binomial(
    n=10, p=0.5, size=sample_size
)  # Binomial distribution

# Generate standard normal distribution for comparison
normal_samples = np.random.normal(loc=0, scale=1, size=sample_size)

# Plotting histograms
plt.figure(figsize=(18, 6))

# Pareto distribution
plt.subplot(1, 3, 1)
plt.hist(
    pareto_samples,
    bins=50,
    density=True,
    alpha=0.6,
    color="g",
    label="Pareto Distribution",
)
x = np.linspace(min(pareto_samples), max(pareto_samples), 100)
plt.plot(
    x,
    stats.norm.pdf(x, np.mean(pareto_samples), np.std(pareto_samples)),
    "r-",
    lw=2,
    label="Normal Distribution",
)
plt.title("Pareto Distribution")
plt.legend()

# Uniform distribution
plt.subplot(1, 3, 2)
plt.hist(
    uniform_samples,
    bins=50,
    density=True,
    alpha=0.6,
    color="b",
    label="Uniform Distribution",
)
x = np.linspace(min(uniform_samples), max(uniform_samples), 100)
plt.plot(
    x,
    stats.norm.pdf(x, np.mean(uniform_samples), np.std(uniform_samples)),
    "r-",
    lw=2,
    label="Normal Distribution",
)
plt.title("Uniform Distribution")
plt.legend()

# Binomial distribution
plt.subplot(1, 3, 3)
plt.hist(
    binomial_samples,
    bins=50,
    density=True,
    alpha=0.6,
    color="orange",
    label="Binomial Distribution",
)
x = np.linspace(min(binomial_samples), max(binomial_samples), 100)
plt.plot(
    x,
    stats.norm.pdf(x, np.mean(binomial_samples), np.std(binomial_samples)),
    "r-",
    lw=2,
    label="Normal Distribution",
)
plt.title("Binomial Distribution")
plt.legend()

plt.suptitle("Comparison of Different Distributions with a Normal Distribution")
plt.show()

# !pip install powerlaw

import numpy as np
import matplotlib.pyplot as plt


def generate_power_law(alpha, size=10000, xmin=1):
    """Generate a power-law distribution with exponent alpha."""
    r = np.random.uniform(0, 1, size)
    return xmin * (1 - r) ** (-1 / (alpha - 1))


# Parameters
alphas = [1.5, 2.0, 2.5, 3.0, 3.5]
size = 10000  # Number of samples
xmin = 1  # Minimum value

# Plotting
plt.figure(figsize=(10, 6))

for alpha in alphas:
    data = generate_power_law(alpha, size, xmin)
    plt.hist(data, bins=100, density=True, histtype="step", label=f"alpha = {alpha}")

plt.xscale("log")
plt.yscale("log")
plt.xlabel("Value")
plt.ylabel("Density")
plt.title("Power Law Distributions with Different Alpha")
plt.legend()
plt.show()

import numpy as np
import matplotlib.pyplot as plt


def power_law(x, alpha):
    return x ** (-alpha)


def simulate_power_law(alpha, xmin, xmax, num_points):
    x = np.linspace(xmin, xmax, num_points)
    y = power_law(x, alpha)
    return x, y


# Set up the plot
plt.figure(figsize=(12, 8))

# Simulate and plot for different alpha values
alpha_values = [1.5, 2.0, 2.5, 3.0]
colors = ["r", "g", "b", "purple"]

for alpha, color in zip(alpha_values, colors):
    x, y = simulate_power_law(alpha, 1, 100, 1000)
    plt.loglog(x, y, color=color, label=f"α = {alpha}")

plt.title("Power Law Distributions with Different α Values")
plt.xlabel("x")
plt.ylabel("P(x)")
plt.legend()
plt.grid(True)

plt.show()

import numpy as np
import matplotlib.pyplot as plt
from powerlaw import Fit, plot_ccdf

# Generate example data following a power law
np.random.seed(42)
data = (
    np.random.pareto(a=2.5, size=1000) + 1
)  # Pareto distribution (shifted to avoid zero)

# Fit the power law model
fit = Fit(data)

# Print the estimated alpha value
print(f"Estimated alpha: {fit.alpha:.2f}")

# Plot the Complementary Cumulative Distribution Function (CCDF)
plt.figure(figsize=(10, 6))
plot_ccdf(data, linestyle="--", color="blue", label="Data")
fit.power_law.plot_ccdf(color="red", linestyle="-", label="Power Law Fit")
plt.title("Power Law Fit to Data")
plt.xlabel("x")
plt.ylabel("CCDF")
plt.legend()
plt.grid(True)
plt.show()

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import lognorm

# Parameters for the log-normal distribution
shape = (
    0.954  # Shape parameter (standard deviation of the underlying normal distribution)
)
scale = np.exp(0.5)  # Scale parameter (mean of the underlying normal distribution)

# Generate random samples from a log-normal distribution
data = lognorm.rvs(shape, scale=scale, size=1000)


# Compute the CCDF
def compute_ccdf(data):
    data_sorted = np.sort(data)[::-1]
    ccdf = np.arange(1, len(data_sorted) + 1) / len(data_sorted)
    return data_sorted, ccdf


# Get the CCDF values
x, ccdf = compute_ccdf(data)

# Plot the CCDF
plt.figure(figsize=(10, 6))
plt.plot(x, ccdf, "b-", label="Log-Normal Data CCDF")

plt.title("CCDF of Log-Normal Distribution")
plt.xlabel("x")
plt.ylabel("CCDF")
plt.xscale("log")
plt.yscale("log")
plt.legend()
plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.show()

import numpy as np
import matplotlib.pyplot as plt


def cauchy_pdf(x, x0, gamma):
    """
    Probability Density Function of the Cauchy distribution.

    Parameters:
    x (float or array): The input value(s)
    x0 (float): The location parameter
    gamma (float): The scale parameter

    Returns:
    float or array: The PDF value(s)
    """
    return 1 / (np.pi * gamma * (1 + ((x - x0) / gamma) ** 2))


def cauchy_cdf(x, x0, gamma):
    """
    Cumulative Distribution Function of the Cauchy distribution.

    Parameters:
    x (float or array): The input value(s)
    x0 (float): The location parameter
    gamma (float): The scale parameter

    Returns:
    float or array: The CDF value(s)
    """
    return 1 / np.pi * np.arctan((x - x0) / gamma) + 0.5


def generate_cauchy_samples(n, x0, gamma):
    """
    Generate random samples from the Cauchy distribution.

    Parameters:
    n (int): Number of samples to generate
    x0 (float): The location parameter
    gamma (float): The scale parameter

    Returns:
    array: Array of n samples from the Cauchy distribution
    """
    u = np.random.uniform(0, 1, n)
    return x0 + gamma * np.tan(np.pi * (u - 0.5))


# Example usage
x0 = 0  # location parameter
gamma = 1  # scale parameter

# Generate x values
x = np.linspace(-10, 10, 1000)

# Calculate PDF and CDF
pdf_values = cauchy_pdf(x, x0, gamma)
cdf_values = cauchy_cdf(x, x0, gamma)

# Generate random samples
samples = generate_cauchy_samples(1000, x0, gamma)

# Plotting
plt.figure(figsize=(12, 4))

plt.subplot(131)
plt.plot(x, pdf_values)
plt.title("Cauchy PDF")
plt.xlabel("x")
plt.ylabel("PDF")

plt.subplot(132)
plt.plot(x, cdf_values)
plt.title("Cauchy CDF")
plt.xlabel("x")
plt.ylabel("CDF")

plt.subplot(133)
plt.hist(samples, bins=50, density=True, alpha=0.7)
plt.title("Cauchy Random Samples")
plt.xlabel("x")
plt.ylabel("Frequency")

plt.tight_layout()
plt.show()

import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from scipy.stats import norm

# Parameters
symbol = "AAPL"  # Example: Apple Inc.
start_date = "2021-01-01"
end_date = "2023-01-01"
strike_price = 150
risk_free_rate = 0.05  # Example risk-free rate (annualized)
volatility = 0.2  # Example volatility (annualized)


# Fetch historical stock prices
def fetch_stock_prices(symbol, start_date, end_date):
    stock_data = yf.download(symbol, start=start_date, end=end_date)
    return stock_data["Adj Close"].values  # Use adjusted close prices


# Black-Scholes option price
def black_scholes_price(S, K, T, r, sigma, option_type="call"):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == "put":
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return price


# Hedging strategy
def calculate_hedging_errors(prices, strike_price, risk_free_rate, volatility, dt):
    num_days = len(prices)
    hedging_errors = np.zeros(num_days)
    T = np.arange(num_days) * dt  # Time to expiration for each day

    for t_index in range(1, num_days):
        S_t = prices[t_index]
        S_t_prev = prices[t_index - 1]
        option_price = black_scholes_price(
            S_t_prev, strike_price, T[t_index], risk_free_rate, volatility
        )
        d1 = (
            np.log(S_t_prev / strike_price)
            + (risk_free_rate + 0.5 * volatility**2) * T[t_index]
        ) / (volatility * np.sqrt(T[t_index]))
        hedge_ratio = norm.cdf(d1)  # Delta of the call option
        delta_position = hedge_ratio * (S_t - S_t_prev)
        hedging_errors[t_index] = delta_position - option_price

    return hedging_errors


# Main execution
prices = fetch_stock_prices(symbol, start_date, end_date)
dt = 1 / 252  # Daily time step (assuming 252 trading days per year)
hedging_errors = calculate_hedging_errors(
    prices, strike_price, risk_free_rate, volatility, dt
)

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(hedging_errors, label="Hedging Errors", color="r")
plt.title("Hedging Errors Over Time for " + symbol)
plt.xlabel("Days")
plt.ylabel("Hedging Error")
plt.legend()
plt.show()

import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Parameters
discount_rate = 0.07  # Traditional discount rate (5%)
failure_probability = 0.50  # Probability of failure (10%)

# Fetch historical Bitcoin data from Yahoo Finance
bitcoin = yf.Ticker("BTC-USD")
data = bitcoin.history(period="5y")  # Fetch all available data

# Calculate daily returns and cumulative returns
data["Daily Return"] = data["Close"].pct_change()
data["Cumulative Return"] = (1 + data["Daily Return"]).cumprod() - 1

# Convert cumulative return to price
initial_price = data["Close"].iloc[0]
data["Price"] = initial_price * (1 + data["Cumulative Return"])

# Calculate required growth rate
required_growth_rate = discount_rate + failure_probability

# Generate time periods in years based on data
data["Time"] = (data.index - data.index[0]).days / 365.25  # Time in years

# Calculate theoretical price growth with and without absorption barrier using continuous compounding
prices_no_barrier = initial_price * np.exp(discount_rate * data["Time"])
prices_with_barrier = initial_price * np.exp(required_growth_rate * data["Time"])

# Plotting
plt.figure(figsize=(14, 7))

# Plot actual Bitcoin prices
plt.plot(
    data.index,
    data["Price"],
    label="Actual Bitcoin Price",
    color="black",
    linestyle="-",
)

# Add labels and title
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.title(
    "Bitcoin Price Growth With and Without Absorption Barrier (Continuous Compounding)"
)
plt.legend()
plt.grid(True)
plt.show()

# Print required growth rate
print(f"Required Growth Rate: {required_growth_rate * 100:.2f}%")

# Plot theoretical prices
plt.plot(
    data.index,
    prices_no_barrier,
    label="Growth Without Absorption Barrier",
    color="blue",
    linestyle="--",
)
plt.plot(
    data.index,
    prices_with_barrier,
    label="Growth With Absorption Barrier",
    color="red",
    linestyle="-.",
)
