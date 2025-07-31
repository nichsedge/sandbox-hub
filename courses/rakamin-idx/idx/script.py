# %%
# import all packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as no
import warnings

warnings.filterwarnings("ignore")
pd.options.display.max_columns = 1000
pd.options.display.max_rows = 1000

# %%
# load in the dataset into a pandas dataframe
df = pd.read_csv("loan_data_2007_2014.csv", index_col=0, low_memory=False)
df.head()

# %%
# Shape of the Original dataset
print("Number of rows   :", df.shape[0])
print("Number of columns:", df.shape[1])

# %% [markdown]
# # Duplicate entries

# %%
if len(df) == len(df.member_id.unique()):
    print("No duplicate data found")
else:
    print("Some Duplicates are found")

# %% [markdown]
# # Removed all irrelevant columns

# %%
# post approval features -delinq_2yrs,revol_bal,out_prncp,total_pymnt,total_rec_prncp,total_rec_int,total_rec_late_fee,
# recoveries,collection_recovery_fee,last_pymnt_d ,last_pymnt_amnt,next_pymnt_d ,chargeoff_within_12_mths

# Around 13 features are there which are Post approval so these are not useful to predict whether the loan should be given
# to particular applicat or not

drop_cols = [
    "delinq_2yrs",
    "revol_bal",
    "out_prncp",
    "total_pymnt",
    "total_rec_prncp",
    "total_rec_int",
    "total_rec_late_fee",
    "recoveries",
    "collection_recovery_fee",
    "last_pymnt_d",
    "last_pymnt_amnt",
    "next_pymnt_d",
]
df.drop(drop_cols, axis=1, inplace=True)
# print("Features we are left with",list(df.columns))

# %%
# remove non-required columns
# Not required : id,member_id ,emp_title,url,desc,title
# zip_code : Complete zip code is not available
# out_prncp_inv - not useful as its for investors
# total_pymnt_inv - not useful as it is for investors
# last_credit_pull_d - irrelevant for approval


drop_cols = [
    "id",
    "member_id",
    "funded_amnt",
    "emp_title",
    "url",
    "desc",
    "title",
    "zip_code",
    "out_prncp_inv",
    "total_pymnt_inv",
    "last_credit_pull_d",
    "pymnt_plan",
]
df.drop(drop_cols, axis=1, inplace=True)
# print("Features we have in Dataset: ",list(df.columns))

# %%
# Shape of dataframe after removing all irrelevant features
print("Number of rows   :", df.shape[0])
print("Number of columns:", df.shape[1])

# %% [markdown]
# # NULL Values analysis & treatment

# %%
# Missing value analysis
null_df = pd.DataFrame()
null_df["Features"] = df.isnull().sum().index
null_df["Null values"] = df.isnull().sum().values
null_df["% Null values"] = (df.isnull().sum().values / df.shape[0]) * 100
null_df.sort_values(by="% Null values", ascending=False)

# %%
# We will drop the columns which are having more than 50% NULL Values
null_columns = null_df[null_df["% Null values"] >= 50]["Features"]
df.drop(columns=null_columns, inplace=True)
# df.columns                 ##Columns present in the dataset
# np.array(null_columns)     ##Columns that are removed

# %%
# Dropping the rows which are having less tham 5% of null values in that column
null_df_5 = null_df[null_df["% Null values"] < 5]["Features"]
df.dropna(subset=null_df_5, axis=0, inplace=True)

# %%
# Imputation is done for the columns having more than 5% & less than 50% null values
cols_null = np.array(
    null_df[(null_df["% Null values"] > 5) & (null_df["% Null values"] < 50)][
        "Features"
    ]
)
cols_null

# No column exists which is having null values between 5 to 50%

# %%
# Shape after removing the 100% null valued columns
print("Number of rows   :", df.shape[0])
print("Number of columns:", df.shape[1])

# %% [markdown]
# # Remove Single value Columns

# %%
# Checking number of unique values in each column. We should remove the columns that has single value.
# Those columns will not give us meaningful information
unique_val = pd.DataFrame()
unique_val["Features"] = df.nunique().index
unique_val["Unique_Values"] = df.nunique().values
unique_val.sort_values(by="Unique_Values")

# %%
# Columns that has single value are removed
df.drop(columns=unique_val[unique_val.Unique_Values == 1]["Features"], inplace=True)

# %%
# Shape after removing all the unwanted columns
print("Number of rows   :", df.shape[0])
print("Number of columns:", df.shape[1])

# Columns left in the dataset
# df.columns

df = df.reset_index(drop=True)  # Index are reset

# %%
df.head()

# %% [markdown]
# **Removing records with loan status as "Current", as the loan is currently running and we can't infer any information regarding default from such loans.**

# %%
# Target variable
df["loan_status"].value_counts()

# %%
# Removed those records which are having loan_status as 'Current' and it is irrelevant
df = df[df["loan_status"] != "Current"]

# Checked for values count
df["loan_status"].value_counts()

# %% [markdown]
# # Change the Data format of some  columns

# %%
# Term is given in '36 months' format, changed it to 36
df["term_months"] = df["term"].str.strip("months")
df.drop(columns=["term"], inplace=True)


# %%
# Function to bring the data of emp_len in year only instead of 'n years'
def func(x):
    if "<" in x:
        return 0
    elif "+" in x:
        year = int(x.split("+")[0])
        return year
    else:
        year = int(x.split(" ")[0])
        return year


df["emp_length(years)"] = df["emp_length"].apply(lambda a: func(a))
df.drop(columns=["emp_length"], inplace=True)


# %%
# Dataset after stripping
df.head()

# %%
# year , month are saved in different columns
df["earliest_cr_line_date"] = pd.to_datetime(df["earliest_cr_line"], format="%b-%y")
df["earliest_cr_line_month"] = pd.to_datetime(
    df["earliest_cr_line_date"], format="%b-%y"
).dt.strftime("%m")
df["earliest_cr_line_year"] = pd.to_datetime(
    df["earliest_cr_line_date"], format="%b-%y"
).dt.strftime("%Y")
df["issue_date"] = pd.to_datetime(df["issue_d"], format="%b-%y")
df["issue_date_month"] = pd.to_datetime(df["issue_date"], format="%b-%y").dt.strftime(
    "%m"
)
df["issue_date_year"] = pd.to_datetime(df["issue_date"], format="%b-%y").dt.strftime(
    "%Y"
)
df.drop(columns=["issue_d", "earliest_cr_line"], axis=1, inplace=True)

# %%
df.info()

# %%
df.shape

# %% [markdown]
# # Outlier treatement

# %%
# Individual Boxplot to check outliers in each feature

df_num = df.select_dtypes(include=np.number)

for i in range(len(df_num.columns)):
    sns.boxplot(df_num.iloc[:, i])
    plt.show()

# %%
# Skewness is checked for each feature
df.skew().sort_values(ascending=False)

# %%
# From the above boxplot & skewness values,
# we should treat outliers in each feature having high skewness individually

# Looking upon the quantile values of each features, we will treat outliers for the some features

# Outlier treatment for Annual income
print("Highest value in the annual income:", df["annual_inc"].max())
print("75% quantile value in the annual income:", df["annual_inc"].quantile(0.75))
print(
    "50% quantile (Mean) value in the annual income:", df["annual_inc"].quantile(0.50)
)

# Before removing outliers
print("\nSkewness Before:", df["annual_inc"].skew())
plt.figure(figsize=(10, 4))
sns.boxplot(df["annual_inc"])
plt.legend(labels=["Before removing Outliers"])
plt.show()

# We will remove the values which lies between quantile 99% to 100%
df = df[df["annual_inc"] < df["annual_inc"].quantile(0.99)]
plt.figure(figsize=(10, 4))
sns.boxplot(df["annual_inc"])
print("Skewness After:", df["annual_inc"].skew())
plt.legend(labels=["After removing Outliers"])
plt.show()

# %%
# total_acc:The total number of credit lines currently in the borrower's credit file
print("Highest value in the total_acc:", df["total_acc"].max())
print("75% quantile value in the total_acc:", df["total_acc"].quantile(0.75))
print("50% quantile (Mean) value in the total_acc:", df["total_acc"].quantile(0.50))

# Before removing outliers
print("\nSkewness Before:", df["total_acc"].skew())
plt.figure(figsize=(10, 4))
sns.boxplot(df["total_acc"])
plt.legend(labels=["Before removing Outliers"])
plt.show()

# We will remove the values which lies between quantile 98% to 100%
df = df[df["total_acc"] < df["total_acc"].quantile(0.98)]
plt.figure(figsize=(10, 4))
sns.boxplot(df["total_acc"])
plt.legend(labels=["After removing Outliers"])
print("Skewness After:", df["total_acc"].skew())
plt.show()

# %%
df.shape

# %%
# open_acc : The number of open credit lines in the borrower's credit file.
print("Highest value in the open_acc:", df["open_acc"].max())
print("75% quantile value in the open_acc:", df["open_acc"].quantile(0.75))
print("50% quantile (Mean) value in the open_acc:", df["open_acc"].quantile(0.50))

# Before removing outliers
print("\nSkewness Before:", df["open_acc"].skew())
plt.figure(figsize=(10, 4))
sns.boxplot(df["open_acc"])
plt.legend(labels=["Before removing Outliers"])
plt.show()


# We will remove the values which lies between quantile 99.9% to 100%
df = df[df["open_acc"] < df["open_acc"].quantile(0.999)]
plt.figure(figsize=(10, 4))
sns.boxplot(df["open_acc"])
plt.legend(labels=["After removing Outliers"])
print("Skewness After:", df["open_acc"].skew())
plt.show()

# %%
df.skew()

# %%
# Reset Index
df.reset_index(drop=True, inplace=True)
df.head()

# %%
df["earliest_cr_line_month"] = df["earliest_cr_line_month"].astype("int64")
df["earliest_cr_line_year"] = df["earliest_cr_line_year"].astype("int64")

# %%
df["issue_date_month"] = df["issue_date_month"].astype("int64")
df["issue_date_year"] = df["issue_date_year"].astype("int64")

# %%
df["pub_rec"] = df["pub_rec"].astype("int64")
df.info()

# %% [markdown]
# Replace

# %%
df["loan_status"] = df["loan_status"].replace(
    {
        "Does not meet the credit policy. Status:Fully Paid": "Fully Paid",
        "Does not meet the credit policy. Status:Charged Off": "Charged Off",
        "Late (31-120 days)": "Late",
        "Late (16-30 days)": "Late",
    }
)

# %% [markdown]
# ## Copy of dataset till data cleaning

# %%
# We will use this df_after_data_cleaning dataset after EDA part again
df_after_data_cleaning = df.copy()

# %% [markdown]
# # UNIVARIATE & BIVARIATE ANALYSIS

# %% [markdown]
# ### Categorical variables present after data cleaning

# %%
df.select_dtypes("object").columns

# %% [markdown]
# ### Numerical variables present after data cleaning

# %%
df.select_dtypes(include=np.number).columns

# %% [markdown]
# ## Distribution of Target variable

# %% [markdown]
# 1. From the above plot , we ca say that 14.46 % people are the loan defaulters.
# 2. There are around 5232 people of total 36194 people who are loan defaulters.

# %%
# Visualize payment status (next_pymnt_d)
payment_status = df["loan_status"].value_counts()

plt.figure(figsize=(8, 6))
payment_status.plot(kind="bar")
plt.title("Payment Status")
plt.xlabel("Payment Status")
plt.ylabel("Loan Count")
plt.show()

# %%
loan_status_counts = df["loan_status"].value_counts()

# Set up the figure and axis
fig, ax = plt.subplots()

# Plot the pie chart
ax.pie(loan_status_counts, labels=loan_status_counts.index, autopct="%1.1f%%")

# Set the title
ax.set_title("Loan Status Distribution")

# Display the chart
plt.show()


# %% [markdown]
# ## Convert target variable into numerical variable

# %%
df = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])]

# %%
# target variable converted into 1's & 0''s
# loan defaulters are charged off people therefore charged off=1
# 0 : Fully paid
# 1 : Charged off

df["loan_status"] = df["loan_status"].replace({"Fully Paid": 0, "Charged Off": 1})

# %% [markdown]
# ## Loan Purpose

# %%
# Loan purpose Vs Loan defaulters

count = df["purpose"].value_counts()
labels = count.index
values = count.values

# Percentage of loan purpose
plt.figure(figsize=(12, 10))
plt.pie(x=values, labels=labels, autopct="%0.2f%%")
plt.title("\nLoan Purpose Information", fontsize=20)
plt.legend(labels=labels, loc=(1.2, 0.7))
plt.show()

# Loan defaults w.r.t Purpose of loan
plt.figure(figsize=(15, 6))
sns.barplot(x=df["purpose"], y=df["loan_status"])
plt.title("\nLoan defaulters w.r.t Purpose\n", fontsize=15)
plt.xticks(rotation=60)

plt.show()

# %% [markdown]
# 1. Loans are taken for majority for debt consolidation, Other,Home improvement , major purchase & small buisiness purpose.
# 2. From the bar plot, we can observe that the probability of persong being loan defaulter is more in small buisiness,
# Defaulter rate is more when person take loan for small business purpose.
# 3. Defaulter Rate will depend on the Purpose of the loan

# %% [markdown]
# ## Term

# %%
# Term vs loan defaulters
fig, ax = plt.subplots(1, 2, figsize=(10, 6))

# Countplot for Term
sns.countplot(df["term_months"], ax=ax[0])
# Loan defaults vs term
sns.barplot(x=df["term_months"], y=df["loan_status"], ax=ax[1])
ax[0].set_title("\nTERM (in Months)\n", fontsize=15)
ax[1].set_title("\nLoan defaults % w.r.t TERM (in Months)\n", fontsize=15)
fig.tight_layout()


# %% [markdown]
# 1. In the givan dataset, we are having more number of people with term 36 months than 60 months.
# 2. But The probability of loan getting defaulted is more for 60 months than 30 months.

# %% [markdown]
# ## Grade

# %%
sns.countplot(data=df, x="grade", hue="loan_status")

# %% [markdown]
# 1. There are more number of people with grade B.
# 2. Defaulter rate is high with the grade G and less for grade A.

# %% [markdown]
# ## Sub-Grade

# %%
# check for defaulters wrt subgrade in the data using countplot

# Countplot for sub grade
fig, ax = plt.subplots(2, 1, figsize=(15, 12))
sns.countplot(x=df["sub_grade"], ax=ax[0], order=df["sub_grade"].value_counts().index)
# Loan defaulter vs sub grade
sns.barplot(
    x=df["sub_grade"],
    y=df["loan_status"],
    ax=ax[1],
    order=df["sub_grade"].value_counts().index,
)
ax[0].set_title("\n SUB GRADE\n", fontsize=20)
ax[1].set_title("\nLoan defaults % w.r.t SUB GRADE\n", fontsize=20)
plt.tight_layout()
plt.show()

# %% [markdown]
# 1. There are more number of people with sub grade A4.
# 2. Defaulter rate is increasing with the sub grade , loan defaulter rate is more for F5 grade  and less for grade A1.
# 3. Sub Grade is useful for further analysis.

# %% [markdown]
# ## Home ownership

# %%
sns.countplot(data=df, x="home_ownership", hue="loan_status")

# %% [markdown]
# 1. Loan defaulter rate is almost constant for all the home ownerships, slightly more for OTHER home ownership.
# 2. We can say that loan defaulters does not depends on home ownership.
# 3. Home ownership is not useful for further analysis.

# %%
# we will remove home ownership NONE
# Since Only one record is present for None category
df = df[df["home_ownership"] != "NONE"]

# Again check for value counts
# df['home_ownership'].value_counts()

# %% [markdown]
# ## Verification Status

# %%
sns.countplot(data=df, x="verification_status", hue="loan_status")

# %% [markdown]
# 1. In the given data ,There are more records for which the ststus is non verified.
# 2. but the defaulter rate is more for verified status.

# %% [markdown]
# # Numerical variables

# %%
df.select_dtypes(include=np.number).columns

# %% [markdown]
# ## Interest rate

# %%
sns.boxplot(data=df, y="int_rate")

# Display the plot
plt.show()

# %%
# Define the bin ranges
bins = [0, 5, 10, 15, 20, 25, 30]

# Create a new column 'interest_rate_group' with the grouped values
df["int_rate_cat"] = pd.cut(
    df["int_rate"],
    bins=bins,
    labels=["0-5", "5-10", "10-15", "15-20", "20-25", "25-30"],
)

# Create the countplot
sns.countplot(data=df, x="int_rate_cat")

# Set labels and title
plt.xlabel("Interest Rate Group")
plt.ylabel("Count")
plt.title("Count of Loans by Interest Rate Group")

# Display the plot
plt.show()


# %%
# Divide interest rate into groups based on intervals
df["int_rate_cat"] = pd.cut(
    df["int_rate"],
    [0, 5, 10, 15, 20, 25, 30],
    labels=["0-5", "5-10", "10-15", "15-20", "20-25", "25-30"],
)

# %% [markdown]
# 1. There are more records with intrest rate between 10-15%
# 2. The rate of loan defaulter is more for highest intrest rate & less for lowest intrest rate.

# %% [markdown]
# ## Annual income

# %%
# Boxplot for annual income
plt.figure(figsize=(10, 6))
df["annual_inc"].plot(kind="box")

plt.text(1.1, df["annual_inc"].max(), s=df["annual_inc"].max())
plt.text(1.1, df["annual_inc"].min(), s=df["annual_inc"].min())
plt.text(1.1, df["annual_inc"].quantile(0.25), s=df["annual_inc"].quantile(0.25))
plt.text(1.1, df["annual_inc"].quantile(0.50), s=df["annual_inc"].quantile(0.50))
plt.text(1.1, df["annual_inc"].quantile(0.75), s=df["annual_inc"].quantile(0.75))

plt.ylabel("Annual Income", fontsize=15)
plt.show()
plt.show()

# %% [markdown]
# 1. The median income is 58000 ,the minum income is 4000 & the maximum income is 234996.


# %%
# Divide annual income into groups based on intervals
def annual_income(inc):
    if inc <= 50000:
        return "low"
    elif inc > 50000 and inc <= 100000:
        return "medium"
    elif inc > 100000 and inc <= 150000:
        return "high"
    else:
        return "very high"


df["annual_inc_cat"] = df["annual_inc"].apply(lambda x: annual_income(x))
df["annual_inc_cat"].value_counts()

# %% [markdown]
# 1. Defaulter rate is increasing with the annual income value, defaulter rate will depend on loan amount
# 2. The annual income variable is useful for further analysis.

# %% [markdown]
# ## Loan amount

# %%
# Boxplot for loan amount
plt.figure(figsize=(10, 6))
df["loan_amnt"].plot(kind="box")

plt.text(1.1, df["loan_amnt"].max(), s=df["loan_amnt"].max())
plt.text(1.1, df["loan_amnt"].min(), s=df["loan_amnt"].min())
plt.text(1.1, df["loan_amnt"].quantile(0.25), s=df["loan_amnt"].quantile(0.25))
plt.text(1.1, df["loan_amnt"].quantile(0.50), s=df["loan_amnt"].quantile(0.50))
plt.text(1.1, df["loan_amnt"].quantile(0.75), s=df["loan_amnt"].quantile(0.75))

plt.ylabel("Loan Amount", fontsize=15)
plt.show()
plt.show()

# %% [markdown]
# The median loan amount is 9600 , the minimum loan amount is 500, the maximum loan amount is 35000


# %%
# Divide Loan amount into groups based on intervals
def loan_amount(amt):
    if amt <= 5500:
        return "low"
    elif amt > 5500 and amt <= 10000:
        return "medium"
    elif amt > 10000 and amt <= 15000:
        return "high"
    else:
        return "very high"


df["loan_amnt_cat"] = df["loan_amnt"].apply(lambda x: loan_amount(x))
df["loan_amnt_cat"].value_counts()

# %%
sns.barplot(x=df["loan_amnt_cat"], y=df["loan_status"])

# %% [markdown]
# 1. loan defaulter rate is increasing as loan amount range .
# 2. This feature is useful for further analysis

# %% [markdown]
# ## Debt to Income ratio

# %%
df["dti"].describe()

# %%
# Divide interest rate into groups based on intervals
df["dti_cat"] = pd.cut(
    df["dti"],
    [0, 5, 10, 15, 20, 25, 30],
    labels=["0-5", "5-10", "10-15", "15-20", "20-25", "25-30"],
)
# df.head()

# %%
sns.barplot(x=df["dti_cat"], y=df["loan_status"])

# %% [markdown]
# 1. Loan defaulter rate is increasing with the debt to income ratio.
# 2. Dti is useful for finding the loan defaulter.

# %% [markdown]
# ## Revolving line utilization rate

# %%
# Boxplot for revol_util
plt.figure(figsize=(10, 6))
df["revol_util"].plot(kind="box")

plt.text(1.1, df["revol_util"].max(), s=df["revol_util"].max())
plt.text(1.1, df["revol_util"].min(), s=df["revol_util"].min())
plt.text(1.1, df["revol_util"].quantile(0.25), s=df["revol_util"].quantile(0.25))
plt.text(1.1, df["revol_util"].quantile(0.50), s=df["revol_util"].quantile(0.50))
plt.text(1.1, df["revol_util"].quantile(0.75), s=df["revol_util"].quantile(0.75))

plt.ylabel("revolving line utilization rate", fontsize=15)
plt.show()
plt.show()

# %%
# Divide revol utilization rate into groups based on intervals
df["revol_util_cat"] = pd.cut(
    df["revol_util"], [0, 25, 50, 75, 100], labels=["0-25", "25-50", "50-75", "75-100"]
)

# %%
sns.barplot(x=df["revol_util_cat"], y=df["loan_status"])

# %% [markdown]
# 1. Loan defaulter rate is increasing with the revolving line utilization rate.
# 2. this is useful for finding the loan defaulter.

# %% [markdown]
# ## Installments

# %%
df["installment"].describe()


# %%
# installment
def installment(n):
    if n <= 200:
        return "low"
    elif n > 200 and n <= 400:
        return "medium"
    elif n > 400 and n <= 600:
        return "high"
    else:
        return "very high"


df["installment_cat"] = df["installment"].apply(lambda x: installment(x))

# %%
sns.barplot(x=df["installment_cat"], y=df["loan_status"])

# %% [markdown]
# 1. Loan defaulter rate is increasing with the installment values.
# 2. Dti is useful for finding the loan defaulter.

# %% [markdown]
# ### Installments Vs Loan amount

# %%
plt.figure(figsize=(10, 8))
sns.scatterplot(data=df, x="loan_amnt", y="installment")
plt.title("Installments Vs Loan amount", fontsize=20)
plt.show()

# %% [markdown]
# 1. It is obvious that if the loan amount is more, installment amount will also be more

# %% [markdown]
# ### Annual income VS LOAN AMOUNT

# %%
plt.figure(figsize=(10, 8))
sns.scatterplot(data=df, x="annual_inc", y="loan_amnt")
plt.title("Annual_inc Vs Loan amount", fontsize=20)
plt.show()

# %% [markdown]
# 1. People with annual income between 0 to 100000 tend to appply more for loan

# %% [markdown]
# # MULTIVARIATE ANALYSIS

# %%
# Correlation matrix
plt.figure(figsize=(15, 8))
sns.heatmap(df.corr(), annot=True)
plt.show()

# %% [markdown]
# 1. There is a strong correlation between loan amount and funded amount.
# 2. There is a strong correlation between loan amount and installment.
# 3. The columns total_acc, open_acc are having high correlation
# 4. There are few cells having negative correlation

# %% [markdown]
# # Pairplot
#
#
#

# %%
# sns.pairplot(df_num)

# %% [markdown]
# ### Loan amount & Interest rate

# %%
plt.figure(figsize=(10, 8))
sns.scatterplot(x=df["loan_amnt"], y=df["int_rate"], hue=df["loan_status"])
plt.title("Interest rate  Vs Loan amount", fontsize=20)
plt.show()

# %% [markdown]
# The defaulters are present at all the places

# %% [markdown]
# ## Loan defaulters w. r. t. Term & Purpose

# %%
plt.figure(figsize=(15, 8))
sns.barplot(x=df["term_months"], y=df["loan_status"], hue=df["purpose"])
plt.show()

# %% [markdown]
# 1. From the above plot, we can infer out that default rate is increases for every purpose w.r.t term.

# %% [markdown]
# ## Loan defaulters w. r. t. Grade & Purpose

# %%
plt.figure(figsize=(15, 8))
sns.barplot(x=df["grade"], y=df["loan_status"], hue=df["purpose"])
plt.show()

# %% [markdown]
# 1. From the above plot, we can infer out that default rate is increases for every purpose w.r.t Grade.
# 2. The more number of defaulters are present in the Grade G and less in Grade A

# %% [markdown]
# ## Loan defaulters w. r. t. Term & Loan amount

# %%
plt.figure(figsize=(15, 8))
sns.barplot(x=df["loan_amnt_cat"], y=df["loan_status"], hue=df["term_months"])
plt.show()

# %% [markdown]
# 1. From the above plot, we can infer out that default rate is increases for loan amount category w.r.t term.

# %%
sns.barplot(x=df["issue_date_month"], y=df["loan_amnt"], hue=df["loan_status"])

# %% [markdown]
# In every month, there are almost equal number of loan defaulters as loan takers

# %%
sns.barplot(x=df["earliest_cr_line_month"], y=df["loan_amnt"])

# %% [markdown]
# The amount issued by the bank is same for all the months

# %% [markdown]
# ## Save the Dataset till EDA

# %%
df_after_EDA = df.copy()

# %% [markdown]
# # Important features selected from EDA

# %% [markdown]
# The features which are depends on whether the person will be able to repay the loan amount or not are term, grade,sub grade,purpose,revol_util, int_rate, installment, annual income, loan amount.

# %%
df_after_EDA.head()

# %% [markdown]
# # Hereafter we will continue with the dataset which we got after data cleaning

# %%
# Hereafter we will continue with the dataset which we got after data cleaning
df1 = df_after_data_cleaning.copy()
df1.head()

# %%
df1.shape

# %%
df1.columns

# %%
# Dropping the NONE category from the home ownership column as it contains only one record
df1 = df1[df1["home_ownership"] != "NONE"]
df1 = df1[df1["loan_status"].isin(["Fully Paid", "Charged Off"])]
df1.shape

# %% [markdown]
# # Hypothesis testing

# %%
import scipy.stats as st

# %% [markdown]
# Hypothesis: 1
# H0: The interest rate is same for different purpose of loans
# H1: The interest rate is not same for different purpose of loans

# %%
cc = df1[df1["purpose"] == "credit_card"]["int_rate"]
car = df1[df1["purpose"] == "car"]["int_rate"]
sm_bus = df1[df1["purpose"] == "small_business"]["int_rate"]
wedding = other = df1[df1["purpose"] == "wedding"]["int_rate"]
debt_cons = df1[df1["purpose"] == "debt_consolidation"]["int_rate"]
home_imp = df1[df1["purpose"] == "home_improvement"]["int_rate"]
maj_pur = df1[df1["purpose"] == "major_purchase"]["int_rate"]
med = df1[df1["purpose"] == "medical"]["int_rate"]
move = df1[df1["purpose"] == "moving"]["int_rate"]
vac = df1[df1["purpose"] == "vacation"]["int_rate"]
ren_energy = df1[df1["purpose"] == "renewable_energy"]["int_rate"]
house = df1[df1["purpose"] == "house"]["int_rate"]
edu = df1[df1["purpose"] == "educational"]["int_rate"]

# %%
plt.figure(figsize=(15, 6))
sns.boxplot(x=df1["purpose"], y=df1["int_rate"])

# %%
cols = [
    cc,
    car,
    sm_bus,
    wedding,
    debt_cons,
    home_imp,
    maj_pur,
    med,
    move,
    vac,
    ren_energy,
    house,
    edu,
]
for i in cols:
    print(st.shapiro(i)[1])

# %%
st.levene(
    cc,
    car,
    sm_bus,
    wedding,
    debt_cons,
    home_imp,
    maj_pur,
    med,
    move,
    vac,
    ren_energy,
    house,
    edu,
)

# %%
st.f_oneway(
    cc,
    car,
    sm_bus,
    wedding,
    debt_cons,
    home_imp,
    maj_pur,
    med,
    move,
    vac,
    ren_energy,
    house,
    edu,
)

# %% [markdown]
# From Shapiro test, all the variables have pvalue < 0.05. So null hypothesis is rejected means that no variable is following normal distribution
# From levene test, the pvalue < 0.05. So null hypothesis is rejected means that variance is different
# From the oneway anova test the pvalue is less than 0.05. So we are rejecting the null hypothesis(H0). So it is clear that the interest rate is different for different purpose

# %% [markdown]
# Hypothesis : 2
# H0: Loan amount given for different grade is same
# H1: Loan amount given for different grade is not same

# %%
A = df1[df1["grade"] == "A"]["loan_amnt"]
B = df1[df1["grade"] == "B"]["loan_amnt"]
C = df1[df1["grade"] == "C"]["loan_amnt"]
D = df1[df1["grade"] == "D"]["loan_amnt"]
E = df1[df1["grade"] == "E"]["loan_amnt"]
F = df1[df1["grade"] == "F"]["loan_amnt"]
G = df1[df1["grade"] == "G"]["loan_amnt"]

# %%
cols = [A, B, C, D, E, F, G]
for i in cols:
    print(st.shapiro(i)[1])

# %%
sns.countplot(x=df1["grade"])

# %%
st.levene(A, B, C, D, E, F, G)

# %%
st.f_oneway(A, B, C, D, E, F, G)

# %% [markdown]
# From Shapiro test, all the variables have pvalue < 0.05. So null hypothesis is rejected means that no variable is following normal distribution
# From levene test, the pvalue < 0.05. So null hypothesis is rejected means that variance is different
# From the oneway anova test the pvalue is less than 0.05. So we are rejecting the null hypothesis(H0).It is clear that the loan amount for different grade is not same

# %% [markdown]
# Hypothesis : 3
# H0: Loan status is having association with the grade
# H1: Loan status is not having association with the grade

# %%
table = pd.crosstab(df1["loan_status"], df1["grade"])
st.chi2_contingency(table)

# %% [markdown]
# From the chi2 test the pvalue is less than 0.05. So we are rejecting the null hypothesis(H0). It is clear that the Loan status is not having association with the grade

# %%
df1 = df1.reset_index(drop=True)

# %%
df_num = df1.select_dtypes(include=np.number)
df_num.shape

# %%
df_num.info()

# %%
df_cat = df1.select_dtypes(include=object)
print(df_cat.shape)
df_cat.columns

# %%
# Removing subgrade column as it will be equivalent to the Grade column
df_cat.drop(columns="sub_grade", inplace=True)
df_cat.shape

# %%
# Performing encoding for the columns
df_dummies = pd.get_dummies(
    df_cat[
        [
            "home_ownership",
            "grade",
            "verification_status",
            "term_months",
            "initial_list_status",
        ]
    ],
    drop_first=True,
)
df_dummies.shape

# %%
# Performing label encoding for Addr_state
state = df_cat["addr_state"].unique()
add_dict = {}
j = 1
for i in state:
    add_dict[i] = j
    j = j + 1
df_cat["addr_state"] = df_cat["addr_state"].map(add_dict)


# %%
# Performing label encoding for purpose
purpose = df_cat["purpose"].unique()
purpose_dict = {}
j = 1
for i in purpose:
    purpose_dict[i] = j
    j = j + 1
df_cat["purpose"] = df_cat["purpose"].map(purpose_dict)

# %%
# Dropping columns home_ownership,verification_status,term_months,grade
df_cat.drop(
    columns=[
        "home_ownership",
        "grade",
        "verification_status",
        "term_months",
        "loan_status",
    ],
    inplace=True,
)

# concatenating the df_dummies, df_cat
df_cat = pd.concat([df_cat, df_dummies], axis=1)
df_cat.shape

# %%
df_cat.head()

# %% [markdown]
# # Feature selection

# %%
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from mlxtend.feature_selection import SequentialFeatureSelector
from sklearn.linear_model import LogisticRegression

# %%
plt.figure(figsize=(15, 8))
sns.heatmap(df_num.corr(), annot=True)

# %%
# The features of loan_amnt, funded_amnt_inv, installment have high correlation. So dropping two columns among them
plt.figure(figsize=(15, 8))
sns.heatmap(df_num.drop(columns=["loan_amnt", "installment"]).corr(), annot=True)

# %% [markdown]
# using feature selection technique from sklearn to check importance of features for numerical columns

# %%
# Extacting y variable and encoding it. Checking the feature importances of numerical variables
# Goal is to find loan defaulters so changed off=1 , fully paid=0
y = df1["loan_status"]
y = y.replace({"Charged Off": 1, "Fully Paid": 0})

# %%
df_num.fillna(0, inplace=True)

# %%
df_num.isna().sum()

# %%
feature_importances_ = mutual_info_regression(df_num, y)

# %%
features_importances = pd.Series(
    feature_importances_, df_num.columns[0 : len(df_num.columns)]
)
features_importances.plot(kind="barh")
plt.show()

# %% [markdown]
# From above graph we see that installment has high importance than funded_amnt_inv, loan_amnt. So keeping installment and removing other two columns in order to reduce multicollinearity

# %%
plt.figure(figsize=(12, 7))
sns.heatmap(df_num.drop(columns=["funded_amnt_inv", "loan_amnt"]).corr(), annot=True)

# %%
df_cat.drop(columns=["initial_list_status"], inplace=True)

# %%
# Calculating the feature importance for categorical columns
feature_importances_cat = mutual_info_classif(df_cat, y)
features_importances_cat = pd.Series(
    feature_importances_cat, df_cat.columns[0 : len(df_cat.columns)]
)
features_importances_cat.plot(kind="barh")
plt.show()

# %%
# Concating the df_num,df_cat to a single dataframe
df2 = pd.concat([df_num, df_cat], axis=1)
print(df2.shape)
df2.head()

# %%
# #Using Sequential Feature selection technique and applying forward substitution
# lr=LogisticRegression()
# sfs_forward=SequentialFeatureSelector(lr,k_features=25)
# sfs_forward.fit(df2,y)
# sfs_forward.k_feature_names_

# %%
# #Using Sequential Feature selection technique and applying backward elimination
# sfs_backward=SequentialFeatureSelector(lr,k_features=25,forward=False)
# sfs_backward.fit(df2,y)
# sfs_backward.k_feature_names_

# %%
# The final set of features obtained are stored in features variable. The final set is obtained from the combination of columns
# that are common in sfs_backward,sfs_forward,mutual_info algorithm
features = [
    "loan_amnt",
    "funded_amnt_inv",
    "dti",
    "inq_last_6mths",
    "pub_rec",
    "int_rate",
    "revol_util",
    "purpose",
    "home_ownership_OTHER",
    "home_ownership_OWN",
    "home_ownership_RENT",
    "grade_C",
    "grade_D",
    "grade_E",
    "verification_status_Verified",
    "term_months_ 60 ",
    "grade_B",
    "grade_G",
    "earliest_cr_line_month",
    "earliest_cr_line_year",
    "open_acc",
    "addr_state",
    "grade_F",
    "issue_date_year",
    "issue_date_month",
]
print("The number of features are:", len(features))

# %% [markdown]
# # Scaling the features

# %%
from sklearn.preprocessing import StandardScaler

sc = StandardScaler()
x = df2[features]
x_num = x.loc[
    :,
    [
        "loan_amnt",
        "funded_amnt_inv",
        "dti",
        "int_rate",
        "revol_util",
    ],
]
x_num = pd.DataFrame(sc.fit_transform(x_num), columns=x_num.columns)
x_num.head()

# %%
# The final transformed independent variables
x_sc = pd.concat([x_num, x.drop(columns=x_num.columns)], axis=1)
print(x_sc.shape)
x_sc.head()

# %% [markdown]
# # Balancing the dataset

# %% [markdown]
# The project on loan default model is very much analagous to the defect or disease capturing models where there will be always more data on OK and only fewer example data on NOT OK or default issues. Such data is the natural data on a practical real life situation and hence does not need tp be balanced.

# %% [markdown]
# ## Train test split

# %%
from sklearn.model_selection import train_test_split

xtrain, xtest, ytrain, ytest = train_test_split(x_sc, y, test_size=0.3, random_state=10)

# %% [markdown]
# # Building the models

# %%
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score, GridSearchCV, RepeatedKFold
from sklearn.metrics import (
    accuracy_score,
    auc,
    roc_auc_score,
    roc_curve,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.metrics import precision_score, recall_score
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
import warnings

warnings.filterwarnings("ignore")

# %% [markdown]
# # Decision Tree BASE MODEL

# %%
# cross validation for random forest model to find out bias & variance error
dt = DecisionTreeClassifier(random_state=10)
score = cross_val_score(dt, xtrain, ytrain, scoring="accuracy")
bias = np.mean(1 - score)
var = np.std(score)
print("Bias error     :", bias)
print("variance error :", var)

# %%
# building the model
dt = DecisionTreeClassifier(random_state=10)
dt.fit(xtrain, ytrain)
ypred_dt = dt.predict(xtest)
print("Training accuracy:", dt.score(xtrain, ytrain))
print("Testing accuracy :", dt.score(xtest, ytest))

# %%
ypred_full = dt.predict_proba(xtest)[:, 1]
print("AUC-ROC Score : ", roc_auc_score(ytest, ypred_full))
fpr, tpr, thresholds = roc_curve(ytest, ypred_full)
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.grid(True)
plt.show()

# %%
# Confusion matrix
cm = pd.DataFrame(
    data=confusion_matrix(ytest, ypred_dt),
    columns=["ypred_0", "ypred_1"],
    index=["yactual_0", "yactual_1"],
)
sns.heatmap(cm, annot=True)
plt.show()

# %%
# classification report for decison tree base model
# list to save results of precision,recall,f1-score & accuracy
report_list = []
print("Confusion matrix:")
print(confusion_matrix(ytest, ypred_dt))
print("Classification Report :")
cr1 = classification_report(ytest, ypred_dt, output_dict=True)
report_list.append(
    [
        "Decision Tree Base",
        cr1["0"]["precision"],
        cr1["0"]["recall"],
        cr1["0"]["f1-score"],
        cr1["1"]["precision"],
        cr1["1"]["recall"],
        cr1["1"]["f1-score"],
        cr1["accuracy"],
    ]
)
print(classification_report(ytest, ypred_dt))

# %% [markdown]
# ## Decision Tree Hypertunned model

# %%
# tunned model to find best parameters
DT1 = DecisionTreeClassifier()
param = {"max_depth": np.arange(3, 100), "criterion": ["gini", "entropy"]}

gs = GridSearchCV(DT1, param_grid=param, scoring="roc_auc", n_jobs=-1)
gs.fit(xtrain, ytrain)
gs.best_params_

# %%
# tunned model to find best parameters
DT2 = DecisionTreeClassifier()
param = {"max_depth": np.arange(3, 100), "criterion": ["gini", "entropy"]}

gs = GridSearchCV(DT2, param_grid=param, scoring="f1_weighted", n_jobs=-1)
gs.fit(xtrain, ytrain)
gs.best_params_

# %%
# cross validation for random forest model to find out bias & variance error

DT1 = DecisionTreeClassifier(max_depth=4, criterion="entropy", random_state=10)
score1 = cross_val_score(DT1, xtrain, ytrain, scoring="roc_auc")

biasdt1 = np.mean(1 - score1)
vardt1 = np.std(score1)

print("Bias error     :", biasdt1)
print("variance error :", vardt1)

# %%
DT2 = DecisionTreeClassifier(max_depth=7, criterion="gini", random_state=10)
score2 = cross_val_score(DT2, xtrain, ytrain, scoring="f1_weighted")

biasdt2 = np.mean(1 - score2)
vardt2 = np.std(score2)

print("Bias error     :", biasdt2)
print("variance error :", vardt2)

# %%
DT1 = DecisionTreeClassifier(max_depth=4, criterion="entropy", random_state=10)
DT1.fit(xtrain, ytrain)
# ypred_DT1=DT1.predict(xtest)
print("Training accuracy:", DT1.score(xtrain, ytrain))
print("Testing accuracy :", DT1.score(xtest, ytest))


# %%
DT2 = DecisionTreeClassifier(max_depth=7, criterion="gini", random_state=10)
DT2.fit(xtrain, ytrain)
# ypred_DT1=DT1.predict(xtest)
print("Training accuracy:", DT2.score(xtrain, ytrain))
print("Testing accuracy :", DT2.score(xtest, ytest))

# %%
ypred_tunned = DT1.predict_proba(xtest)[:, 1]
print("AUC-ROC Score : ", roc_auc_score(ytest, ypred_tunned))

fpr, tpr, thresholds = roc_curve(ytest, ypred_tunned)

plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)

plt.grid(True)

plt.show()

# %%
ypred_tunned = DT2.predict_proba(xtest)[:, 1]
print("AUC-ROC Score : ", roc_auc_score(ytest, ypred_tunned))

fpr, tpr, thresholds = roc_curve(ytest, ypred_tunned)

plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)

plt.grid(True)

plt.show()

# %%
ypred_DT1 = DT1.predict(xtest)

cm = pd.DataFrame(
    data=confusion_matrix(ytest, ypred_DT1),
    columns=["ypred_0", "ypred_1"],
    index=["yactual_0", "yactual_1"],
)
sns.heatmap(cm, annot=True)
plt.show()

# %%
ypred_DT2 = DT2.predict(xtest)

cm = pd.DataFrame(
    data=confusion_matrix(ytest, ypred_DT2),
    columns=["ypred_0", "ypred_1"],
    index=["yactual_0", "yactual_1"],
)
sns.heatmap(cm, annot=True)
plt.show()

# %%
# ROC-AUC SCORE TUNNED
ypred_DT1 = DT1.predict(xtest)
print("Classification Report :")
cr2 = classification_report(ytest, ypred_DT1, output_dict=True)
report_list.append(
    [
        "Decision Tree Tunned using ROC-AUC",
        cr2["0"]["precision"],
        cr2["0"]["recall"],
        cr2["0"]["f1-score"],
        cr2["1"]["precision"],
        cr2["1"]["recall"],
        cr2["1"]["f1-score"],
        cr2["accuracy"],
    ]
)
print(classification_report(ytest, ypred_DT1))

# %%
# F1-SCORE TUNNED
ypred_DT2 = DT2.predict(xtest)
print("Classification Report :")
cr3 = classification_report(ytest, ypred_DT2, output_dict=True)
report_list.append(
    [
        "Decision Tree Tunned using F1-Weighted",
        cr3["0"]["precision"],
        cr3["0"]["recall"],
        cr3["0"]["f1-score"],
        cr3["1"]["precision"],
        cr3["1"]["recall"],
        cr3["1"]["f1-score"],
        cr3["accuracy"],
    ]
)
print(classification_report(ytest, ypred_DT2))

# %% [markdown]
# # XGBoosting

# %%
tunned_param = [{"n_estimators": np.arange(3, 100)}]
xgb_model = XGBClassifier(random_state=10)
xgb_grid = GridSearchCV(estimator=xgb_model, param_grid=tunned_param, cv=5, n_jobs=-1)

xgb_grid.fit(xtrain, ytrain)
xgb_grid.best_params_

# %%
# max depth=4 taken from the above decision tree model
xgb1 = XGBClassifier(n_estimators=6, random_state=10)
xgbscore1 = cross_val_score(xgb1, xtrain, ytrain, scoring="roc_auc")

biasxgb2 = np.mean(1 - xgbscore1)
varxgb2 = np.std(xgbscore1)

print("Bias error     :", biasxgb2)
print("variance error :", varxgb2)

# %%
xgb1 = XGBClassifier(n_estimators=6, max_depth=4, random_state=10)
xgb1.fit(xtrain, ytrain)
print("Training accuracy:", xgb1.score(xtrain, ytrain))
print("Testing accuracy :", xgb1.score(xtest, ytest))

# %%
# ROC-AUC SCORE TUNNED
ypredxgb1 = xgb1.predict(xtest)
print("Classification Report :")
cr4 = classification_report(ytest, ypredxgb1, output_dict=True)
report_list.append(
    [
        "Extreme Gradient Boosting",
        cr4["0"]["precision"],
        cr4["0"]["recall"],
        cr4["0"]["f1-score"],
        cr4["1"]["precision"],
        cr4["1"]["recall"],
        cr4["1"]["f1-score"],
        cr4["accuracy"],
    ]
)
print(classification_report(ytest, ypredxgb1))

# %%
ypred_xgb1 = xgb1.predict_proba(xtest)[:, 1]
print("AUC-ROC Score : ", roc_auc_score(ytest, ypred_xgb1))

fpr, tpr, thresholds = roc_curve(ytest, ypred_xgb1)

plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)

plt.grid(True)

plt.show()

# %%
ypred_xg1 = xgb1.predict(xtest)

cm = pd.DataFrame(
    data=confusion_matrix(ytest, ypred_xg1),
    columns=["ypred_0", "ypred_1"],
    index=["yactual_0", "yactual_1"],
)
sns.heatmap(cm, annot=True)
plt.show()

# %% [markdown]
# ## Random Forest BASE MODEL

# %%
# cross validation for random forest model to find out bias & variance error
rf = RandomForestClassifier(random_state=10)
score = cross_val_score(rf, xtrain, ytrain, scoring="f1_weighted")
bias = np.mean(1 - score)
var = np.std(score)
print("Bias error     :", bias)
print("variance error :", var)

# %%
rf = RandomForestClassifier(random_state=10)
rf.fit(xtrain, ytrain)
ypred_rf = rf.predict(xtest)
print("Training accuracy:", rf.score(xtrain, ytrain))
print("Testing accuracy :", rf.score(xtest, ytest))

# %%
ypred_rffull = rf.predict_proba(xtest)[:, 1]
print("AUC-ROC Score : ", roc_auc_score(ytest, ypred_rffull))
fpr, tpr, thresholds = roc_curve(ytest, ypred_rffull)
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.grid(True)
plt.show()

# %%
ypred = rf.predict(xtest)
cm = pd.DataFrame(
    data=confusion_matrix(ytest, ypred),
    columns=["ypred_0", "ypred_1"],
    index=["yactual_0", "yactual_1"],
)
sns.heatmap(cm, annot=True)
plt.show()

# %%
ypred_rf = rf.predict(xtest)
print("Classification Report :")
print(classification_report(ytest, ypred_rf))

# %%
ypred_rf = rf.predict(xtest)
print("Classification Report :")
cr5 = classification_report(ytest, ypred_rf, output_dict=True)
report_list.append(
    [
        "Random Forest Base",
        cr5["0"]["precision"],
        cr5["0"]["recall"],
        cr5["0"]["f1-score"],
        cr5["1"]["precision"],
        cr5["1"]["recall"],
        cr5["1"]["f1-score"],
        cr5["accuracy"],
    ]
)
print(classification_report(ytest, ypred_rf))

# %% [markdown]
# ## Random Forest Hypertunned Model

# %%
# tunned model to find best parameters
rf_tunned = RandomForestClassifier()
param = {"n_estimators": np.arange(1, 100), "criterion": ["entropy", "gini"]}
gs = GridSearchCV(rf_tunned, param_grid=param, scoring="f1_weighted", n_jobs=-1)
gs.fit(xtrain, ytrain)
gs.best_params_

# %%
# cross validation for random model to find out bias & variance error
RF_tunned = RandomForestClassifier(
    n_estimators=11, criterion="entropy", random_state=10
)
score = cross_val_score(RF_tunned, xtrain, ytrain, scoring="f1_weighted")
bias = np.mean(1 - score)
var = np.std(score)
print("Bias error     :", bias)
print("variance error :", var)

# %%
# random forest model
RF_tunned = RandomForestClassifier(
    n_estimators=50, criterion="entropy", random_state=10
)
RF_tunned.fit(xtrain, ytrain)
ypredrf1 = RF_tunned.predict(xtrain)
ypredrf2 = RF_tunned.predict(xtest)
print(
    "\nOverall accuaracy of the Decision tree training data :",
    accuracy_score(ytrain, ypredrf1),
)
print(
    "Overall accuaracy of the Decision tree testing data  :",
    accuracy_score(ytest, ypredrf2),
)
from sklearn.metrics import cohen_kappa_score

print("\nCohen kappa score:", cohen_kappa_score(ytest, ypredrf2))

# %%
ypred_RF = RF_tunned.predict(xtest)
print("Classification Report :")
cr6 = classification_report(ytest, ypred_RF, output_dict=True)
report_list.append(
    [
        "Random Forest Tunned",
        cr6["0"]["precision"],
        cr6["0"]["recall"],
        cr6["0"]["f1-score"],
        cr6["1"]["precision"],
        cr6["1"]["recall"],
        cr6["1"]["f1-score"],
        cr6["accuracy"],
    ]
)
print(classification_report(ytest, ypred_RF))

# %%
ypred_rft = RF_tunned.predict_proba(xtest)[:, 1]
print("AUC-ROC Score : ", roc_auc_score(ytest, ypred_rft))
fpr, tpr, thresholds = roc_curve(ytest, ypred_rft)
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.grid(True)
plt.show()

# %%
cm = pd.DataFrame(
    data=confusion_matrix(ytest, ypred_RF),
    columns=["ypred_0", "ypred_1"],
    index=["yactual_0", "yactual_1"],
)
sns.heatmap(cm, annot=True)
plt.show()

# %% [markdown]
# ### Dataframe of results

# %%
report1 = pd.DataFrame(
    data=report_list,
    columns=[
        "MODEL",
        "Precision_0",
        "Recall_0",
        "f1-score_0",
        "Precision_1",
        "Recall_1",
        "f1-score_1",
        "Overall_accuracy",
    ],
)
report1

# %% [markdown]
# # Logistic Regression

# %%
logreg = LogisticRegression()
logreg.fit(xtrain, ytrain)
ypred_logreg = logreg.predict(xtest)
accuracy_logreg = accuracy_score(ytest, ypred_logreg)
f1_logreg = f1_score(ytest, ypred_logreg)
precision_logreg = precision_score(ytest, ypred_logreg)
recall_logreg = recall_score(ytest, ypred_logreg)
auc_logreg = roc_auc_score(ytest, ypred_logreg)
conf_logreg = confusion_matrix(ytest, ypred_logreg)
print("Confusion matrix:\n", conf_logreg)
print("Auc:", auc_logreg)
print("Recall:", recall_logreg)
print("Precision:", precision_logreg)
print("f1_score:", f1_logreg)
print("Accuracy:", accuracy_logreg)


# %%
# Dictionary of classification report
cr7 = classification_report(ytest, ypred_logreg, output_dict=True)

# %%
y_pred_prob_logreg = logreg.predict_proba(xtest)
y_pred_prob_logreg1 = logreg.predict_proba(xtrain)
fpr, tpr, th = roc_curve(ytest, y_pred_prob_logreg[:, 1])
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.grid(True)
plt.show()

# %%
y_pred_df_logreg = pd.Series(y_pred_prob_logreg[:, 1])
y_pred_df_logreg


# %%
def cutoff_youdens_j(fpr, tpr, th):
    j_scores = tpr - fpr
    j_ordered = sorted(zip(j_scores, th))
    return j_ordered[-1][1]


cutoff = cutoff_youdens_j(fpr, tpr, th)
ser1 = []
for i in y_pred_prob_logreg1[:, 1]:
    if i > cutoff:
        ser1.append(1)
    else:
        ser1.append(0)
df_ser1 = pd.DataFrame(ser1)

# %%
logreg1 = LogisticRegression()
logreg1.fit(xtrain, df_ser1)
y_pred_logreg1 = logreg1.predict(xtest)
y_pred_prob_logreg_tuned = logreg1.predict_proba(xtest)
accuracy_logreg1 = accuracy_score(ytest, y_pred_logreg1)
conf_logreg1 = confusion_matrix(ytest, y_pred_logreg1)
f1_logreg1 = f1_score(ytest, y_pred_logreg1)
recall_logreg1 = recall_score(ytest, y_pred_logreg1)
precision_logreg1 = precision_score(ytest, y_pred_logreg1)
auc_logreg1 = roc_auc_score(ytest, y_pred_logreg1)
fpr, tpr, thresholds = roc_curve(ytest, y_pred_prob_logreg_tuned[:, 1])
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.show()
print("Confusion matrix:\n", conf_logreg1)
print("Auc:", auc_logreg1)
print("Recall:", recall_logreg1)
print("Precision:", precision_logreg1)
print("f1_score:", f1_logreg1)
print("Accuracy:", accuracy_logreg1)

# %%
# Dictionary of classification report
cr8 = classification_report(ytest, y_pred_logreg1, output_dict=True)

# %% [markdown]
# # Navie Bayes

# %%
nbmodel = GaussianNB()
nbmodel.fit(xtrain, ytrain)
ypred_nb = nbmodel.predict(xtest)
accuracy_nb = accuracy_score(ytest, ypred_nb)
f1_nb = f1_score(ytest, ypred_nb)
precision_nb = precision_score(ytest, ypred_nb)
recall_nb = recall_score(ytest, ypred_nb)
auc_nb = roc_auc_score(ytest, ypred_nb)
conf_nb = confusion_matrix(ytest, ypred_nb)
print("Confusion matrix\n", conf_nb)
print("AUC score:", auc_nb)
print("Recall:", recall_nb)
print("Precision:", precision_nb)
print("F1_score:", f1_nb)
print("Accuracy:", accuracy_nb)

# %%
# Dictionary of classification report
cr9 = classification_report(ytest, ypred_nb, output_dict=True)

# %%
cv_method = RepeatedKFold(n_splits=5, n_repeats=3, random_state=10)
params_NB = {"var_smoothing": np.logspace(0, -9, num=100)}
gs_NB = GridSearchCV(
    estimator=nbmodel,
    param_grid=params_NB,
    cv=cv_method,
    verbose=1,
    scoring="f1_weighted",
)
gs_NB.fit(xtrain, ytrain)
print("Best parameters:", gs_NB.best_params_)
print("Best score:", gs_NB.best_score_)

# %%
nbmodel1 = GaussianNB(var_smoothing=0.0012328467394420659)
nbmodel1.fit(xtrain, ytrain)
ypred_nb1 = nbmodel1.predict(xtest)
accuracy_nb1 = accuracy_score(ytest, ypred_nb1)
f1_nb1 = f1_score(ytest, ypred_nb1)
precision_nb1 = precision_score(ytest, ypred_nb1)
recall_nb1 = recall_score(ytest, ypred_nb1)
auc_nb1 = roc_auc_score(ytest, ypred_nb1)
conf_nb1 = confusion_matrix(ytest, ypred_nb1)
print("Confusion matrix\n", conf_nb1)
print("AUC score:", auc_nb1)
print("Recall:", recall_nb1)
print("Precision:", precision_nb1)
print("F1_score:", f1_nb1)
print("Accuracy:", accuracy_nb1)

# %%
# Dictionary of classification report
cr10 = classification_report(ytest, ypred_nb1, output_dict=True)

# %%
ypred_nb_tuned = nbmodel1.predict_proba(xtest)[:, 1]
fpr, tpr, thresholds = roc_curve(ytest, ypred_nb_tuned)
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.grid(True)
plt.show()

# %%
model = XGBClassifier(objective="binary:logistic")
model.fit(xtrain, ytrain)
ypred_xgboost = model.predict(xtest)
ypred_xgboost_prob = model.predict_proba(xtest)[:, 1]
accuracy_xgboost = accuracy_score(ytest, ypred_xgboost)
f1_xgboost = f1_score(ytest, ypred_xgboost)
precision_xgboost = precision_score(ytest, ypred_xgboost)
recall_xgboost = recall_score(ytest, ypred_xgboost)
auc_xgboost = roc_auc_score(ytest, ypred_xgboost)
conf_xgboost = confusion_matrix(ytest, ypred_xgboost)
print("Confusion matrix\n", conf_xgboost)
print("AUC:", auc_xgboost)
print("Recall:", recall_xgboost)
print("Precision:", precision_xgboost)
print("F1_score:", f1_xgboost)
print("Accuracy:", accuracy_xgboost)

# %%
# Dictionary of classification report
cr11 = classification_report(ytest, ypred_xgboost, output_dict=True)

# %%
fpr, tpr, thresholds = roc_curve(ytest, ypred_xgboost_prob)
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.grid(True)
plt.show()

# %%
param_grid = {
    "criterion": ["entropy", "gini"],
    "max_depth": range(2, 5),
    "n_estimators": [90, 100, 150, 200],
}
gs_xgboost = GridSearchCV(
    estimator=model, param_grid=param_grid, verbose=1, cv=5, scoring="f1_weighted"
)
gs_xgboost.fit(xtrain, ytrain)

# %%
print("Best Parameters", gs_xgboost.best_params_)

# %%
model1 = XGBClassifier(
    objective="binary:logistic", criterion="entropy", max_depth=4, n_estimators=90
)
model1.fit(xtrain, ytrain)
ypred_xgboost1 = model1.predict(xtest)
accuracy_xgboost1 = accuracy_score(ytest, ypred_xgboost1)
f1_xgboost1 = f1_score(ytest, ypred_xgboost1)
precision_xgboost1 = precision_score(ytest, ypred_xgboost1)
recall_xgboost1 = recall_score(ytest, ypred_xgboost1)
auc_xgboost1 = roc_auc_score(ytest, ypred_xgboost1)
conf_xgboost1 = confusion_matrix(ytest, ypred_xgboost1)
print("Confusion matrix\n", conf_xgboost1)
print("AUC:", auc_xgboost1)
print("Recall:", recall_xgboost1)
print("Precision:", precision_xgboost1)
print("F1_score:", f1_xgboost1)
print("Accuracy:", accuracy_xgboost1)

# %%
# Dictionary of classification report
cr12 = classification_report(ytest, ypred_xgboost1, output_dict=True)

# %%
ypred_xgboost1_prob = model1.predict_proba(xtest)[:, 1]
fpr, tpr, thresholds = roc_curve(ytest, ypred_xgboost1_prob)
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.grid(True)
plt.show()

# %%
data = {
    "Accuracy": [
        accuracy_logreg,
        accuracy_logreg1,
        accuracy_nb,
        accuracy_nb1,
        accuracy_xgboost,
        accuracy_xgboost1,
    ],
    "F1_Score": [f1_logreg, f1_logreg1, f1_nb, f1_nb1, f1_xgboost, f1_xgboost1],
    "Precision": [
        precision_logreg,
        precision_logreg1,
        precision_nb,
        precision_nb1,
        precision_xgboost,
        precision_xgboost1,
    ],
    "Recall": [
        recall_logreg,
        recall_logreg1,
        recall_nb,
        recall_nb1,
        recall_xgboost,
        recall_xgboost1,
    ],
    "AUC_Score": [auc_logreg, auc_logreg1, auc_nb, auc_nb1, auc_xgboost, auc_xgboost1],
}
Report_2 = pd.DataFrame(
    data,
    index=[
        "Logistic Regression",
        "Logistic Regression Tuned",
        "Naive Bayes",
        "Naive Bayes Tuned",
        "XGB Classifier",
        "XGB Classifier Tuned",
    ],
)
Report_2

# %% [markdown]
# # KNN

# %%
knn = KNeighborsClassifier()
knn.fit(xtrain, ytrain)
ypred_knn = knn.predict(xtest)
accuracy_knn = accuracy_score(ytest, ypred_knn)
f1_knn = f1_score(ytest, ypred_knn)
precision_knn = precision_score(ytest, ypred_knn)
recall_knn = recall_score(ytest, ypred_knn)
auc_knn = roc_auc_score(ytest, ypred_knn)
conf_knn = confusion_matrix(ytest, ypred_knn)
print("Confusion matrix\n", conf_knn)
print("AUC:", auc_knn)
print("Recall:", recall_knn)
print("Precision:", precision_knn)
print("F1_score:", f1_knn)
print("Accuracy:", accuracy_knn)

# %%
# Dictionary of classification report
cr13 = classification_report(ytest, ypred_knn, output_dict=True)

# %%
knn = KNeighborsClassifier()
param = {
    "n_neighbors": range(10, 100),
    "weights": ["uniform", "distance"],
    "algorithm": ["auto", "ball_tree", "kd_tree"],
}
gs = GridSearchCV(
    knn, param_grid=param, cv=5, verbose=1, scoring="f1_weighted", n_jobs=-1
)
gs.fit(xtrain, ytrain)
gs.best_params_

# %%
knn1 = KNeighborsClassifier(n_neighbors=10, weights="distance", algorithm="auto")
knn1.fit(xtrain, ytrain)
ypred_knn1 = knn1.predict(xtest)
accuracy_knn1 = accuracy_score(ytest, ypred_knn1)
f1_knn1 = f1_score(ytest, ypred_knn1)
precision_knn1 = precision_score(ytest, ypred_knn1)
recall_knn1 = recall_score(ytest, ypred_knn1)
auc_knn1 = roc_auc_score(ytest, ypred_knn1)
conf_knn1 = confusion_matrix(ytest, ypred_knn1)
print("Confusion matrix\n", conf_knn1)
print("AUC:", auc_knn1)
print("Recall:", recall_knn1)
print("Precision:", precision_knn1)
print("F1_score:", f1_knn1)
print("Accuracy:", accuracy_knn1)

# %%
# Dictionary of classification report
cr14 = classification_report(ytest, ypred_knn1, output_dict=True)

# %%
ypred_knn1_prob = knn1.predict_proba(xtest)[:, 1]
fpr, tpr, thresholds = roc_curve(ytest, ypred_knn1_prob)
plt.plot([0, 1], [0, 1], "r--")
plt.plot(fpr, tpr)
plt.grid(True)
plt.show()

# %% [markdown]
# # DATAFRAME OF  RESULT OF ALL THE MODELS

# %%
new_zero = pd.DataFrame(
    data=[
        cr1["0"],
        cr2["0"],
        cr3["0"],
        cr4["0"],
        cr5["0"],
        cr6["0"],
        cr7["0"],
        cr8["0"],
        cr9["0"],
        cr10["0"],
        cr11["0"],
        cr12["0"],
        cr13["0"],
        cr14["0"],
    ]
)
new_one = pd.DataFrame(
    data=[
        cr1["1"],
        cr2["1"],
        cr3["1"],
        cr4["1"],
        cr5["1"],
        cr6["1"],
        cr7["1"],
        cr8["1"],
        cr9["1"],
        cr10["1"],
        cr11["1"],
        cr12["1"],
        cr13["1"],
        cr14["1"],
    ]
)
acc_df = pd.DataFrame(
    data=[
        cr1["accuracy"],
        cr2["accuracy"],
        cr3["accuracy"],
        cr4["accuracy"],
        cr5["accuracy"],
        cr6["accuracy"],
        cr7["accuracy"],
        cr8["accuracy"],
        cr9["accuracy"],
        cr10["accuracy"],
        cr11["accuracy"],
        cr12["accuracy"],
        cr13["accuracy"],
        cr14["accuracy"],
    ]
)
new_macro = pd.DataFrame(
    data=[
        cr1["macro avg"],
        cr2["macro avg"],
        cr3["macro avg"],
        cr4["macro avg"],
        cr5["macro avg"],
        cr6["macro avg"],
        cr7["macro avg"],
        cr8["macro avg"],
        cr9["macro avg"],
        cr10["macro avg"],
        cr11["macro avg"],
        cr12["macro avg"],
        cr13["macro avg"],
        cr14["macro avg"],
    ]
)
new_weighted = pd.DataFrame(
    data=[
        cr1["weighted avg"],
        cr2["weighted avg"],
        cr3["weighted avg"],
        cr4["weighted avg"],
        cr5["weighted avg"],
        cr6["weighted avg"],
        cr7["weighted avg"],
        cr8["weighted avg"],
        cr9["weighted avg"],
        cr10["weighted avg"],
        cr11["weighted avg"],
        cr12["weighted avg"],
        cr13["weighted avg"],
        cr14["weighted avg"],
    ]
)


# %%
model_df = pd.DataFrame(
    data=[
        "Decision Tree Base",
        "Decision Tree Tunned using ROC-AUC",
        "Decision Tree Tunned using F1-Weighted",
        "Extreme Gradient Boosting",
        "Random Forest Base",
        "Random Forest Tunned",
        "Logistic Regression BASE",
        "Logistic Regression Tuned",
        "Naive Bayes BASE",
        "Naive Bayes Tuned",
        "XGB Classifier BASE",
        "XGB Classifier Tuned",
        "KNN BASE",
        "KNN Tunned",
    ]
)

# join inner will gives the intersection of df
df_combined = pd.concat(
    (model_df, new_zero, new_one, acc_df, new_macro, new_weighted),
    axis=1,
    join="outer",
    keys=[
        "MODEL NAME",
        "Results for 0's",
        "Results for 1's",
        "Accuracy",
        "Results for macro avg",
        "Results for weighted avg",
    ],
)

df_combined

# %% [markdown]
# ## INFERENCES
#
# DECISION TREE BASE MODEL
# 1. Without using any hyperparameters base model of decision tree is build.
# 2. Using cross validation bias and variance errors are calculated.
# 3. Training and testing accuracy are calculated, Training accuracy is more than the testing accuracy, Our decision tree base model is Overfitted.
# 4. In overfitting model , variance error is more.Therefore to reduce variance error we have build Hypertunned decision tree model.
#
# Hypertunned Decision Tree model
# 1. Fully grown decision tree tends to overfit the model , so to control that we have use max_depth hyperparameter.
# 2. Two model are build , One is using ROC_AUC scoring & another using f1_weighted.
# 3. Using GridsearchCV , we got best max_depth for roc_auc =4 and best max_depth for f1_weighted score =10
# 4. Decision tree model is build for both max_depth using criterion 'entropy'
# 5. We got better accuracy , precision, recall & f1 score for model build using scoring='roc_auc' than the BASE decision tree model
# 6.Training & testing accuracy are nearly equal. so model is not overfitted or underfitted
# 7. Since Precision , recall,f1 scores are not good for 1's therefore we have build extreme gradient boost model.
#
#
# Extreme Gradient Boosting
# 1. Extreme gradient boosting model will reduce bias as well as variance error.
# 2. n estimators are found using GridsearchCV , we got best value for n_estimator=6.
# 3. XGBoost model is build , Variance & bias errors are less as compared to the Hypertunned decison tree model.
# 4. Training & testing accuracy are nearly equal. so model is not overfitted or underfitted
# 5. Precision ,recall ,f1-score & accuracy scores for 1's are improved & better than the previously build models.
#
#
# Random forest Base model
# 1. Since we can only reduce variance error using max_depth hyperparamer in decision tree but cannot reduce bias error so we build Random forest model.
# 2. Random forest base model is build without any hyperparameter.
# 3. We got training accuracy more than testing accuracy , model is overfitted. so we build hypertunned random forest model.
#
# Random Forest Tree model
# 1. Using GridsearchCV we found best n_estimators & criterion.
# 2. Bias and variance error are less as compared to all the models build.
# 3. But precesion , recall & f1-scores of this model are less than the extreme gradient boosting model
# 4. So from all the models build, we got best results for the model build using Extreme gradient boosting.
#
