import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Optional


def simulate_stock_path(
    initial_price: float,
    mean_daily_return: float,
    daily_volatility: float,
    days: int,
    seed: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate a single stock price path using Geometric Brownian Motion approximation.

    Parameters:
    -----------
    initial_price : float
        Starting stock price (must be > 0).
    mean_daily_return : float
        Expected daily return (drift term).
    daily_volatility : float
        Daily standard deviation of returns (must be >= 0).
    days : int
        Number of simulation days (must be > 0).
    seed : int, optional
        Random seed for reproducibility.

    Returns:
    --------
    Tuple of (days_array, prices_array): NumPy arrays for x-axis (days) and simulated prices.

    Raises:
    -------
    ValueError: If parameters are invalid (e.g., non-positive initial_price or days).

    Notes:
    ------
    Uses vectorized NumPy operations for efficiency. Assumes daily compounding.
    """
    # Input validation
    if initial_price <= 0:
        raise ValueError("Initial price must be positive.")
    if daily_volatility < 0:
        raise ValueError("Daily volatility must be non-negative.")
    if days <= 0 or not isinstance(days, int):
        raise ValueError("Number of days must be a positive integer.")

    # Set seed for reproducibility if provided
    if seed is not None:
        np.random.seed(seed)

    # Generate daily returns (normal distribution)
    returns = np.random.normal(loc=mean_daily_return, scale=daily_volatility, size=days)

    # Compute price path using vectorized cumulative product (more efficient than loop)
    with np.errstate(
        over="ignore", under="ignore"
    ):  # Suppress potential numerical warnings
        price_factors = 1 + returns
        prices = initial_price * np.cumprod(price_factors)

    # Handle days=0 edge case (though validation ensures >0, for completeness)
    if days == 0:
        return np.array([]), np.array([initial_price])

    # Days array for plotting
    days_array = np.arange(days + 1)  # Includes day 0

    # Prepend initial price to make full path
    full_prices = np.concatenate(([initial_price], prices))

    return days_array, full_prices


def plot_stock_path(
    days_array: np.ndarray,
    prices: np.ndarray,
    title: str = "One Simulated Stock Price Path (10 days)",
) -> None:
    """
    Plot the simulated stock price path.

    Parameters:
    -----------
    days_array : np.ndarray
        Array of day indices.
    prices : np.ndarray
        Array of corresponding prices.
    title : str, optional
        Plot title.
    """
    plt.figure(figsize=(10, 6))  # Explicit figure size for better readability
    plt.plot(days_array, prices, marker="o", linewidth=2, markersize=4)
    plt.title(title)
    plt.xlabel("Day")
    plt.ylabel("Price")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()  # Auto-adjust layout
    plt.show()


# Example usage with parameters
initial_price = 100.0  # Initial stock price
mean_daily_return = 0.001  # Mean daily return
daily_volatility = 0.02  # Daily volatility
num_days = 10  # Number of days
random_seed = 42  # For reproducibility

# Simulate and plot
days_arr, price_path = simulate_stock_path(
    initial_price=initial_price,
    mean_daily_return=mean_daily_return,
    daily_volatility=daily_volatility,
    days=num_days,
    seed=random_seed,
)
plot_stock_path(days_arr, price_path)

import numpy as np
import matplotlib.pyplot as plt

# Parameters
S0 = 100
mu = 0.001
sigma = 0.02
days = 10
n_simulations = 1000
np.random.seed(42)

# Simulate 1000 paths
returns = np.random.normal(loc=mu, scale=sigma, size=(n_simulations, days))
price_paths = np.zeros((n_simulations, days + 1))
price_paths[:, 0] = S0

# Fill in price paths
for t in range(1, days + 1):
    price_paths[:, t] = price_paths[:, t - 1] * (1 + returns[:, t - 1])

# Plot some paths
plt.plot(price_paths[:20].T, alpha=0.5)
plt.title("20 Simulated Price Paths (10 Days)")
plt.xlabel("Day")
plt.ylabel("Price")
plt.grid(True)
plt.show()

# Analyze final prices
final_prices = price_paths[:, -1]
expected_price = np.mean(final_prices)
var_95 = np.percentile(final_prices, 5)

print(f"Expected Price after 10 days: {expected_price:.2f}")
print(f"5% Value at Risk (VaR): {S0 - var_95:.2f}")

import numpy as np
import matplotlib.pyplot as plt

# --- Simulation Settings ---
n_assets = 3
n_days = 100  # Increased days for a more interesting visualization
n_simulations = 1000
S0 = np.array([100, 50, 75])
mu = np.array([0.001, 0.0005, 0.0008])
sigma = np.array([0.02, 0.015, 0.025])

# Correlation matrix (must be symmetric and positive semi-definite)
corr_matrix = np.array([[1.0, 0.3, 0.2], [0.3, 1.0, 0.4], [0.2, 0.4, 1.0]])

# Convert to covariance matrix
cov_matrix = np.outer(sigma, sigma) * corr_matrix

# Cholesky decomposition
L = np.linalg.cholesky(cov_matrix)

# --- Generate Simulations ---
price_paths = np.zeros((n_simulations, n_assets, n_days + 1))
price_paths[:, :, 0] = S0

np.random.seed(42)
for t in range(1, n_days + 1):
    Z = np.random.normal(size=(n_simulations, n_assets))
    correlated_returns = Z @ L.T + mu
    price_paths[:, :, t] = price_paths[:, :, t - 1] * (1 + correlated_returns)

# --- Visualization Improvements ---

# 1. Individual Subplots for Each Asset
#    - Clearer separation of each asset's paths.
#    - Use different colors for clarity.
#    - Improved titles and labels.

plt.style.use("seaborn-v0_8-whitegrid")  # A clean, modern style
fig, axes = plt.subplots(n_assets, 1, figsize=(10, 12))
fig.suptitle("Simulated Asset Price Paths (5 paths per asset)", fontsize=16)

colors = ["cornflowerblue", "darkorange", "forestgreen"]

for i in range(n_assets):
    ax = axes[i]
    ax.plot(price_paths[:5, i, :].T, color=colors[i], alpha=0.8)
    ax.set_title(f"Asset {i + 1}", fontsize=12)
    ax.set_xlabel("Day")
    ax.set_ylabel("Price")
    ax.grid(True)

plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust layout to make room for suptitle
plt.show()


# 2. Single Asset with all simulations and a Confidence Interval
#    - Focus on a single asset to show the full range of outcomes.
#    - Shaded area highlights the central tendency of the simulations.

plt.figure(figsize=(12, 7))
asset_index = 0  # Focus on the first asset

# Plot all simulation paths for the chosen asset
plt.plot(price_paths[:, asset_index, :].T, color="lightgray", alpha=0.5, linewidth=0.5)

# Calculate and plot the mean path
mean_path = np.mean(price_paths[:, asset_index, :], axis=0)
plt.plot(mean_path, color="darkblue", linewidth=2, label="Mean Path")

# Calculate and plot a 50% confidence interval (25th to 75th percentile)
percentile_25 = np.percentile(price_paths[:, asset_index, :], 25, axis=0)
percentile_75 = np.percentile(price_paths[:, asset_index, :], 75, axis=0)
plt.fill_between(
    range(n_days + 1),
    percentile_25,
    percentile_75,
    color="darkblue",
    alpha=0.2,
    label="50% Confidence Interval",
)

plt.title(f"All Simulated Price Paths for Asset {asset_index + 1}", fontsize=16)
plt.xlabel("Day", fontsize=12)
plt.ylabel("Price", fontsize=12)
plt.legend()
plt.grid(True)
plt.show()


# 3. Distribution of Final Prices (Histograms)
#    - Provides a statistical summary of the simulation's end state.
#    - Shows the probability distribution of final prices for each asset.

fig, axes = plt.subplots(1, n_assets, figsize=(15, 5))
fig.suptitle("Distribution of Final Simulated Prices", fontsize=16)

for i in range(n_assets):
    ax = axes[i]
    final_prices = price_paths[:, i, -1]  # Get the prices at the last day
    ax.hist(final_prices, bins=50, color=colors[i], alpha=0.7, edgecolor="black")
    ax.axvline(
        np.mean(final_prices),
        color="red",
        linestyle="dashed",
        linewidth=1,
        label="Mean",
    )
    ax.set_title(f"Asset {i + 1}", fontsize=12)
    ax.set_xlabel("Final Price")
    ax.set_ylabel("Frequency")
    ax.legend()
    ax.grid(True)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()

import pandas as pd
import io
import os


def process_gramps_data(
    input_filename="gramps_raw.csv", output_filename="gramps_cleaned.csv"
):
    """
    Parses a specialized multi-section CSV file, reformats Person names,
    and deduplicates Person, Marriage, and Family records by updating IDs.

    Args:
        input_filename (str): The name of the input CSV file.
        output_filename (str): The name of the output CSV file.
    """
    # --- 0. Load Data ---
    try:
        with open(input_filename, "r", encoding="utf-8") as f:
            csv_data = f.read()
    except FileNotFoundError:
        print(
            f"Error: Input file '{input_filename}' not found. Please ensure it exists."
        )
        return

    # --- 1. Split the data into sections ---
    lines = csv_data.strip().split("\n")
    sections = {}
    current_section = None
    section_data = []

    # Map section names to their start indicators (first column value)
    section_map = {
        "Metadata": "Place",
        "Person": "Person",
        "Marriage": "Marriage",
        "Family": "Family",
    }

    # Identify the main sections and their raw data
    for line in lines:
        if not line.strip():
            continue

        first_col = line.split(",")[0]

        # Check if a new section is starting
        is_header_row = first_col in section_map.values()
        is_metadata_data_row = current_section == "Metadata" and first_col.startswith(
            "["
        )

        if is_header_row or (current_section is None and first_col.startswith("Place")):
            if current_section is not None:
                sections[current_section] = "\n".join(section_data)

            # Find the section name based on the indicator
            if is_header_row:
                current_section = next(
                    k for k, v in section_map.items() if v == first_col
                )
            elif first_col.startswith("Place"):
                current_section = "Metadata"

            section_data = [line]  # Start with the header line
        elif current_section:
            section_data.append(line)

    # Add the last section
    if current_section is not None:
        sections[current_section] = "\n".join(section_data)

    # --- 2. Process the 'Person' data and create ID Map ---
    if "Person" in sections:
        person_df = pd.read_csv(io.StringIO(sections["Person"]))

        # Store the original ID before modification
        person_df["Original_ID"] = person_df["Person"]

        # 2a. Move 'Surname' to last part of 'Given' and clear 'Surname'
        # Fill NaN values with empty string for safe concatenation
        person_df["Surname"] = person_df["Surname"].fillna("")
        person_df["Given"] = person_df.apply(
            lambda row: f"{row['Given']} {row['Surname']}".strip(), axis=1
        )
        person_df["Surname"] = ""

        # 2b. Deduplicate 'Person' records and determine Master IDs
        # Group by the combined 'Given' name
        master_ids = person_df.drop_duplicates(subset=["Given"], keep="first")

        # Create a mapping from all original IDs to the Master ID
        id_map = {}
        for _, row in person_df.iterrows():
            # Find the Master_ID (Original_ID of the first record with this 'Given' name)
            master_id = master_ids[master_ids["Given"] == row["Given"]][
                "Original_ID"
            ].iloc[0]
            id_map[row["Original_ID"]] = master_id

        # The final 'Person' DataFrame is just the unique records
        person_df_cleaned = master_ids.drop(columns=["Original_ID"])

    else:
        print("Warning: No 'Person' section found. Cannot perform deduplication.")
        return

    # --- 3. Helper function to update references ---
    def update_references(df, cols_to_update, id_mapping):
        """Updates IDs in specified columns of a DataFrame using the ID map."""
        for col in cols_to_update:
            if col in df.columns:
                # Use .get() with the original value as default to handle IDs not in the map
                df[col] = df[col].apply(lambda x: id_mapping.get(x, x))
        return df

    # --- 4. Update and Deduplicate 'Marriage' records ---
    if "Marriage" in sections:
        marriage_df = pd.read_csv(io.StringIO(sections["Marriage"]))
        # Update Husband and Wife IDs to their Master IDs
        marriage_df_cleaned = update_references(
            marriage_df, ["Husband", "Wife"], id_map
        )
        # Deduplicate marriages (e.g., if [I0008]-[I0055] and [I0061]-[I0055] become [I0008]-[I0055])
        marriage_df_cleaned.drop_duplicates(
            subset=["Husband", "Wife", "Date", "Place"], keep="first", inplace=True
        )
    else:
        marriage_df_cleaned = None

    # --- 5. Update and Deduplicate 'Family' records ---
    if "Family" in sections:
        family_df = pd.read_csv(io.StringIO(sections["Family"]))

        # Update Child IDs to their Master IDs
        family_df_cleaned = update_references(family_df, ["Child"], id_map)

        # Deduplicate child entries within the same family (Family ID, Child ID)
        family_df_cleaned.drop_duplicates(
            subset=["Family", "Child"], keep="first", inplace=True
        )
    else:
        family_df_cleaned = None

    # --- 6. Reconstruct and Write the CSV output ---
    output_lines = []

    # 6a. Metadata (Header)
    if "Metadata" in sections:
        output_lines.append(sections["Metadata"].strip())
        output_lines.append("")

    # 6b. Person (Cleaned)
    person_csv = person_df_cleaned.to_csv(index=False, header=True, lineterminator="\n")
    output_lines.append(person_csv.strip())
    output_lines.append("")

    # 6c. Marriage (Cleaned)
    if marriage_df_cleaned is not None and not marriage_df_cleaned.empty:
        marriage_df_cleaned.sort_values(by=["Husband", "Wife"], inplace=True)
        marriage_csv = marriage_df_cleaned.to_csv(
            index=False, header=True, lineterminator="\n"
        )
        output_lines.append(marriage_csv.strip())
        output_lines.append("")

    # 6d. Family (Cleaned)
    if family_df_cleaned is not None and not family_df_cleaned.empty:
        family_df_cleaned.sort_values(by=["Family", "Child"], inplace=True)
        family_csv = family_df_cleaned.to_csv(
            index=False, header=True, lineterminator="\n"
        )
        output_lines.append(family_csv.strip())
        output_lines.append("")

    # Write the result to the output file
    final_output = "\n".join(output_lines).strip()
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_output)

    print(f"Successfully processed and cleaned data written to '{output_filename}'.")
    print("\n--- Summary of Changes ---")
    print(f"Original Person Records: {len(person_df)}")
    print(f"Cleaned Person Records: {len(person_df_cleaned)}")
    if marriage_df_cleaned is not None:
        print(f"Original Marriage Records: {len(marriage_df)}")
        print(f"Cleaned Marriage Records: {len(marriage_df_cleaned)}")


# --- Setup and Example Usage ---

# Create a dummy gramps_raw.csv file for the example to work
example_csv_content = """Place,Title,Name,Type,Latitude,Longitude,Code,Enclosed_by,Date
Person,Surname,Given,Call,Nickname,Suffix,Prefix,Title,Gender,Birth date,Birth place,Birth source,Baptism date,Baptism place,Baptism source,Death date,Death place,Death source,Burial date,Burial place,Burial source,Note
[I0008],Qudratullah,Adnan Azis,,,,,,male,,,,,,,,,,,,,
[I0061],Qudratullah,Adnan Azis,,,,,,male,,,,,,,,,,,,,
[I0062],,Adnan Azis Qudratullah,,,,,,male,,,,,,,,,,,,, # Explicitly duplicate name
[I0000],,John Doe,,,,,,male,,,,,,,,,,,,,
[I0055],,Jane Smith,,,,,,female,,,,,,,,,,,,,
[I0056],,Kid Child,,,,,,male,,,,,,,,,,,,,

Marriage,Husband,Wife,Date,Place,Source,Note
[F0000],[I0000],[I0055],2000-01-01,,,
[F0001],[I0008],[I0055],2000-01-01,,, # Master Husband ID
[F0002],[I0061],[I0055],2000-01-01,,, # Duplicate husband ID (I0061 maps to I0008) -> MERGED
[F0003],[I0062],[I0055],2000-01-01,,, # Duplicate husband ID (I0062 maps to I0008) -> MERGED

Family,Child
[F0000],[I0056]
[F0001],[I0056]
[F0002],[I0056] # This Family ID will be merged with [F0001] if the marriage is merged.
"""

# Write the example data to the file
with open("gramps_raw.csv", "w", encoding="utf-8") as f:
    f.write(example_csv_content)

# Run the deduplication process
process_gramps_data()

# Optional: Print the content of the cleaned file
print("\n--- Content of gramps_cleaned.csv (First 20 lines) ---")
with open("gramps_cleaned.csv", "r", encoding="utf-8") as f:
    print("\n".join(f.readlines()[:20]).strip())

# Clean up the created files (optional)
# os.remove("gramps_raw.csv")
# os.remove("gramps_cleaned.csv")
