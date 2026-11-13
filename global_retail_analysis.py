# %% [1] IMPORT LIBRARIES AND SET UP FOLDERS
import os
import logging
import time
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
CHART_DIR = os.path.join(REPORT_DIR, "charts")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

# %% [2] SET UP LOGGING
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "project.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

# %% [3] CONNECT TO SQLITE DATABASE
db_path = os.path.join(BASE_DIR, "global_retail.db")
engine = create_engine(f"sqlite:///{db_path}")
print("Database connection is ready.")

# %% [4] LOAD CSV FILES INTO SQLITE
def ingest_csv_files():
    start_time = time.time()
    csv_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".csv")]

    if not csv_files:
        print("No CSV files found in the data folder.")
        return

    for file_name in csv_files:
        file_path = os.path.join(DATA_DIR, file_name)
        df = pd.read_csv(file_path)

        # Basic text cleaning: trim spaces in text columns
        text_cols = df.select_dtypes(include=["object", "string"]).columns
        for col in text_cols:
            df[col] = df[col].astype("string").str.strip()

        table_name = os.path.splitext(file_name)[0]
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)

        logging.info("Loaded %s with %s rows", file_name, len(df))
        print(f"Loaded {file_name}: {len(df)} rows")

    elapsed = round(time.time() - start_time, 2)
    logging.info("CSV ingestion finished in %s seconds", elapsed)
    print(f"Ingestion complete in {elapsed} seconds.")

# %% [5] RUN DATA INGESTION
ingest_csv_files()

# %% [6] READ TABLES BACK FROM SQLITE
customers = pd.read_sql("SELECT * FROM customers", con=engine)
products = pd.read_sql("SELECT * FROM products", con=engine)
employees = pd.read_sql("SELECT * FROM employees", con=engine)
orders = pd.read_sql("SELECT * FROM orders", con=engine)

print("Customers:", customers.shape)
print("Products:", products.shape)
print("Employees:", employees.shape)
print("Orders:", orders.shape)

# %% [7] CLEAN AND PREPARE DATA
orders["Order_Date"] = pd.to_datetime(orders["Order_Date"], errors="coerce")
orders["Quantity"] = pd.to_numeric(orders["Quantity"], errors="coerce")
orders["Discount"] = pd.to_numeric(orders["Discount"], errors="coerce").fillna(0)
products["Unit_Price"] = pd.to_numeric(products["Unit_Price"], errors="coerce")
products["Unit_Cost"] = pd.to_numeric(products["Unit_Cost"], errors="coerce")

orders = orders.drop_duplicates(subset=["Order_ID"])
orders = orders.dropna(subset=["Order_Date", "Customer_ID", "Product_ID"])

# %% [8] CREATE A MASTER SALES DATASET USING MERGE
sales = orders.merge(customers, on="Customer_ID", how="left")
sales = sales.merge(products, on="Product_ID", how="left")
sales = sales.merge(employees, on="Employee_ID", how="left")

sales["Gross_Sales"] = sales["Quantity"] * sales["Unit_Price"]
sales["Net_Sales"] = sales["Gross_Sales"] - sales["Discount"]
sales["Estimated_Profit"] = (
    sales["Net_Sales"] - (sales["Quantity"] * sales["Unit_Cost"])
)
sales["Order_Month"] = sales["Order_Date"].dt.to_period("M").astype(str)

print(sales[["Order_ID", "Customer_Name", "Product_Name", "Net_Sales"]].head())

# %% [9] BUSINESS SUMMARY 1: SALES BY CITY
sales_by_city = (
    sales.groupby("City", as_index=False)["Net_Sales"]
    .sum()
    .sort_values("Net_Sales", ascending=False)
)
sales_by_city.to_csv(os.path.join(REPORT_DIR, "sales_by_city.csv"), index=False)
print(sales_by_city.head(10))

# %% [10] BUSINESS SUMMARY 2: SALES BY PRODUCT CATEGORY
sales_by_category = (
    sales.groupby("Product_Category", as_index=False)["Net_Sales"]
    .sum()
    .sort_values("Net_Sales", ascending=False)
)
sales_by_category.to_csv(os.path.join(REPORT_DIR, "sales_by_category.csv"), index=False)
print(sales_by_category)

# %% [11] BUSINESS SUMMARY 3: MONTHLY SALES
monthly_sales = (
    sales.groupby("Order_Month", as_index=False)["Net_Sales"]
    .sum()
    .sort_values("Order_Month")
)
monthly_sales.to_csv(os.path.join(REPORT_DIR, "monthly_sales.csv"), index=False)

# %% [12] BUSINESS SUMMARY 4: TOP 10 CUSTOMERS
top_customers = (
    sales.groupby(["Customer_ID", "Customer_Name"], as_index=False)["Net_Sales"]
    .sum()
    .sort_values("Net_Sales", ascending=False)
    .head(10)
)
top_customers.to_csv(os.path.join(REPORT_DIR, "top_10_customers.csv"), index=False)

# %% [13] BUSINESS SUMMARY 5: EMPLOYEE SALES PERFORMANCE
employee_performance = (
    sales.groupby(["Employee_ID", "Employee_Name", "Department"], as_index=False)
    .agg(Total_Sales=("Net_Sales", "sum"), Orders_Handled=("Order_ID", "nunique"))
    .sort_values("Total_Sales", ascending=False)
)
employee_performance.to_csv(
    os.path.join(REPORT_DIR, "employee_performance.csv"), index=False
)

# %% [14] VISUALIZATION: SALES BY CATEGORY
plt.figure(figsize=(9, 5))
plt.bar(sales_by_category["Product_Category"], sales_by_category["Net_Sales"])
plt.title("Net Sales by Product Category")
plt.xlabel("Product Category")
plt.ylabel("Net Sales ($)")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "sales_by_category.png"))
plt.show()

# %% [15] VISUALIZATION: MONTHLY SALES TREND
plt.figure(figsize=(11, 5))
plt.plot(monthly_sales["Order_Month"], monthly_sales["Net_Sales"], marker="o")
plt.title("Monthly Net Sales Trend")
plt.xlabel("Month")
plt.ylabel("Net Sales ($)")
plt.xticks(rotation=60)
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "monthly_sales_trend.png"))
plt.show()

# %% [16] FINAL BUSINESS KPIs
total_revenue = sales["Net_Sales"].sum()
total_orders = sales["Order_ID"].nunique()
average_order_value = total_revenue / total_orders if total_orders else 0
total_profit = sales["Estimated_Profit"].sum()

print("\n========== COMPANY PERFORMANCE ==========")
print(f"Total Revenue: ${total_revenue:,.2f}")
print(f"Total Orders: {total_orders:,}")
print(f"Average Order Value: ${average_order_value:,.2f}")
print(f"Estimated Profit: ${total_profit:,.2f}")
print("Reports and charts saved in the reports folder.")


# %%
import pandas as pd
import os

data_folder = "data"

files = os.listdir(data_folder)

print(files)


# %%
import pandas as pd

customers = pd.read_csv("data/customers.csv")

print(customers.head())
# %%


# %%
print("Dataset shape:", customers.shape)

print("\nColumn names:")
print(customers.columns)

print("\nDataset information:")
customers.info()
# %%

# %%
print(customers.isnull().sum())

# %%
print("Total missing values:", customers.isnull().sum().sum())
# %%

# %%
print("Total duplicate rows:", customers.duplicated().sum())
# %%
# %%
print("Duplicate Customer IDs:", customers["Customer_ID"].duplicated().sum())
# %%
# %%
print(customers["City"].value_counts())
# %%

# %%
print(customers["City"].value_counts(normalize=True) * 100)
# %%
# %%
print(customers["Membership"].value_counts())
# %%


# %%
print(customers["Membership"].value_counts())
# %%
# %%
print(customers.columns.tolist())
# %%

# %%
print(customers["Customer_Segment"].value_counts())
# %%
# %%
print(customers["Customer_Segment"].value_counts(normalize=True) * 100)
# %%
# %%
products = pd.read_csv("data/products.csv")

print(products.head())
# %%
# %%
print("Shape:", products.shape)

print("\nColumns:")
print(products.columns.tolist())

print("\nDataset information:")
products.info()
# %%
# %%
print(products["Product_Category"].value_counts())
# %%
# %%
products["Profit_Per_Unit"] = (
    products["Unit_Price"] - products["Unit_Cost"]
)

print(products[[
    "Product_Name",
    "Unit_Price",
    "Unit_Cost",
    "Profit_Per_Unit"
]])
# %%
# %%
highest_profit = products.loc[
    products["Profit_Per_Unit"].idxmax()
]

print(highest_profit)
# %%
# %%
print(
    products.sort_values(
        by="Profit_Per_Unit",
        ascending=False
    )[["Product_Name", "Unit_Price", "Unit_Cost", "Profit_Per_Unit"]]
)
# %%
# %%
sorted_products = products.sort_values(
    by="Profit_Per_Unit",
    ascending=False
)

print(sorted_products[
    ["Product_Name", "Profit_Per_Unit"]
])
# %%
# %%
employees = pd.read_csv("data/employees.csv")

print(employees.head())
# %%
# %%
print("Shape:", employees.shape)

print("Columns:", employees.columns.tolist())

employees.info()
# %%
# %%
print(employees["Department"].value_counts())
# %%
# %%
orders = pd.read_csv("data/orders.csv")

print(orders.head())
# %%
# %%
print("Shape:", orders.shape)

print("\nColumns:")
print(orders.columns.tolist())

print("\nDataset information:")
orders.info()
# %%
# %%
orders["Order_Date"] = pd.to_datetime(
    orders["Order_Date"]
)

print(orders["Order_Date"].dtype)
# %%
# %%
orders["Month"] = orders["Order_Date"].dt.month_name()

print(orders["Month"].value_counts())
# %%
# %%
monthly_orders = (
    orders.groupby(orders["Order_Date"].dt.to_period("M"))
    ["Order_ID"].count()
)

print(monthly_orders)
# %%

# %%
import sqlalchemy

print("SQLAlchemy version:", sqlalchemy.__version__)
# %%
# %%
from sqlalchemy import create_engine
# %%
# %%
engine = create_engine("sqlite:///global_retail.db")

print("Database engine created successfully!")
# %%
"sqlite:///global_retail.db"

# %%
with engine.connect() as connection:
    print("Successfully connected to SQLite database!")
# %%

# %%
import pandas as pd
# %%

# %%
customers = pd.read_csv("data/customers.csv")

print(customers.head())
# %%
# %%
customers.to_sql(
    name="customers",
    con=engine,
    if_exists="replace",
    index=False
)

print("Customers table loaded successfully!")
# %%
# %%
print(pd.read_sql("SELECT * FROM customers LIMIT 5", engine))
# %%
# %%
products = pd.read_csv("data/products.csv")
employees = pd.read_csv("data/employees.csv")
orders = pd.read_csv("data/orders.csv")
# %%
# %%
products.to_sql("products", engine, if_exists="replace", index=False)
employees.to_sql("employees", engine, if_exists="replace", index=False)
orders.to_sql("orders", engine, if_exists="replace", index=False)

print("All three tables loaded successfully!")
# %%
# %%
tables = ["customers", "products", "employees", "orders"]

for table in tables:
    count = pd.read_sql(
        f"SELECT COUNT(*) AS total_rows FROM {table}",
        engine
    )
    print(table, ":", count.iloc[0, 0], "records")
# %%
# %%
query = """
SELECT *
FROM customers
LIMIT 10
"""

result = pd.read_sql(query, engine)

print(result)
# %%
# %%
query = """
SELECT COUNT(*) AS total_orders
FROM orders
"""

result = pd.read_sql(query, engine)

print(result)
# %%
# %%
query = """
SELECT City, COUNT(*) AS total_customers
FROM customers
GROUP BY City
ORDER BY total_customers DESC
"""

result = pd.read_sql(query, engine)

print(result)
# %%


# %%
query = """
SELECT
    orders.Order_ID,
    orders.Customer_ID,
    customers.Customer_Name,
    customers.City,
    orders.Quantity
FROM orders
INNER JOIN customers
ON orders.Customer_ID = customers.Customer_ID
LIMIT 10
"""

result = pd.read_sql(query, engine)

print(result)
# %%

# %%
query = """
SELECT
    orders.Order_ID,
    orders.Product_ID,
    products.Product_Name,
    products.Product_Category,
    orders.Quantity,
    products.Unit_Price
FROM orders
INNER JOIN products
ON orders.Product_ID = products.Product_ID
LIMIT 10
"""

result = pd.read_sql(query, engine)

print(result)
# %%
# %%
query = """
SELECT
    orders.Order_ID,
    products.Product_Name,
    orders.Quantity,
    products.Unit_Price,
    orders.Quantity * products.Unit_Price AS Gross_Sales
FROM orders
INNER JOIN products
ON orders.Product_ID = products.Product_ID
LIMIT 10
"""

result = pd.read_sql(query, engine)

print(result)
# %%

# %%
query = """
SELECT
    orders.Order_ID,
    products.Product_Name,
    orders.Quantity,
    products.Unit_Price,
    orders.Discount,
    orders.Quantity * products.Unit_Price AS Gross_Sales,
    (orders.Quantity * products.Unit_Price) * orders.Discount AS Discount_Amount,
    (orders.Quantity * products.Unit_Price) * (1 - orders.Discount) AS Net_Sales
FROM orders
INNER JOIN products
ON orders.Product_ID = products.Product_ID
LIMIT 10
"""

result = pd.read_sql(query, engine)

print(result)
# %%


# %%
query = """
SELECT
    orders.Order_ID,
    products.Product_Name,
    orders.Quantity,
    products.Unit_Price,
    products.Unit_Cost,
    orders.Discount,

    orders.Quantity * products.Unit_Price AS Gross_Sales,

    orders.Quantity * products.Unit_Price * orders.Discount
        AS Discount_Amount,

    orders.Quantity * products.Unit_Price * (1 - orders.Discount)
        AS Net_Sales,

    orders.Quantity * products.Unit_Cost AS Total_Cost,

    (orders.Quantity * products.Unit_Price * (1 - orders.Discount))
        - (orders.Quantity * products.Unit_Cost)
        AS Estimated_Profit

FROM orders
INNER JOIN products
ON orders.Product_ID = products.Product_ID

LIMIT 10
"""

result = pd.read_sql(query, engine)

print(result)
# %%

# %%
query = """
SELECT
    SUM(orders.Quantity * products.Unit_Price) AS Total_Gross_Sales,

    SUM(orders.Quantity * products.Unit_Price * orders.Discount)
        AS Total_Discount,

    SUM(orders.Quantity * products.Unit_Price * (1 - orders.Discount))
        AS Total_Net_Sales,

    SUM(orders.Quantity * products.Unit_Cost) AS Total_Cost,

    SUM(
        orders.Quantity * products.Unit_Price * (1 - orders.Discount)
        - orders.Quantity * products.Unit_Cost
    ) AS Total_Estimated_Profit

FROM orders
INNER JOIN products
ON orders.Product_ID = products.Product_ID
"""

result = pd.read_sql(query, engine)

print(result)
# %%
# %%
query = """
SELECT
    products.Product_Category,

    SUM(
        orders.Quantity * products.Unit_Price * (1 - orders.Discount)
    ) AS Total_Net_Sales,

    SUM(
        orders.Quantity * products.Unit_Cost
    ) AS Total_Cost,

    SUM(
        orders.Quantity * products.Unit_Price * (1 - orders.Discount)
        - orders.Quantity * products.Unit_Cost
    ) AS Total_Profit

FROM orders

INNER JOIN products
ON orders.Product_ID = products.Product_ID

GROUP BY products.Product_Category

ORDER BY Total_Profit DESC
"""

result = pd.read_sql(query, engine)

print(result)
# %%
# %%
print("Discount values:")
print(orders["Discount"].unique())

print("\nMinimum discount:", orders["Discount"].min())
print("Maximum discount:", orders["Discount"].max())
# %%
# %%
check = pd.read_sql("""
SELECT
    orders.Order_ID,
    products.Product_Name,
    orders.Quantity,
    products.Unit_Price,
    orders.Discount,
    orders.Quantity * products.Unit_Price AS Gross_Sales,
    (orders.Quantity * products.Unit_Price) - orders.Discount AS Net_Sales
FROM orders
INNER JOIN products
ON orders.Product_ID = products.Product_ID
LIMIT 10
""", engine)

print(check)
# %%
# %%
query = """
SELECT
    products.Product_Category,

    SUM(
        orders.Quantity * products.Unit_Price - orders.Discount
    ) AS Total_Net_Sales,

    SUM(
        orders.Quantity * products.Unit_Cost
    ) AS Total_Cost,

    SUM(
        orders.Quantity * products.Unit_Price
        - orders.Discount
        - orders.Quantity * products.Unit_Cost
    ) AS Total_Profit

FROM orders

INNER JOIN products
ON orders.Product_ID = products.Product_ID

GROUP BY products.Product_Category

ORDER BY Total_Profit DESC
"""

result = pd.read_sql(query, engine)

print(result)
# %%
# %%
query = """
SELECT
    strftime('%Y-%m', orders.Order_Date) AS Sales_Month,

    SUM(
        orders.Quantity * products.Unit_Price - orders.Discount
    ) AS Monthly_Net_Sales

FROM orders

INNER JOIN products
ON orders.Product_ID = products.Product_ID

GROUP BY Sales_Month

ORDER BY Sales_Month
"""

monthly_sales = pd.read_sql(query, engine)

print(monthly_sales)
# %%
# %%
highest_month = monthly_sales.loc[
    monthly_sales["Monthly_Net_Sales"].idxmax()
]

print("Highest Sales Month:")
print(highest_month)
# %%
# %%
import pandas as pd

query = """
SELECT
    strftime('%Y-%m', orders.Order_Date) AS Sales_Month,
    SUM(
        orders.Quantity * products.Unit_Price - orders.Discount
    ) AS Monthly_Net_Sales
FROM orders
INNER JOIN products
ON orders.Product_ID = products.Product_ID
GROUP BY Sales_Month
ORDER BY Sales_Month
"""

monthly_sales = pd.read_sql(query, engine)

print(monthly_sales)
# %%
# %%
import pandas as pd
from sqlalchemy import create_engine
# %%
# %%
engine = create_engine("sqlite:///global_retail.db")

with engine.connect() as connection:
    print("Database connected successfully!")
# %%
# %%
query = """
SELECT
    strftime('%Y-%m', orders.Order_Date) AS Sales_Month,
    SUM(
        orders.Quantity * products.Unit_Price - orders.Discount
    ) AS Monthly_Net_Sales
FROM orders
INNER JOIN products
ON orders.Product_ID = products.Product_ID
GROUP BY Sales_Month
ORDER BY Sales_Month
"""

monthly_sales = pd.read_sql(query, engine)

print(monthly_sales)
# %%
# %%
highest_month = monthly_sales.loc[
    monthly_sales["Monthly_Net_Sales"].idxmax()
]

lowest_month = monthly_sales.loc[
    monthly_sales["Monthly_Net_Sales"].idxmin()
]

print("Highest sales month:\n", highest_month)
print("\nLowest sales month:\n", lowest_month)
print("\nAverage monthly sales:",
      round(monthly_sales["Monthly_Net_Sales"].mean(), 2))

# %%
query = """
SELECT
    MIN(Order_Date) AS First_Order,
    MAX(Order_Date) AS Last_Order,
    COUNT(*) AS Total_Orders
FROM orders
"""

date_check = pd.read_sql(query, engine)

print(date_check)
# %%
# %%
print("Total months analysed:", len(monthly_sales))
# %%
# %% Lesson 31: Sales by Channel

query = """
SELECT
    orders.Sales_Channel,
    COUNT(orders.Order_ID) AS Total_Orders,
    SUM(orders.Quantity) AS Total_Quantity_Sold,
    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Total_Net_Sales
FROM orders
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
GROUP BY orders.Sales_Channel
ORDER BY Total_Net_Sales DESC
"""

channel_sales = pd.read_sql(query, engine)

print(channel_sales)
# %%

# %% Check available sales channels

print(orders["Sales_Channel"].unique())
# %%
# %% Load orders table

orders = pd.read_sql("SELECT * FROM orders", engine)

print(orders.head())
# %%
channel_sales = pd.read_sql(query, engine)
print(channel_sales)
# %% Lesson 32: Available Payment Modes

print(orders["Payment_Mode"].unique())
# %%
# %% Lesson 32: Sales by Payment Mode

query = """
SELECT
    orders.Payment_Mode,
    COUNT(orders.Order_ID) AS Total_Orders,
    SUM(orders.Quantity) AS Total_Quantity_Sold,
    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Total_Net_Sales
FROM orders
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
GROUP BY orders.Payment_Mode
ORDER BY Total_Net_Sales DESC
"""

payment_sales = pd.read_sql(query, engine)

print(payment_sales)
# %%
# %% Calculate Average Order Value

payment_sales["Average_Order_Value"] = (
    payment_sales["Total_Net_Sales"] /
    payment_sales["Total_Orders"]
)

payment_sales["Average_Order_Value"] = (
    payment_sales["Average_Order_Value"].round(2)
)

print(payment_sales[
    ["Payment_Mode", "Average_Order_Value"]
])
# %%
# %% Lesson 33: Sales by Customer Segment

query = """
SELECT
    customers.Customer_Segment,
    COUNT(orders.Order_ID) AS Total_Orders,
    SUM(orders.Quantity) AS Total_Quantity_Sold,
    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Total_Net_Sales
FROM orders
INNER JOIN customers
    ON orders.Customer_ID = customers.Customer_ID
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
GROUP BY customers.Customer_Segment
ORDER BY Total_Net_Sales DESC
"""

segment_sales = pd.read_sql(query, engine)

print(segment_sales)
# %%
# %% Average Order Value by Customer Segment

segment_sales["Average_Order_Value"] = (
    segment_sales["Total_Net_Sales"] /
    segment_sales["Total_Orders"]
).round(2)

print(segment_sales[
    ["Customer_Segment", "Average_Order_Value"]
])
# %%
# %% Lesson 35: Sales by Customer City

query = """
SELECT
    customers.City,
    COUNT(orders.Order_ID) AS Total_Orders,
    SUM(orders.Quantity) AS Total_Quantity_Sold,
    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Total_Net_Sales
FROM orders
INNER JOIN customers
    ON orders.Customer_ID = customers.Customer_ID
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
GROUP BY customers.City
ORDER BY Total_Net_Sales DESC
"""

city_sales = pd.read_sql(query, engine)

print(city_sales)
# %%
# %% Average Order Value by City

city_sales["Average_Order_Value"] = (
    city_sales["Total_Net_Sales"] /
    city_sales["Total_Orders"]
).round(2)

print(
    city_sales[
        ["City", "Average_Order_Value"]
    ]
)
# %%
# %% Lesson 37: Top 10 Best-Selling Products

query = """
SELECT
    products.Product_Name,
    SUM(orders.Quantity) AS Total_Quantity_Sold,
    COUNT(orders.Order_ID) AS Total_Orders,
    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Total_Net_Sales
FROM orders
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
GROUP BY products.Product_Name
ORDER BY Total_Quantity_Sold DESC
LIMIT 10
"""

top_products = pd.read_sql(query, engine)

print(top_products)
# %%
# %% Lesson 38: Top 10 Products by Revenue

query = """
SELECT
    products.Product_Name,
    SUM(orders.Quantity) AS Total_Quantity_Sold,
    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Total_Net_Sales
FROM orders
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
GROUP BY products.Product_Name
ORDER BY Total_Net_Sales DESC
LIMIT 10
"""

top_revenue_products = pd.read_sql(query, engine)

print(top_revenue_products)
# %%
# %% Lesson 39: Top 10 Most Profitable Products

query = """
SELECT
    products.Product_Name,
    SUM(orders.Quantity) AS Total_Quantity_Sold,
    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Total_Net_Sales,
    ROUND(
        SUM(orders.Quantity * products.Unit_Cost), 2
    ) AS Total_Cost,
    ROUND(
        SUM(
            orders.Quantity * products.Unit_Price
            - orders.Discount
            - orders.Quantity * products.Unit_Cost
        ), 2
    ) AS Estimated_Profit
FROM orders
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
GROUP BY products.Product_Name
ORDER BY Estimated_Profit DESC
LIMIT 10
"""

top_profit_products = pd.read_sql(query, engine)

print(top_profit_products)
# %%
# %% Lesson 40: Profit Margin by Product

top_profit_products["Profit_Margin"] = (
    top_profit_products["Estimated_Profit"] /
    top_profit_products["Total_Net_Sales"]
    * 100
).round(2)

print(
    top_profit_products[
        ["Product_Name", "Estimated_Profit", "Profit_Margin"]
    ]
)
# %%
# %% Lesson 41: Profit Margin Chart

import matplotlib.pyplot as plt

plt.figure(figsize=(10, 5))

plt.bar(
    top_profit_products["Product_Name"],
    top_profit_products["Profit_Margin"]
)

plt.title("Profit Margin by Product")
plt.xlabel("Product Name")
plt.ylabel("Profit Margin (%)")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()
plt.show()
# %%
# %% Lesson 42: Revenue Chart by Product

plt.figure(figsize=(10, 5))

plt.bar(
    top_revenue_products["Product_Name"],
    top_revenue_products["Total_Net_Sales"]
)

plt.title("Top 10 Products by Net Sales")
plt.xlabel("Product Name")
plt.ylabel("Net Sales ($)")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()
plt.show()

# %% Lesson 43: Monthly Sales Trend

plt.figure(figsize=(12, 5))

plt.plot(
    monthly_sales["Sales_Month"],
    monthly_sales["Monthly_Net_Sales"],
    marker="o"
)

plt.title("Monthly Net Sales Trend")
plt.xlabel("Month")
plt.ylabel("Net Sales ($)")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()
plt.show()
# %%
# %% Lesson 44: Sales by Customer Segment Chart

plt.figure(figsize=(8, 5))

plt.bar(
    segment_sales["Customer_Segment"],
    segment_sales["Total_Net_Sales"]
)

plt.title("Net Sales by Customer Segment")
plt.xlabel("Customer Segment")
plt.ylabel("Net Sales ($)")

plt.tight_layout()
plt.show()

# %%
# %% Lesson 45: Sales by Payment Mode Chart

plt.figure(figsize=(8, 5))

plt.bar(
    payment_sales["Payment_Mode"],
    payment_sales["Total_Net_Sales"]
)

plt.title("Net Sales by Payment Mode")
plt.xlabel("Payment Mode")
plt.ylabel("Net Sales ($)")

plt.tight_layout()
plt.show()
# %%
# %% Lesson 46: Sales by City Chart

plt.figure(figsize=(10, 5))

plt.bar(
    city_sales["City"],
    city_sales["Total_Net_Sales"]
)

plt.title("Net Sales by City")
plt.xlabel("City")
plt.ylabel("Net Sales ($)")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()
plt.show()
# %%
# %% Lesson 47: Sales by Channel Chart

plt.figure(figsize=(8, 5))

plt.bar(
    channel_sales["Sales_Channel"],
    channel_sales["Total_Net_Sales"]
)

plt.title("Net Sales by Sales Channel")
plt.xlabel("Sales Channel")
plt.ylabel("Net Sales ($)")

plt.tight_layout()
plt.show()
# %%
# %% Lesson 48: Business KPI Summary

query = """
SELECT
    COUNT(orders.Order_ID) AS Total_Orders,

    SUM(orders.Quantity) AS Total_Quantity_Sold,

    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Total_Net_Sales,

    ROUND(
        SUM(
            orders.Quantity * products.Unit_Price
            - orders.Discount
            - orders.Quantity * products.Unit_Cost
        ), 2
    ) AS Total_Estimated_Profit,

    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount)
        / COUNT(orders.Order_ID), 2
    ) AS Average_Order_Value

FROM orders
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
"""

kpi_summary = pd.read_sql(query, engine)

print(kpi_summary.T)
# %%
# %% Lesson 49: Overall Profit Margin

total_sales = kpi_summary.loc[0, "Total_Net_Sales"]

total_profit = kpi_summary.loc[0, "Total_Estimated_Profit"]

overall_profit_margin = (
    total_profit / total_sales
) * 100

print("Overall Profit Margin:", round(overall_profit_margin, 2), "%")
# %%
# %% Lesson 50: Monthly Sales Summary

monthly_summary = monthly_sales.copy()

monthly_summary["Monthly_Net_Sales"] = (
    monthly_summary["Monthly_Net_Sales"].round(2)
)

print(monthly_summary.head(10))
# %%
# %% Check monthly_sales columns

print(monthly_sales.columns)
print(monthly_sales.head())
# %%
print(engine)
# %%
# %% Check project location

import os

print("Current folder:", os.getcwd())
print("Files in folder:", os.listdir())
# %%
# %% Reconnect to existing database

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

engine = create_engine("sqlite:///global_retail.db")

print("Database connected successfully!")
# %%
# %% Recreate Monthly Sales Summary

query = """
SELECT
    strftime('%Y-%m', Order_Date) AS Sales_Month,
    ROUND(
        SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2
    ) AS Monthly_Net_Sales
FROM orders
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
GROUP BY Sales_Month
ORDER BY Sales_Month
"""

monthly_sales = pd.read_sql(query, engine)

print(monthly_sales.head(10))
# %%
# %% Lesson 50: Clean Monthly Sales Summary

monthly_summary = monthly_sales.copy()

monthly_summary["Monthly_Net_Sales"] = (
    monthly_summary["Monthly_Net_Sales"].round(2)
)

print(monthly_summary.head(10))
# %%
# %% Lesson 51: Highest and Lowest Sales Month

highest_month = monthly_summary.loc[
    monthly_summary["Monthly_Net_Sales"].idxmax()
]

lowest_month = monthly_summary.loc[
    monthly_summary["Monthly_Net_Sales"].idxmin()
]

print("Highest Sales Month:")
print(highest_month)

print("\nLowest Sales Month:")
print(lowest_month)
# %%
# %% Lesson 52: Average Monthly Sales

average_monthly_sales = monthly_summary["Monthly_Net_Sales"].mean()

print("Average Monthly Sales: $", round(average_monthly_sales, 2))
# %%
# %% Lesson 53: Month-over-Month Sales Growth

monthly_summary["Sales_Growth_Percent"] = (
    monthly_summary["Monthly_Net_Sales"].pct_change() * 100
).round(2)

print(monthly_summary.head(10))
# %%
# %% Lesson 54: Highest Monthly Growth

highest_growth = monthly_summary.loc[
    monthly_summary["Sales_Growth_Percent"].idxmax()
]

print("Highest Sales Growth Month:")
print(highest_growth)
# %%
# %% Lesson 55: Lowest Monthly Growth

lowest_growth = monthly_summary.loc[
    monthly_summary["Sales_Growth_Percent"].idxmin()
]

print("Lowest Sales Growth Month:")
print(lowest_growth)
# %%
# %% Lesson 56: Export Monthly Sales Report

monthly_summary.to_excel(
    "reports/Monthly_Sales_Report.xlsx",
    index=False
)

print("Monthly Sales Report exported successfully!")
# %%
# %% Lesson 57: Professional Excel Formatting

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

file_path = "reports/Monthly_Sales_Report.xlsx"

workbook = load_workbook(file_path)
sheet = workbook.active

# Format column headings
for cell in sheet[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(
        start_color="1F4E78",
        end_color="1F4E78",
        fill_type="solid"
    )
    cell.alignment = Alignment(horizontal="center")

# Format monthly sales as currency
for cell in sheet["B"][1:]:
    cell.number_format = '$#,##0.00'

# Format growth as percentage
for cell in sheet["C"][1:]:
    cell.number_format = '0.00"%"'

# Adjust column widths
sheet.column_dimensions["A"].width = 18
sheet.column_dimensions["B"].width = 22
sheet.column_dimensions["C"].width = 24

workbook.save(file_path)

print("Excel report formatted successfully!")
# %%
# %% Lesson 58: Create Business Summary Sheet

from openpyxl import load_workbook

file_path = "reports/Monthly_Sales_Report.xlsx"

workbook = load_workbook(file_path)

summary_sheet = workbook.create_sheet("Business Summary")

summary_data = [
    ["Business KPI", "Value"],
    ["Average Monthly Sales", average_monthly_sales],
    ["Highest Sales Month", highest_month["Sales_Month"]],
    ["Highest Monthly Sales", highest_month["Monthly_Net_Sales"]],
    ["Lowest Sales Month", lowest_month["Sales_Month"]],
    ["Lowest Monthly Sales", lowest_month["Monthly_Net_Sales"]],
    ["Highest Growth Month", highest_growth["Sales_Month"]],
    ["Highest Growth (%)", highest_growth["Sales_Growth_Percent"]],
    ["Lowest Growth Month", lowest_growth["Sales_Month"]],
    ["Lowest Growth (%)", lowest_growth["Sales_Growth_Percent"]]
]

for row in summary_data:
    summary_sheet.append(row)

workbook.save(file_path)

print("Business Summary sheet created successfully!")
# %%
# %% Lesson 58: Create Business Summary Sheet

from openpyxl import load_workbook

file_path = "reports/Monthly_Sales_Report.xlsx"

workbook = load_workbook(file_path)

summary_sheet = workbook.create_sheet("Business Summary")

summary_data = [
    ["Business KPI", "Value"],
    ["Average Monthly Sales", average_monthly_sales],
    ["Highest Sales Month", highest_month["Sales_Month"]],
    ["Highest Monthly Sales", highest_month["Monthly_Net_Sales"]],
    ["Lowest Sales Month", lowest_month["Sales_Month"]],
    ["Lowest Monthly Sales", lowest_month["Monthly_Net_Sales"]],
    ["Highest Growth Month", highest_growth["Sales_Month"]],
    ["Highest Growth (%)", highest_growth["Sales_Growth_Percent"]],
    ["Lowest Growth Month", lowest_growth["Sales_Month"]],
    ["Lowest Growth (%)", lowest_growth["Sales_Growth_Percent"]]
]

for row in summary_data:
    summary_sheet.append(row)

workbook.save(file_path)

print("Business Summary sheet created successfully!")
# %%
# %% Lesson 59: Format Business Summary

from openpyxl.styles import Font, PatternFill, Alignment

summary_sheet = workbook["Business Summary"]

# Format headings
for cell in summary_sheet[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(
        start_color="1F4E78",
        end_color="1F4E78",
        fill_type="solid"
    )
    cell.alignment = Alignment(horizontal="center")

# Format currency values
for row in [2, 4, 6]:
    summary_sheet[f"B{row}"].number_format = '$#,##0.00'

# Format growth percentages
for row in [8, 10]:
    summary_sheet[f"B{row}"].number_format = '0.00"%"'

# Adjust column widths
summary_sheet.column_dimensions["A"].width = 28
summary_sheet.column_dimensions["B"].width = 22

workbook.save(file_path)

print("Business Summary formatted successfully!")
# %%
# %% Lesson 60: Create Monthly Sales Chart

from openpyxl.chart import LineChart, Reference

# Select monthly sales worksheet
sales_sheet = workbook["Sheet"]

# Create line chart
chart = LineChart()
chart.title = "Monthly Net Sales Trend"
chart.style = 13
chart.y_axis.title = "Net Sales ($)"
chart.x_axis.title = "Sales Month"

# Select sales data
data = Reference(
    sales_sheet,
    min_col=2,
    min_row=1,
    max_row=sales_sheet.max_row
)

categories = Reference(
    sales_sheet,
    min_col=1,
    min_row=2,
    max_row=sales_sheet.max_row
)

chart.add_data(data, titles_from_data=True)
chart.set_categories(categories)

chart.height = 10
chart.width = 20

# Add chart to worksheet
sales_sheet.add_chart(chart, "E2")

workbook.save(file_path)

print("Monthly Sales Chart created successfully!")
# %%
# %% Check Excel Worksheet Names

print(workbook.sheetnames)
# %%
# %% Lesson 60: Create Monthly Sales Chart

from openpyxl.chart import LineChart, Reference

sales_sheet = workbook["Sheet1"]

chart = LineChart()
chart.title = "Monthly Net Sales Trend"
chart.style = 13
chart.y_axis.title = "Net Sales ($)"
chart.x_axis.title = "Sales Month"

data = Reference(
    sales_sheet,
    min_col=2,
    min_row=1,
    max_row=sales_sheet.max_row
)

categories = Reference(
    sales_sheet,
    min_col=1,
    min_row=2,
    max_row=sales_sheet.max_row
)

chart.add_data(data, titles_from_data=True)
chart.set_categories(categories)

chart.height = 10
chart.width = 20

sales_sheet.add_chart(chart, "E2")

workbook.save(file_path)

print("Monthly Sales Chart created successfully!")
# %%
# %% Lesson 61: Create Dashboard Sheet

if "Dashboard" not in workbook.sheetnames:
    dashboard = workbook.create_sheet("Dashboard")
else:
    dashboard = workbook["Dashboard"]

dashboard["A1"] = "GLOBAL RETAIL SOLUTIONS"
dashboard["A2"] = "BUSINESS PERFORMANCE DASHBOARD"

from openpyxl.styles import Font, PatternFill, Alignment

dashboard["A1"].font = Font(
    bold=True,
    size=20,
    color="FFFFFF"
)

dashboard["A1"].fill = PatternFill(
    start_color="1F4E78",
    end_color="1F4E78",
    fill_type="solid"
)

dashboard["A2"].font = Font(
    bold=True,
    size=14,
    color="1F4E78"
)

dashboard.column_dimensions["A"].width = 35
dashboard.column_dimensions["B"].width = 25

workbook.save(file_path)

print("Dashboard sheet created successfully!")
# %%
# %% Save Dashboard

workbook.save(file_path)

print("Dashboard saved successfully!")
# %%
# %% Lesson 62: Add Business KPIs

dashboard["A4"] = "BUSINESS PERFORMANCE"
dashboard["A5"] = "Total Orders"
dashboard["B5"] = kpi_summary.loc[0, "Total_Orders"]

dashboard["A6"] = "Total Quantity Sold"
dashboard["B6"] = kpi_summary.loc[0, "Total_Quantity_Sold"]

dashboard["A7"] = "Total Net Sales"
dashboard["B7"] = kpi_summary.loc[0, "Total_Net_Sales"]

dashboard["A8"] = "Estimated Profit"
dashboard["B8"] = kpi_summary.loc[0, "Total_Estimated_Profit"]

dashboard["A9"] = "Average Order Value"
dashboard["B9"] = kpi_summary.loc[0, "Average_Order_Value"]

# Currency formatting
for cell in ["B7", "B8", "B9"]:
    dashboard[cell].number_format = '$#,##0.00'

dashboard["A4"].font = Font(bold=True, size=14, color="1F4E78")

workbook.save(file_path)

print("Business KPIs added to Dashboard!")
# %%
# %% Restore Business KPIs

query = """
SELECT
    COUNT(orders.Order_ID) AS Total_Orders,
    SUM(orders.Quantity) AS Total_Quantity_Sold,
    ROUND(SUM(orders.Quantity * products.Unit_Price - orders.Discount), 2) AS Total_Net_Sales,
    ROUND(SUM(orders.Quantity * products.Unit_Price - orders.Discount - orders.Quantity * products.Unit_Cost), 2) AS Total_Estimated_Profit,
    ROUND(SUM(orders.Quantity * products.Unit_Price - orders.Discount) / COUNT(orders.Order_ID), 2) AS Average_Order_Value
FROM orders
INNER JOIN products
    ON orders.Product_ID = products.Product_ID
"""

kpi_summary = pd.read_sql(query, engine)

print(kpi_summary.T)
# %%
# %% Lesson 62: Add Business KPIs

dashboard["A4"] = "BUSINESS PERFORMANCE"

dashboard["A5"] = "Total Orders"
dashboard["B5"] = kpi_summary.loc[0, "Total_Orders"]

dashboard["A6"] = "Total Quantity Sold"
dashboard["B6"] = kpi_summary.loc[0, "Total_Quantity_Sold"]

dashboard["A7"] = "Total Net Sales"
dashboard["B7"] = kpi_summary.loc[0, "Total_Net_Sales"]

dashboard["A8"] = "Estimated Profit"
dashboard["B8"] = kpi_summary.loc[0, "Total_Estimated_Profit"]

dashboard["A9"] = "Average Order Value"
dashboard["B9"] = kpi_summary.loc[0, "Average_Order_Value"]

for cell in ["B7", "B8", "B9"]:
    dashboard[cell].number_format = '$#,##0.00'

dashboard["A4"].font = Font(bold=True, size=14, color="1F4E78")

workbook.save(file_path)

print("Business KPIs added to Dashboard!")
# %%
# %% Lesson 63: Format Dashboard KPIs

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Format main heading
dashboard.merge_cells("A1:B1")
dashboard["A1"].alignment = Alignment(horizontal="center")

# Format KPI section heading
dashboard.merge_cells("A4:B4")
dashboard["A4"].fill = PatternFill(
    start_color="1F4E78",
    end_color="1F4E78",
    fill_type="solid"
)
dashboard["A4"].font = Font(bold=True, color="FFFFFF", size=14)
dashboard["A4"].alignment = Alignment(horizontal="center")

# Format KPI labels and values
for row in range(5, 10):
    dashboard[f"A{row}"].font = Font(bold=True)
    dashboard[f"B{row}"].font = Font(bold=True, color="1F4E78")

    dashboard[f"A{row}"].alignment = Alignment(horizontal="left")
    dashboard[f"B{row}"].alignment = Alignment(horizontal="right")

    dashboard[f"A{row}"].fill = PatternFill(
        start_color="D9EAF7",
        end_color="D9EAF7",
        fill_type="solid"
    )

    dashboard[f"B{row}"].fill = PatternFill(
        start_color="E2F0D9",
        end_color="E2F0D9",
        fill_type="solid"
    )

# Add borders
thin_border = Border(
    bottom=Side(style="thin", color="BFBFBF")
)

for row in range(5, 10):
    dashboard[f"A{row}"].border = thin_border
    dashboard[f"B{row}"].border = thin_border

workbook.save(file_path)

print("Dashboard KPI formatting completed!")
# %%
# %% Lesson 64: Add Sales Chart to Dashboard

from copy import copy

sales_sheet = workbook["Sheet1"]

# Copy the existing chart
original_chart = sales_sheet._charts[0]
dashboard_chart = copy(original_chart)

# Position chart on Dashboard
dashboard.add_chart(dashboard_chart, "D4")

# Save workbook
workbook.save(file_path)

print("Monthly Sales Chart added to Dashboard!")

# %% Lesson 65: Add Overall Profit Margin

total_sales = kpi_summary.loc[0, "Total_Net_Sales"]
total_profit = kpi_summary.loc[0, "Total_Estimated_Profit"]

profit_margin = (total_profit / total_sales) * 100

dashboard["A10"] = "Overall Profit Margin"
dashboard["B10"] = round(profit_margin, 2)

dashboard["B10"].number_format = '0.00"%"'

dashboard["A10"].font = Font(bold=True)
dashboard["B10"].font = Font(bold=True, color="008000")

dashboard["A10"].fill = PatternFill(
    start_color="D9EAF7",
    end_color="D9EAF7",
    fill_type="solid"
)

dashboard["B10"].fill = PatternFill(
    start_color="E2F0D9",
    end_color="E2F0D9",
    fill_type="solid"
)

workbook.save(file_path)

print("Overall Profit Margin added to Dashboard!")
# %%


# %% Lesson 66: Format Profit Margin KPI

dashboard["A10"].alignment = Alignment(horizontal="left")
dashboard["B10"].alignment = Alignment(horizontal="right")

dashboard["A10"].border = thin_border
dashboard["B10"].border = thin_border

dashboard["A10"].font = Font(bold=True)
dashboard["B10"].font = Font(bold=True, color="008000")

workbook.save(file_path)

print("Profit Margin KPI formatted successfully!")
# %%


# %% Lesson 67: Create Sales vs Profit Chart

from openpyxl.chart import BarChart, Reference

dashboard["D2"] = "Business Performance"

dashboard["D3"] = "Metric"
dashboard["E3"] = "Amount"

dashboard["D4"] = "Net Sales"
dashboard["E4"] = kpi_summary.loc[0, "Total_Net_Sales"]

dashboard["D5"] = "Estimated Profit"
dashboard["E5"] = kpi_summary.loc[0, "Total_Estimated_Profit"]

chart = BarChart()
chart.title = "Net Sales vs Estimated Profit"
chart.y_axis.title = "Amount ($)"
chart.x_axis.title = "Business Metric"

data = Reference(dashboard, min_col=5, min_row=3, max_row=5)
categories = Reference(dashboard, min_col=4, min_row=4, max_row=5)

chart.add_data(data, titles_from_data=True)
chart.set_categories(categories)

chart.height = 8
chart.width = 14

dashboard.add_chart(chart, "D7")

workbook.save(file_path)

print("Sales vs Profit chart added successfully!")
# %%

# %% Lesson 68: Format Chart Data as Currency

for cell in ["E4", "E5"]:
    dashboard[cell].number_format = '$#,##0.00'

for cell in ["D3", "E3"]:
    dashboard[cell].font = Font(bold=True, color="FFFFFF")
    dashboard[cell].fill = PatternFill(
        start_color="1F4E78",
        end_color="1F4E78",
        fill_type="solid"
    )

dashboard.column_dimensions["D"].width = 25
dashboard.column_dimensions["E"].width = 20

workbook.save(file_path)

print("Chart data formatted successfully!")
# %%
# %% Lesson 69: Dashboard Completion Check

print("Dashboard Sheets:", workbook.sheetnames)
print("Dashboard Charts:", len(dashboard._charts))

print("\nBusiness KPIs:")
for row in range(5, 11):
    print(dashboard[f"A{row}"].value, ":", dashboard[f"B{row}"].value)

print("\nDashboard verification completed!")
# %%
# %% Lesson 70: Inspect Dashboard Charts

for i, chart in enumerate(dashboard._charts, start=1):
    print(f"Chart {i}")
    print("Position:", chart.anchor._from.col, chart.anchor._from.row)
    print("Title:", chart.title.tx.rich.p[0].r[0].t)
    print("--------------------")
# %%

# %% Lesson 70: Inspect Dashboard Charts

for i, chart in enumerate(dashboard._charts, start=1):
    print(f"Chart {i}")

    if isinstance(chart.anchor, str):
        print("Position:", chart.anchor)
    else:
        print(
            "Position:",
            chart.anchor._from.col,
            chart.anchor._from.row
        )

    print("--------------------")
# %%
# %% Lesson 71: Fix Chart Overlap

dashboard._charts[2].anchor = "D22"

workbook.save(file_path)

print("Chart 3 moved to D22 successfully!")
# %%
# %% Lesson 71: Move Third Chart

dashboard._charts[2].anchor = "D25"

workbook.save(file_path)

print("Third chart moved to D25!")
# %%
# %% Lesson 71: Arrange Dashboard Charts

# Monthly Sales Trend
dashboard._charts[0].anchor = "D4"

# Sales vs Estimated Profit
dashboard._charts[1].anchor = "D25"

# Move the extra third chart further down
dashboard._charts[2].anchor = "D45"

workbook.save(file_path)

print("Dashboard charts rearranged successfully!")
# %%
# %% Lesson 72: Final Dashboard Review

print("PROJECT: GLOBAL RETAIL SOLUTIONS")
print("--------------------------------")

print("Total Orders:", dashboard["B5"].value)
print("Total Quantity Sold:", dashboard["B6"].value)
print("Total Net Sales:", dashboard["B7"].value)
print("Estimated Profit:", dashboard["B8"].value)
print("Average Order Value:", dashboard["B9"].value)
print("Profit Margin:", dashboard["B10"].value, "%")

print("\nTotal Charts:", len(dashboard._charts))
print("Dashboard review completed!")
# %%
# %% List All Project Reports

import os

report_files = os.listdir("reports")

print("Files inside reports folder:")
for file in report_files:
    print("-", file)
# %%
