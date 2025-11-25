import cx_Oracle
from datetime import datetime

# Initialize the database connection
db1 = None

def connect():
    global db1
    db1 = cx_Oracle.connect(user="sd", password="sd", dsn="localhost:1521/XE")

connect()

# Create a cursor to interact with the database
c1 = db1.cursor()

# Function to check if a table exists before dropping
def table_exists(cursor, table_name):
    cursor.execute("""
        SELECT COUNT(*) FROM all_tables WHERE table_name = :table_name
    """, {"table_name": table_name.upper()})
    return cursor.fetchone()[0] > 0

# Function to drop tables if they exist
def drop_table_with_retry(cursor, table_name, retries=5):
    for attempt in range(1, retries + 1):
        try:
            if table_exists(cursor, table_name):
                cursor.execute(f"DROP TABLE {table_name} CASCADE CONSTRAINTS")
                print(f"Table {table_name} dropped successfully.")
            else:
                print(f"Table {table_name} does not exist, skipping.")
            break
        except cx_Oracle.DatabaseError as e:
            print(f"Error occurred while dropping table {table_name}: {str(e)}")

# List of tables to drop
tables = ["TRACKING_DETAILS", "PAYMENT", "CART", "ORDER_DETAILS", "ORDERS", "CUSTOMER", "PRODUCT", "PRODUCT_CATEGORY", "SUPPLIER", "SHOPPING_WEBSITE", "ADMIN"]

# Drop each table if it exists
for table in tables:
    drop_table_with_retry(c1, table)

# Create tables

# Admin table
c1.execute("""
    CREATE TABLE ADMIN (
        Admin_id VARCHAR2(15) PRIMARY KEY,
        Admin_role VARCHAR2(50),
        Admin_name VARCHAR2(50)
    )
""")

# Shopping Website table
c1.execute("""
    CREATE TABLE SHOPPING_WEBSITE (
        Web_id VARCHAR2(15) PRIMARY KEY,
        Website_name VARCHAR2(50),
        Website_url VARCHAR2(100),
        Contact_no VARCHAR2(15),
        Admin_id VARCHAR2(15),
        FOREIGN KEY (Admin_id) REFERENCES ADMIN(Admin_id)
    )
""")

# Supplier table
c1.execute("""
    CREATE TABLE SUPPLIER (
        Supplier_id VARCHAR2(15) PRIMARY KEY,
        Supplier_name VARCHAR2(50),
        Supplier_address VARCHAR2(100)
    )
""")

# Product Category table
c1.execute("""
    CREATE TABLE PRODUCT_CATEGORY (
        Category_id VARCHAR2(15) PRIMARY KEY,
        Category_name VARCHAR2(50),
        Web_id VARCHAR2(15),
        FOREIGN KEY (Web_id) REFERENCES SHOPPING_WEBSITE(Web_id)
    )
""")

# Product table
c1.execute("""
    CREATE TABLE PRODUCT (
        Product_id VARCHAR2(15) PRIMARY KEY,
        Product_name VARCHAR2(50),
        Product_price NUMBER(10, 2),
        Product_status VARCHAR2(20),
        Supplier_id VARCHAR2(15),
        Category_id VARCHAR2(15),
        FOREIGN KEY (Supplier_id) REFERENCES SUPPLIER(Supplier_id),
        FOREIGN KEY (Category_id) REFERENCES PRODUCT_CATEGORY(Category_id)
    )
""")

# Cart table
c1.execute("""
    CREATE TABLE CART (
        C_Size NUMBER,
        Quantity NUMBER,
        Product_id VARCHAR2(15),
        FOREIGN KEY (Product_id) REFERENCES PRODUCT(Product_id)
    )
""")

# Customer table
c1.execute("""
    CREATE TABLE CUSTOMER (
        Customer_id VARCHAR2(15) PRIMARY KEY,
        Name VARCHAR2(50),
        Address VARCHAR2(100),
        Contact_no VARCHAR2(15)
    )
""")

# Order table
c1.execute("""
    CREATE TABLE ORDERS (
        Order_id VARCHAR2(15) PRIMARY KEY,
        Order_amount NUMBER(10, 2),
        Order_Date DATE,
        Customer_id VARCHAR2(15),
        FOREIGN KEY (Customer_id) REFERENCES CUSTOMER(Customer_id)
    )
""")

# Order Details table
c1.execute("""
    CREATE TABLE ORDER_DETAILS (
        Order_id VARCHAR2(15) NOT NULL,
        Product_id VARCHAR2(15) NOT NULL,
        Quantity NUMBER,
        PRIMARY KEY (Order_id, Product_id),
        FOREIGN KEY (Order_id) REFERENCES ORDERS(Order_id),
        FOREIGN KEY (Product_id) REFERENCES PRODUCT(Product_id)
    )
""")

# Payment table
c1.execute("""
    CREATE TABLE PAYMENT (
        Payment_no VARCHAR2(15) PRIMARY KEY,
        Payment_amount NUMBER(10, 2),
        Payment_date DATE,
        Order_id VARCHAR2(15),
        FOREIGN KEY (Order_id) REFERENCES ORDERS(Order_id)
    )
""")

# Tracking Details table
c1.execute("""
    CREATE TABLE TRACKING_DETAILS (
        Tracking_no VARCHAR2(15) PRIMARY KEY,
        Courier_name VARCHAR2(50),
        Order_id VARCHAR2(15),
        FOREIGN KEY (Order_id) REFERENCES ORDERS(Order_id)
    )
""")


# Commit all the changes
db1.commit()

# Close the cursor and connection
c1.close()
db1.close()

print("Database setup completed successfully.")