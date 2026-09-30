# from pyforbes import ForbesList


# flist = ForbesList()
# df = flist.get_df("billionaires")

# df.to_csv('data.csv')
df = pd.read_csv("data.csv")

df[["uri", "age", "category", "finalWorth", "selfMadeRank"]]

import plotly.express as px
import pandas as pd

# Create the packed bubble chart
fig = px.scatter(
    df,
    x="age",
    y="finalWorth",  # Dummy y-axis since plotly does not directly support packed bubbles
    size="finalWorth",
    color="category",
    hover_name="uri",
    size_max=60,
    title="Packed Bubble Chart of Final Worth by Age and Category",
)

# Customize the layout to hide the dummy y-axis
# fig.update_layout(yaxis=dict(showticklabels=False, showgrid=False, zeroline=False))

# Show the plot
fig.show()

import plotly.express as px
import pandas as pd

# Create the packed bubble chart
fig = px.scatter(
    df,
    x="age",
    y="selfMadeRank",  # Dummy y-axis since plotly does not directly support packed bubbles
    size="finalWorth",
    color="category",
    hover_name="uri",
    size_max=60,
    title="Packed Bubble Chart of Final Worth by Age and Self Made Score",
)

# Customize the layout to hide the dummy y-axis
# fig.update_layout(yaxis=dict(showticklabels=False, showgrid=False, zeroline=False))

# Show the plot
fig.show()

import plotly.express as px
import pandas as pd

# Create the packed bubble chart
fig = px.scatter(
    df,
    x="age",
    y="finalWorth",  # Dummy y-axis since plotly does not directly support packed bubbles
    size="finalWorth",
    color="country",
    hover_name="uri",
    size_max=60,
    title="Packed Bubble Chart of Final Worth by Age and Country",
)

# Customize the layout to hide the dummy y-axis
fig.update_layout(yaxis=dict(showticklabels=False, showgrid=False, zeroline=False))

# Show the plot
fig.show()

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Sort the DataFrame by 'finalWorth'
df = df.sort_values("finalWorth", ascending=False)
df

# Create the bar plot
plt.figure(figsize=(10, 6))
bar_plot = sns.barplot(
    x="finalWorth", y="uri", data=df.head(25), hue="category", dodge=False
)

# Customize the plot
bar_plot.set_title("Bar Chart of Final Worth Sorted by Final Worth")
bar_plot.set_xlabel("Final Worth")
bar_plot.set_ylabel("Name")

# Show the plot
plt.legend(title="Category")
plt.show()

df[df["country"] == "Indonesia"][["uri", "finalWorth", "category"]].to_csv("indo")

# Calculate the count of entries by country
country_counts = df["country"].value_counts().reset_index().head(20)
country_counts.columns = ["country", "count"]

# Create the bar plot
plt.figure(figsize=(12, 8))
bar_plot = sns.barplot(x="count", y="country", data=country_counts, palette="viridis")

# Customize the plot
bar_plot.set_title("Count of Entries by Country")
bar_plot.set_xlabel("Count")
bar_plot.set_ylabel("Country")

for index, value in enumerate(country_counts["count"]):
    bar_plot.text(value, index, f"{value}", va="center")

# Show the plot
plt.show()

# Calculate the sum of 'totalWorth' by 'country'
country_total_worth = df.groupby("country")["finalWorth"].sum().reset_index()

# Sort the data for better visualization (optional)
country_total_worth = country_total_worth.sort_values(
    by="finalWorth", ascending=False
).head(20)

# Create the bar plot
plt.figure(figsize=(12, 8))
bar_plot = sns.barplot(
    x="finalWorth", y="country", data=country_total_worth, palette="viridis"
)

# Customize the plot
bar_plot.set_title("Sum of Total Worth by Country")
bar_plot.set_xlabel("Total Worth")
bar_plot.set_ylabel("Country")

# Add the total worth numbers beside the bars
for index, value in enumerate(country_total_worth["finalWorth"]):
    bar_plot.text(value, index, f"{value:,.0f}", va="center")

# Show the plot
plt.show()

from pyforbes import ForbesList


flist = ForbesList()
df = flist.get_df("best-employers-for-new-grads", year=2022)

df.info()
