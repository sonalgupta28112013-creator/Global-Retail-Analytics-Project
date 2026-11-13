# Data dictionary

## customers.csv
- Customer_ID: unique customer key
- Customer_Name: customer full name
- City / State: customer location
- Customer_Segment: Consumer, Corporate, or Small Business
- Signup_Date: date customer joined

## products.csv
- Product_ID: unique product key
- Product_Name: product name
- Product_Category: product grouping
- Unit_Price: selling price per unit
- Unit_Cost: estimated cost per unit
- Stock_Quantity: sample stock snapshot

## employees.csv
- Employee_ID: unique employee key
- Employee_Name: employee name
- Department: Sales, Customer Success, or Operations
- Office_City: employee office location
- Hire_Year: year hired

## orders.csv
- Order_ID: unique order-line ID
- Order_Date: transaction date
- Customer_ID / Product_ID / Employee_ID: keys linking to the other files
- Quantity: units sold
- Discount: discount amount for the order line
- Payment_Mode: payment method
- Sales_Channel: Online, In-Store, or Phone
