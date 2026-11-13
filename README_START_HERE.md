# Global Retail Solutions — End-to-End Data Analytics Project

## Project Overview

This project demonstrates an end-to-end data analytics workflow using Python, SQL, Pandas, NumPy, SQLite, Matplotlib, and Excel.

The goal is to analyze retail sales data, identify business trends, measure profitability, and present meaningful insights through reports and dashboards.

The project uses four synthetic datasets:
- Customers
- Products
- Employees
- Orders

**Project Type:** End-to-End Data Analytics  
**Tools:** Python, SQL, Pandas, NumPy, SQLite, Matplotlib, Excel  
**Data Source:** Synthetic retail business data


## Key Business Results

| Business KPI | Result |
|---|---:|
| Total Orders | 1,200 |
| Total Quantity Sold | 4,809 |
| Total Net Sales | $1,725,848.67 |
| Estimated Profit | $650,395.56 |
| Average Order Value | $1,438.21 |
| Overall Profit Margin | 37.69% |

## Project Deliverables

- Data cleaning and preparation
- SQL-based data analysis
- Sales and profit calculations
- Monthly sales trend analysis
- Product and customer performance analysis
- Business KPI calculations
- Excel reports and interactive-style dashboard charts


## Technical Skills Demonstrated

- **Python:** Data analysis and automation
- **Pandas:** Data cleaning, transformation, grouping, and aggregation
- **NumPy:** Numerical calculations
- **SQL:** Queries, joins, filtering, and business analysis
- **SQLite:** Database creation and management
- **Matplotlib:** Business data visualization
- **OpenPyXL:** Excel report formatting, charts, and dashboard creation
- **Git and GitHub:** Version control and project management

## Project Outcome

Successfully developed an end-to-end retail analytics project that transforms raw business data into meaningful business insights and professional reports.


## Project Folder Structure

```text
Global_Retail_Analytics_Project/
│
├── data/
│   ├── customers.csv
│   ├── products.csv
│   ├── employees.csv
│   └── orders.csv
│
├── logs/
│
├── reports/
│   ├── charts/
│   ├── employee_performance.csv
│   ├── monthly_sales.csv
│   ├── Monthly_Sales_Report.xlsx
│   ├── sales_by_category.csv
│   ├── sales_by_city.csv
│   └── top_10_customers.csv
│
├── global_retail.db
├── global_retail_analysis.py
├── requirements.txt
├── DATA_DICTIONARY.md
├── README_START_HERE.md
└── .gitignore
```



## Project story
You are a junior data analyst at Global Retail Solutions, a fictional Canadian retailer.
Management wants to understand sales, customers, products, cities, and employee performance.

All supplied data is synthetic and created for learning. It does not represent real people or a real company.

## Included files
- `data/customers.csv` — customer profiles and locations
- `data/products.csv` — product categories, prices, costs, and stock
- `data/employees.csv` — employee and department information
- `data/orders.csv` — 1,200 sales transactions
- `global_retail_analysis.py` — complete project code, divided into VS Code `# %%` cells
- `requirements.txt` — required Python libraries

## 1. Open in VS Code
1. Extract the ZIP file.
2. In VS Code choose **File → Open Folder** and select `Global_Retail_Analytics_Project`.
3. Open `global_retail_analysis.py`.

## 2. Install libraries
Open the VS Code terminal and run:
```powershell
python -m pip install -r requirements.txt
```

If you want to run one cell at a time, install the VS Code **Python** and **Jupyter** extensions. Then click **Run Cell** above each `# %%` section. Alternatively run the entire file:
```powershell
python global_retail_analysis.py
```

## 3. Project flow
1. Import Python libraries.
2. Set up folders for data, logs, and reports.
3. Configure logging so the program records what it does.
4. Create a SQLite database connection with SQLAlchemy.
5. Read every CSV in `data/` and load it into a database table with Pandas `to_sql()`.
6. Read the database tables back into Pandas DataFrames.
7. Clean dates, numeric columns, and duplicate order IDs.
8. Merge orders with customers, products, and employees to create one analysis-ready sales table.
9. Calculate gross sales, net sales, and estimated profit.
10. Create business summaries and charts.
11. Print key performance indicators (KPIs).

## 4. Key concepts in simple language
- **CSV:** a plain-text table file.
- **DataFrame:** a table held in Python using Pandas.
- **SQLite:** a small database stored in one `.db` file.
- **SQLAlchemy engine:** the connection object Pandas uses to communicate with SQLite.
- **Ingestion:** moving source data into a database.
- **Logging:** writing a record of program activity to a log file.
- **Merge:** combining tables using a shared key, such as `Customer_ID`.
- **GroupBy:** grouping records to calculate totals or averages.
- **KPI:** a key number used to monitor business performance.

## 5. Business questions answered
- Which cities generate the most net sales?
- Which product categories generate the most net sales?
- How do sales change month by month?
- Who are the top 10 customers by net sales?
- Which employees handled the most sales?
- What are total revenue, order count, average order value, and estimated profit?

## 6. Output files
After running the project, look in:
- `global_retail.db` — SQLite database
- `logs/project.log` — ingestion and run log
- `reports/sales_by_city.csv`
- `reports/sales_by_category.csv`
- `reports/monthly_sales.csv`
- `reports/top_10_customers.csv`
- `reports/employee_performance.csv`
- `reports/charts/` — PNG charts

## Important business assumptions
- Each row in `orders.csv` represents one order line with one product.
- Net Sales = Quantity × Unit Price − Discount.
- Estimated Profit = Net Sales − Quantity × Unit Cost. This is a simplified estimate and excludes overhead, tax, shipping, and returns.
- The generated data covers 2024 through late 2026 and is synthetic.
- Product stock is a snapshot field; the project does not calculate inventory movements.

## Suggested study method
Do not try to memorize the entire script. Start with cells 1–5, understand ingestion, and run them. Then continue to reading tables, merging, grouping, and charts. Change one thing at a time and observe the output.
