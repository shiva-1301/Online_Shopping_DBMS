# 🛒 Online Shopping DBMS

### 💻 Technologies Used
**Oracle 11g | SQL | PL/SQL | HTML | CSS | JavaScript**

---

## 📘 Project Overview
The **Online Shopping DBMS** is a database-driven application designed to efficiently manage online shopping operations — including products, customers, orders, and transactions.  
It combines the power of **Oracle SQL & PL/SQL** for backend data management with a **user-friendly front-end interface** for seamless customer interaction.

---

## ⚙️ Key Features
- 🗂️ **Comprehensive Database Design** – Efficiently manages data for products, customers, and orders.  
- 🧾 **Order Details Table** – Tracks product quantities and maintains accurate order histories.  
- 📊 **Advanced SQL Queries & PL/SQL Procedures** – Handles inventory management, sales tracking, and customer analytics.  
- 💬 **Interactive Front-End** – Allows customers to browse products, place orders, and check order status.  
- 🔒 **Data Integrity & Reliability** – Ensures consistent and secure transaction handling.

---

## 🏗️ Database Schema (Overview)
**Main Tables:**
- `PRODUCTS` – Stores product details such as name, price, and stock quantity.  
- `CUSTOMERS` – Holds customer information and contact details.  
- `ORDERS` – Records order-level data including date and total amount.  
- `ORDER_DETAILS` – Links orders with products to track quantity and price.  
- `TRANSACTIONS` – Manages payment details and status updates.  

---

## 🧠 Example SQL Features
```sql
-- Fetch top 5 customers by total purchases
SELECT customer_name, SUM(order_total) AS total_spent
FROM orders
GROUP BY customer_name
ORDER BY total_spent DESC
FETCH FIRST 5 ROWS ONLY;
