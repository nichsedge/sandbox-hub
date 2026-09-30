import pandas as pd
import world_bank_data as wb

wb.get_topics()

wb.get_sources()

df = wb.get_series("NY.GDP.MKTP.CD", mrv=4)

df = pd.DataFrame(df)

import pandas as pd

# World Bank API URL for Indonesia GDP (current US$)
url = "http://api.worldbank.org/v2/en/country/IDN/indicator/NY.GDP.MKTP.CD?format=csv"

# Download the data
gdp_data = pd.read_csv(url)

# Display the first few rows of the data
# print(gdp_data.head())

gdp_data
