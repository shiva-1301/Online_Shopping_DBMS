import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cx_Oracle
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sqlite3

# Initialize database connection
try:
    db = cx_Oracle.connect(user="sd", password="sd", dsn="localhost:1521/XE")
    c = db.cursor()
except cx_Oracle.DatabaseError as e:
    messagebox.showerror("Database Error", f"Failed to connect to the database: {e}")

# Function to display bar and line graphs for product sales and weekly sales

def show_stats():
    """Generate multiple plots in separate windows simultaneously."""
    try:
        # Product Sales Quantity (Bar Chart)
        try:
            product_query = """
            SELECT P.Product_name, SUM(OD.Quantity)
            FROM PRODUCT P
            JOIN ORDER_DETAILS OD ON P.Product_id = OD.Product_id
            GROUP BY P.Product_name
            """
            c.execute(product_query)
            product_data = c.fetchall()
            
            if product_data:
                product_names = [row[0] for row in product_data]
                quantities = [row[1] for row in product_data]
                plt.figure("Product Sales Quantity")
                plt.bar(product_names, quantities, color='skyblue')
                plt.title("Product Sales Quantity")
                plt.xlabel("Product")
                plt.ylabel("Quantity Sold")
                plt.xticks(rotation=30)
                plt.show(block=False)
        except Exception as e:
            print(f"Skipping Product Sales Quantity graph: {e}")

        # Sales Last Week (Line Chart)
        try:
            last_week_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            sales_query = """
            SELECT TO_CHAR(O.Order_Date, 'YYYY-MM-DD') AS Order_Date, SUM(O.Order_amount)
            FROM ORDERS O
            WHERE O.Order_Date >= TO_DATE(:last_week_date, 'YYYY-MM-DD')
            GROUP BY TO_CHAR(O.Order_Date, 'YYYY-MM-DD')
            ORDER BY TO_CHAR(O.Order_Date, 'YYYY-MM-DD')
            """
            c.execute(sales_query, {"last_week_date": last_week_date})
            sales_data = c.fetchall()
            
            if sales_data:
                dates = [row[0] for row in sales_data]
                sales_amounts = [row[1] for row in sales_data]
                plt.figure("Sales Last Week")
                plt.plot(dates, sales_amounts, marker='o', color='orange')
                plt.title("Sales Last Week")
                plt.xlabel("Date")
                plt.ylabel("Sales Amount")
                plt.grid(True)
                plt.show(block=False)
        except Exception as e:
            print(f"Skipping Sales Last Week graph: {e}")

        # Daily/Monthly Sales Trends (Line Chart)
        try:
            trends_query = """
            SELECT TO_CHAR(O.Order_Date, 'YYYY-MM-DD') AS Order_Date, SUM(O.Order_amount)
            FROM ORDERS O
            GROUP BY TO_CHAR(O.Order_Date, 'YYYY-MM-DD')
            ORDER BY TO_CHAR(O.Order_Date, 'YYYY-MM-DD')
            """
            c.execute(trends_query)
            trends_data = c.fetchall()
            
            if trends_data:
                trend_dates = [row[0] for row in trends_data]
                trend_sales = [row[1] for row in trends_data]
                plt.figure("Sales Trends")
                plt.plot(trend_dates, trend_sales, marker='o', color='blue')
                plt.title("Daily/Monthly Sales Trends")
                plt.xlabel("Date")
                plt.ylabel("Sales Amount")
                plt.grid(True)
                plt.show(block=False)
        except Exception as e:
            print(f"Skipping Sales Trends graph: {e}")

        # Top 5 Best-Selling Products (Bar Chart)
        try:
            top_products_query = """
            SELECT P.Product_name, SUM(OD.Quantity)
            FROM PRODUCT P
            JOIN ORDER_DETAILS OD ON P.Product_id = OD.Product_id
            GROUP BY P.Product_name
            ORDER BY SUM(OD.Quantity) DESC
            FETCH FIRST 5 ROWS ONLY
            """
            c.execute(top_products_query)
            top_products_data = c.fetchall()
            
            if top_products_data:
                top_product_names = [row[0] for row in top_products_data]
                top_quantities = [row[1] for row in top_products_data]
                plt.figure("Top 5 Products")
                plt.bar(top_product_names, top_quantities, color='green')
                plt.title("Top 5 Best-Selling Products")
                plt.xlabel("Product")
                plt.ylabel("Quantity Sold")
                plt.xticks(rotation=30)
                plt.show(block=False)
        except Exception as e:
            print(f"Skipping Top 5 Products graph: {e}")

        # Revenue Distribution by Category (Pie Chart)
        # Revenue Distribution by Category (Pie Chart)
        try:
            category_query = """
    SELECT C.Category_name, SUM(O.Order_amount)
    FROM CATEGORY C
    JOIN PRODUCT P ON C.Category_id = P.Category_id
    JOIN ORDER_DETAILS OD ON P.Product_id = OD.Product_id
    JOIN ORDERS O ON OD.Order_id = O.Order_id
    GROUP BY C.Category_name
    """
            c.execute(category_query)
            category_data = c.fetchall()

            if category_data:
                category_names = [row[0] for row in category_data]
                category_revenue = [row[1] for row in category_data]

        # Debug: Print fetched data
                print("Category Data:", category_names, category_revenue)

                plt.figure("Revenue Distribution")
                plt.pie(category_revenue, labels=category_names, autopct='%1.1f%%', startangle=90, colors=['red', 'orange', 'blue', 'green'])
                plt.title("Revenue Distribution by Category")

        # Force rendering of pie chart
                plt.show(block=False)
            else:
                    print("Skipping Revenue Distribution graph: No data found.")
        except Exception as e:
                print(f"Skipping Revenue Distribution graph: {e}")

        # Keep all windows open
        plt.show()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to display stats: {e}")

# Function to fetch and display products bought by each customer in a grid layout
def display_customer_products():
    """Fetches and displays products bought by each customer in a grid layout."""
    try:
        # Clear previous display
        for widget in table_display_frame.winfo_children():
            widget.destroy()

        # Fetch data
        query = """
        SELECT C.Name AS Customer_Name, C.Customer_id, O.Order_id, P.Product_name, P.Product_price, OD.Quantity
        FROM CUSTOMER C
        JOIN ORDERS O ON C.Customer_id = O.Customer_id
        JOIN ORDER_DETAILS OD ON O.Order_id = OD.Order_id
        JOIN PRODUCT P ON OD.Product_id = P.Product_id
        ORDER BY C.Customer_id
        """
        c.execute(query)
        rows = c.fetchall()

        if not rows:
            messagebox.showinfo("No Data", "No records to display.")
            return

        # Create scrollable canvas for display
        canvas = tk.Canvas(table_display_frame)
        scrollbar = ttk.Scrollbar(table_display_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Group products by customers
        customer_data = {}
        for row in rows:
            customer_name = row[0]
            customer_id = row[1]
            order_details = row[2:]

            if customer_id not in customer_data:
                customer_data[customer_id] = {
                    "customer_name": customer_name,
                    "products": []
                }
            customer_data[customer_id]["products"].append(order_details)

        # Dynamic grid layout configuration
        max_columns = 3  # Number of customer panels per row
        row_index = 0
        col_index = 0

        for customer_id, data in customer_data.items():
            customer_frame = tk.Frame(scrollable_frame, bd=2, relief=tk.RAISED)
            customer_frame.grid(row=row_index, column=col_index, padx=10, pady=10, sticky="nsew")

            # Customer Title
            customer_label = tk.Label(
                customer_frame, text=f"Products bought by {data['customer_name']} (ID: {customer_id})",
                font=("Arial", 12, "bold")
            )
            customer_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=2)

            # Headers for product details
            headers = ["Order ID", "Product", "Price", "Quantity"]
            for col_num, header in enumerate(headers):
                header_label = tk.Label(
                    customer_frame, text=header, font=("Arial", 12, "bold")
                )
                header_label.grid(row=1, column=col_num, padx=5, pady=2)

            # Display product details in grid format
            for product_row, order_details in enumerate(data["products"], start=2):
                for col_num, value in enumerate(order_details):
                    value_label = tk.Label(
                        customer_frame, text=value, font=("Arial", 10)
                    )
                    value_label.grid(row=product_row, column=col_num, padx=5, pady=2)

            # Update row and column indices for grid layout
            col_index += 1
            if col_index >= max_columns:
                col_index = 0
                row_index += 1

        canvas.update_idletasks()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch customer products: {e}")

# Function to fetch data from the selected table and display it as a grid of record cards centered width-wise
def fetch_table_data(table_name):
    """Fetches data from the selected table and displays it as a grid of record cards centered width-wise."""
    try:
        # Clear previous display
        for widget in table_display_frame.winfo_children():
            widget.destroy()

        query = f"SELECT * FROM {table_name}"
        c.execute(query)
        rows = c.fetchall()
        columns = [col[0] for col in c.description]

        # Create a canvas for scrolling
        canvas = tk.Canvas(table_display_frame)
        scrollbar = ttk.Scrollbar(table_display_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Grid layout configuration
        max_columns = 4  # Number of cards per row

        for idx, row in enumerate(rows):
            card_frame = tk.Frame(scrollable_frame, bd=2, relief=tk.RAISED, padx=10, pady=10)
            row_pos = idx // max_columns
            col_pos = idx % max_columns

            card_frame.grid(row=row_pos, column=col_pos, padx=15, pady=10, sticky="n")

            # Add key-value pairs inside the card
            for key, value in zip(columns, row):
                key_value_frame = tk.Frame(card_frame)
                key_value_frame.pack(anchor="w", pady=1)

                # Display key
                key_label = tk.Label(key_value_frame, text=f"{key}:", font=("Arial", 10, "bold"))
                key_label.pack(side=tk.LEFT)

                # Display value
                value_label = tk.Label(key_value_frame, text=value, font=("Arial", 10))
                value_label.pack(side=tk.LEFT)

        canvas.update_idletasks()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch table data: {e}")

# Function to fetch and display payment details for each customer in a grid layout
def display_payment_details():
    """Fetch and display payment details for each customer in a grid layout."""
    try:
        # Clear previous display
        for widget in table_display_frame.winfo_children():
            widget.destroy()

        query = """
        SELECT C.Customer_id, C.Name, P.Payment_no, P.Payment_amount, TO_CHAR(P.Payment_date, 'YYYY-MM-DD'), O.Order_id
        FROM CUSTOMER C
        JOIN ORDERS O ON C.Customer_id = O.Customer_id
        JOIN PAYMENT P ON O.Order_id = P.Order_id
        ORDER BY P.Payment_date DESC
        """
        c.execute(query)
        rows = c.fetchall()

        if not rows:
            messagebox.showinfo("No Data", "No payment records to display.")
            return

        # Create a canvas for scrolling
        canvas = tk.Canvas(table_display_frame)
        scrollbar = ttk.Scrollbar(table_display_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Display payment details in a grid
        headers = ["Customer ID", "Customer Name", "Payment No", "Payment Amount", "Payment Date", "Order ID"]
        for col_num, header in enumerate(headers):
            header_label = tk.Label(
                scrollable_frame, text=header, font=("Arial", 10, "bold")
            )
            header_label.grid(row=0, column=col_num, padx=5, pady=2)

        for row_num, row_data in enumerate(rows, start=1):
            for col_num, value in enumerate(row_data):
                value_label = tk.Label(
                    scrollable_frame, text=value, font=("Arial", 10)
                )
                value_label.grid(row=row_num, column=col_num, padx=5, pady=2)

        canvas.update_idletasks()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch payment details: {e}")

def display_products():
    """Fetches and displays products with images in a grid view."""
    try:
        # Clear previous display
        for widget in table_display_frame.winfo_children():
            widget.destroy()

        # Fetch product data
        query = """
        SELECT P.Product_id, P.Product_name, P.Product_price, P.Image_path
        FROM PRODUCT P
        """
        c.execute(query)
        products = c.fetchall()

        if not products:
            messagebox.showinfo("No Data", "No products to display.")
            return

        # Create scrollable canvas for display
        canvas = tk.Canvas(table_display_frame)
        scrollbar = ttk.Scrollbar(table_display_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Grid layout configuration
        max_columns = 7  # Number of products per row
        row_index = 0
        col_index = 0

        for product in products:
            product_id, product_name, product_price, image_path = product

            # Load product image
            try:
                with Image.open(image_path) as image:
                    image = image.resize((100, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
                continue

            # Create a label to display the image
            product_label = tk.Label(scrollable_frame, image=photo)
            product_label.image = photo  # Keep a reference to the image
            product_label.grid(row=row_index, column=col_index, padx=10, pady=10)

            # Bind click event to show product details
            product_label.bind("<Button-1>", lambda event, pid=product_id, pname=product_name, pprice=product_price: show_product_details(pid, pname, pprice))

            # Update column and row indices
            col_index += 1
            if col_index >= max_columns:
                col_index = 0
                row_index += 1

        canvas.update_idletasks()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch products: {e}")
# Function to show product details in a Toplevel window
def show_product_details(product_id, product_name, product_price):
    """Show product details in a Toplevel window."""
    details_window = tk.Toplevel()
    details_window.title("Product Details")

    tk.Label(details_window, text=f"Product ID: {product_id}", font=("Arial", 12, "bold")).pack(pady=5)
    tk.Label(details_window, text=f"Product Name: {product_name}", font=("Arial", 12, "bold")).pack(pady=5)
    tk.Label(details_window, text=f"Product Price: {product_price}", font=("Arial", 12, "bold")).pack(pady=5)

    details_window.transient(table_display_frame)
    details_window.grab_set()
    details_window.wait_window()

# Function to display the main dashboard window after successful login
def show_dashboard_window():
    login_window.destroy()

    dashboard_window = tk.Tk()
    dashboard_window.title("Admin Dashboard")
    dashboard_window.state('zoomed')  # Fullscreen window

    left_frame = tk.Frame(dashboard_window)
    left_frame.pack(side=tk.LEFT, fill=tk.Y)

    right_frame = tk.Frame(dashboard_window)
    right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

    global table_display_frame
    table_display_frame = right_frame
    stats_button = tk.Button(left_frame, text="Stats", font=("Arial", 12), command=show_stats)
    stats_button.pack(fill=tk.X, padx=10, pady=5)

    table_names = ["ORDERS", "CUSTOMER", "PRODUCT_CATEGORY", "SUPPLIER"]

    for table_name in table_names:
        button = tk.Button(
            left_frame, text=table_name.capitalize(), font=("Arial", 12),
            command=lambda tn=table_name: fetch_table_data(tn)
        )
        button.pack(fill=tk.X, padx=10, pady=5)

    display_button = tk.Button(left_frame, text="Display", font=("Arial", 12), command=display_customer_products)
    display_button.pack(fill=tk.X, padx=10, pady=5)
    payment_button = tk.Button(left_frame, text="Payment", font=("Arial", 12), command=display_payment_details)
    payment_button.pack(fill=tk.X, padx=10, pady=5)

    products_button = tk.Button(left_frame, text="Products", font=("Arial", 12), command=display_products)
    products_button.pack(fill=tk.X, padx=10, pady=5)

    dashboard_window.mainloop()

# Function to handle login validation
def handle_login():
    admin_name = admin_name_entry.get()
    admin_password = admin_password_entry.get()

    if admin_name and admin_password == "123":
        show_dashboard_window()
    else:
        messagebox.showerror("Login Failed", "Invalid credentials! Try again.")

# --- Login Window ---
login_window = tk.Tk()
login_window.title("Admin Login")

tk.Label(login_window, text="Admin Name:").grid(row=0, column=0, padx=10, pady=5)
admin_name_entry = tk.Entry(login_window)
admin_name_entry.grid(row=0, column=1)

tk.Label(login_window, text="Password:").grid(row=1, column=0, padx=10, pady=5)
admin_password_entry = tk.Entry(login_window, show="*")
admin_password_entry.grid(row=1, column=1)

login_button = tk.Button(login_window, text="Login", command=handle_login)
login_button.grid(row=2, column=0, columnspan=2, pady=10)

login_window.mainloop()