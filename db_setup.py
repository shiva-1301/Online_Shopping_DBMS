"""Create the Online Shopping schema and load sample data.

Usage:  python db_setup.py
Backend and credentials come from environment variables / .env (see .env.example).
WARNING: drops and recreates all project tables.
"""
from datetime import datetime, timedelta

import database
from database import DB_BACKEND

# Child tables first so foreign keys never block a drop
TABLES = ["TRACKING_DETAILS", "PAYMENT", "CART", "ORDER_DETAILS", "ORDERS", "CUSTOMER",
          "PRODUCT", "PRODUCT_CATEGORY", "SUPPLIER", "SHOPPING_WEBSITE", "ADMIN"]

SCHEMA = [
    """CREATE TABLE ADMIN (
        Admin_id VARCHAR2(15) PRIMARY KEY,
        Admin_role VARCHAR2(50),
        Admin_name VARCHAR2(50) NOT NULL
    )""",
    """CREATE TABLE SHOPPING_WEBSITE (
        Web_id VARCHAR2(15) PRIMARY KEY,
        Website_name VARCHAR2(50) NOT NULL,
        Website_url VARCHAR2(100),
        Contact_no VARCHAR2(15),
        Admin_id VARCHAR2(15),
        FOREIGN KEY (Admin_id) REFERENCES ADMIN(Admin_id)
    )""",
    """CREATE TABLE SUPPLIER (
        Supplier_id VARCHAR2(15) PRIMARY KEY,
        Supplier_name VARCHAR2(50) NOT NULL,
        Supplier_address VARCHAR2(100)
    )""",
    """CREATE TABLE PRODUCT_CATEGORY (
        Category_id VARCHAR2(15) PRIMARY KEY,
        Category_name VARCHAR2(50) NOT NULL,
        Web_id VARCHAR2(15),
        FOREIGN KEY (Web_id) REFERENCES SHOPPING_WEBSITE(Web_id)
    )""",
    # Image_path was queried by the dashboard but missing from the original schema
    """CREATE TABLE PRODUCT (
        Product_id VARCHAR2(15) PRIMARY KEY,
        Product_name VARCHAR2(50) NOT NULL,
        Product_price NUMBER(10, 2) NOT NULL CHECK (Product_price >= 0),
        Product_status VARCHAR2(20),
        Supplier_id VARCHAR2(15),
        Category_id VARCHAR2(15),
        Image_path VARCHAR2(200),
        FOREIGN KEY (Supplier_id) REFERENCES SUPPLIER(Supplier_id),
        FOREIGN KEY (Category_id) REFERENCES PRODUCT_CATEGORY(Category_id)
    )""",
    """CREATE TABLE CART (
        C_Size NUMBER,
        Quantity NUMBER CHECK (Quantity > 0),
        Product_id VARCHAR2(15),
        FOREIGN KEY (Product_id) REFERENCES PRODUCT(Product_id)
    )""",
    """CREATE TABLE CUSTOMER (
        Customer_id VARCHAR2(15) PRIMARY KEY,
        Name VARCHAR2(50) NOT NULL,
        Address VARCHAR2(100),
        Contact_no VARCHAR2(15)
    )""",
    """CREATE TABLE ORDERS (
        Order_id VARCHAR2(15) PRIMARY KEY,
        Order_amount NUMBER(10, 2) CHECK (Order_amount >= 0),
        Order_Date DATE,
        Customer_id VARCHAR2(15),
        FOREIGN KEY (Customer_id) REFERENCES CUSTOMER(Customer_id)
    )""",
    """CREATE TABLE ORDER_DETAILS (
        Order_id VARCHAR2(15) NOT NULL,
        Product_id VARCHAR2(15) NOT NULL,
        Quantity NUMBER CHECK (Quantity > 0),
        PRIMARY KEY (Order_id, Product_id),
        FOREIGN KEY (Order_id) REFERENCES ORDERS(Order_id),
        FOREIGN KEY (Product_id) REFERENCES PRODUCT(Product_id)
    )""",
    """CREATE TABLE PAYMENT (
        Payment_no VARCHAR2(15) PRIMARY KEY,
        Payment_amount NUMBER(10, 2) CHECK (Payment_amount >= 0),
        Payment_date DATE,
        Order_id VARCHAR2(15),
        FOREIGN KEY (Order_id) REFERENCES ORDERS(Order_id)
    )""",
    """CREATE TABLE TRACKING_DETAILS (
        Tracking_no VARCHAR2(15) PRIMARY KEY,
        Courier_name VARCHAR2(50),
        Order_id VARCHAR2(15),
        FOREIGN KEY (Order_id) REFERENCES ORDERS(Order_id)
    )""",
]

CATEGORIES = [("CAT01", "Beauty"), ("CAT02", "Home & Kitchen"), ("CAT03", "Electronics"),
              ("CAT04", "Toys"), ("CAT05", "Books"), ("CAT06", "Footwear"),
              ("CAT07", "Stationery"), ("CAT08", "Sports"), ("CAT09", "Fashion")]

# (id, name, price, category, supplier, image file)
PRODUCTS = [
    ("P02", "Makeup Essentials Kit", 1299, "CAT01", "S01", "2.jpg"),
    ("P03", "3-Seater Fabric Sofa", 24999, "CAT02", "S02", "3.jpg"),
    ("P04", "Smart Home Echo Bundle", 9999, "CAT03", "S03", "4.jpg"),
    ("P05", "Dual-Band WiFi Router", 2499, "CAT03", "S03", "5.jpg"),
    ("P06", "USB-C 4-Port Hub", 899, "CAT03", "S03", "6.jpg"),
    ("P07", "Teddy Bear Plush", 699, "CAT04", "S04", "7.jpg"),
    ("P08", "Reversible Octopus Plush", 349, "CAT04", "S04", "8.jpg"),
    ("P09", "Penguin Soft Toy", 499, "CAT04", "S04", "9.jpg"),
    ("P10", "Soul of South India (Book)", 1495, "CAT05", "S05", "10.jpg"),
    ("P11", "Men's Running Shoes", 1799, "CAT06", "S01", "11.jpg"),
    ("P12", "Women's Flip-Flops", 399, "CAT06", "S01", "12.jpg"),
    ("P13", "iQOO Z9 Lite 5G", 10499, "CAT03", "S03", "13.jpg"),
    ("P14", "Wired Earphones", 399, "CAT03", "S03", "14.jpg"),
    ("P15", "Chromebook Laptop", 21990, "CAT03", "S03", "15.jpg"),
    ("P16", "Greeting Card Set", 199, "CAT07", "S05", "16.jpg"),
    ("P17", "Geometry Stencil Ruler", 149, "CAT07", "S05", "17.jpg"),
    ("P18", "Badminton Racket Set", 1199, "CAT08", "S04", "18.jpg"),
    ("P19", "Puma Football", 899, "CAT08", "S04", "19.jpg"),
    ("P20", "Fridge Storage Box", 549, "CAT02", "S02", "20.jpg"),
    ("P21", "Cotton Crew T-Shirt", 599, "CAT09", "S01", "shirt.jpg"),
]

CUSTOMERS = [
    ("C01", "Aarav Sharma", "12 MG Road, Bengaluru", "9876543210"),
    ("C02", "Diya Patel", "45 Park Street, Kolkata", "9123456780"),
    ("C03", "Rohan Iyer", "7 Anna Salai, Chennai", "9988776655"),
    ("C04", "Sneha Reddy", "22 Jubilee Hills, Hyderabad", "9001122334"),
    ("C05", "Kabir Singh", "3 Connaught Place, Delhi", "9811122233"),
]

# (order id, customer, days ago, [(product, qty), ...])
ORDERS = [
    ("O01", "C01", 1, [("P13", 1), ("P14", 2)]),
    ("O02", "C02", 2, [("P07", 1), ("P08", 2)]),
    ("O03", "C03", 3, [("P15", 1)]),
    ("O04", "C04", 4, [("P02", 2), ("P21", 3)]),
    ("O05", "C05", 5, [("P18", 1), ("P19", 2)]),
    ("O06", "C01", 6, [("P05", 1), ("P06", 1)]),
    ("O07", "C02", 12, [("P10", 1), ("P16", 4)]),
    ("O08", "C03", 18, [("P11", 1), ("P12", 2)]),
    ("O09", "C04", 25, [("P03", 1)]),
    ("O10", "C05", 33, [("P04", 1), ("P20", 3)]),
]

COURIERS = ["BlueDart", "Delhivery", "Ekart", "DTDC"]


def as_date(d):
    """Oracle binds datetime natively; SQLite stores ISO date strings."""
    return d if DB_BACKEND == "oracle" else d.strftime("%Y-%m-%d")


def execute(cursor, sql, params=()):
    cursor.execute(database.to_dialect(sql), params)


def executemany(cursor, sql, rows):
    cursor.executemany(database.to_dialect(sql), rows)


def table_exists(cursor, table_name):
    if DB_BACKEND == "oracle":
        cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :t", {"t": table_name.upper()})
    else:
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = :t", {"t": table_name})
    return cursor.fetchone()[0] > 0


def drop_tables(cursor):
    for table in TABLES:
        if not table_exists(cursor, table):
            print(f"Table {table} does not exist, skipping.")
            continue
        suffix = " CASCADE CONSTRAINTS" if DB_BACKEND == "oracle" else ""
        cursor.execute(f"DROP TABLE {table}{suffix}")
        print(f"Table {table} dropped.")


def seed(cursor):
    execute(cursor, "INSERT INTO ADMIN VALUES ('A01', 'Super Admin', 'admin')")
    execute(cursor, "INSERT INTO SHOPPING_WEBSITE VALUES ('W01', 'ShopEase', 'https://shopease.example', '1800123456', 'A01')")
    executemany(cursor, "INSERT INTO SUPPLIER VALUES (:1, :2, :3)", [
        ("S01", "StyleHub Traders", "Mumbai"), ("S02", "HomeNest Supplies", "Pune"),
        ("S03", "TechWorld Distributors", "Bengaluru"), ("S04", "PlayFit Wholesale", "Jaipur"),
        ("S05", "PaperTrail Books", "Chennai"),
    ])
    executemany(cursor, "INSERT INTO PRODUCT_CATEGORY VALUES (:1, :2, 'W01')", CATEGORIES)
    executemany(cursor, 
        "INSERT INTO PRODUCT VALUES (:1, :2, :3, 'In Stock', :4, :5, :6)",
        [(pid, name, price, sup, cat, f"assets/images/{img}") for pid, name, price, cat, sup, img in PRODUCTS],
    )
    executemany(cursor, "INSERT INTO CUSTOMER VALUES (:1, :2, :3, :4)", CUSTOMERS)

    prices = {p[0]: p[2] for p in PRODUCTS}
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for i, (oid, cid, days_ago, items) in enumerate(ORDERS, start=1):
        order_date = as_date(today - timedelta(days=days_ago))
        amount = sum(prices[pid] * qty for pid, qty in items)
        execute(cursor, "INSERT INTO ORDERS VALUES (:1, :2, :3, :4)", (oid, amount, order_date, cid))
        executemany(cursor, "INSERT INTO ORDER_DETAILS VALUES (:1, :2, :3)", [(oid, pid, qty) for pid, qty in items])
        execute(cursor, "INSERT INTO PAYMENT VALUES (:1, :2, :3, :4)", (f"PAY{i:03}", amount, order_date, oid))
        execute(cursor, "INSERT INTO TRACKING_DETAILS VALUES (:1, :2, :3)",
                       (f"TRK{i:05}", COURIERS[i % len(COURIERS)], oid))
    executemany(cursor, "INSERT INTO CART VALUES (:1, :2, :3)", [(1, 2, "P14"), (1, 1, "P19")])


def main():
    conn = database.connect()
    cursor = conn.cursor()
    try:
        drop_tables(cursor)
        for ddl in SCHEMA:
            cursor.execute(ddl)
        seed(cursor)
        conn.commit()
        print(f"Database setup completed successfully ({DB_BACKEND}).")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
