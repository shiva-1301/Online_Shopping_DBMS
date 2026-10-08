"""Online Shopping DBMS - admin dashboard (Tkinter).

Run:  python app.py      (run `python db_setup.py` once first)
"""
import hmac
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import font as tkfont
from tkinter import messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, ImageTk

import database

# --- Design tokens -----------------------------------------------------------
COLORS = {
    "bg": "#F4F5FA",
    "surface": "#FFFFFF",
    "sidebar": "#1E1B4B",
    "sidebar_hover": "#312E81",
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "text": "#111827",
    "muted": "#6B7280",
    "on_dark": "#E0E7FF",
    "border": "#E5E7EB",
    "stripe": "#F9FAFB",
    "danger": "#DC2626",
}
CHART_COLORS = ["#4F46E5", "#0EA5E9", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#14B8A6", "#64748B"]
MAX_LOGIN_ATTEMPTS = 5

# Only these tables may be opened from the sidebar (prevents SQL injection via table names)
TABLE_PAGES = {
    "ORDERS": "Orders",
    "CUSTOMER": "Customers",
    "PRODUCT_CATEGORY": "Categories",
    "SUPPLIER": "Suppliers",
}


def pick_font_family(root):
    available = set(tkfont.families(root))
    for family in ("Segoe UI", "Inter", "Helvetica Neue", "Helvetica", "Arial"):
        if family in available:
            return family
    return "TkDefaultFont"


def fmt_money(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


class ScrollFrame(ttk.Frame):
    """A vertically scrollable frame with mouse-wheel support."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, style="Page.TFrame")
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._window, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


class ShopAdminApp:
    def __init__(self, root):
        self.root = root
        self.conn = None
        self.cursor = None
        self.login_attempts = 0
        self.nav_buttons = {}
        self.image_cache = []
        self.chart_figures = []

        root.title("ShopEase Admin · Online Shopping DBMS")
        root.geometry("1200x760")
        root.minsize(720, 520)
        root.configure(bg=COLORS["bg"])
        self.family = pick_font_family(root)
        self._init_styles()
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.show_login()

    # --- Styling ---------------------------------------------------------------
    def font(self, size=10, weight="normal"):
        return (self.family, size, weight)

    def _init_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        c = COLORS
        style.configure(".", font=self.font(10), background=c["bg"], foreground=c["text"])
        style.configure("Page.TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["surface"], relief="flat")
        style.configure("Sidebar.TFrame", background=c["sidebar"])
        style.configure("TLabel", background=c["bg"], foreground=c["text"])
        style.configure("Card.TLabel", background=c["surface"])
        style.configure("Muted.TLabel", background=c["bg"], foreground=c["muted"])
        style.configure("CardMuted.TLabel", background=c["surface"], foreground=c["muted"], font=self.font(9))
        style.configure("H1.TLabel", font=self.font(20, "bold"))
        style.configure("CardH1.TLabel", background=c["surface"], font=self.font(20, "bold"))
        style.configure("CardH2.TLabel", background=c["surface"], font=self.font(12, "bold"))
        style.configure("KPI.TLabel", background=c["surface"], font=self.font(18, "bold"), foreground=c["primary"])
        style.configure("Error.TLabel", background=c["surface"], foreground=c["danger"], font=self.font(9))
        style.configure("Footer.TLabel", background=c["surface"], foreground=c["muted"], font=self.font(9))

        style.configure("Primary.TButton", background=c["primary"], foreground="white", borderwidth=0,
                        focusthickness=2, focuscolor=c["on_dark"], padding=(16, 9), font=self.font(10, "bold"))
        style.map("Primary.TButton", background=[("pressed", c["sidebar"]), ("active", c["primary_hover"])])
        style.configure("Ghost.TButton", background=c["surface"], foreground=c["primary"], borderwidth=1,
                        bordercolor=c["border"], padding=(12, 6))
        style.map("Ghost.TButton", background=[("active", "#EEF2FF")])

        style.configure("TEntry", fieldbackground=c["surface"], bordercolor=c["border"], padding=8)
        style.map("TEntry", bordercolor=[("focus", c["primary"])], lightcolor=[("focus", c["primary"])])

        style.configure("Treeview", background=c["surface"], fieldbackground=c["surface"], rowheight=30,
                        bordercolor=c["border"], borderwidth=0, font=self.font(10))
        style.configure("Treeview.Heading", background="#EEF2FF", foreground=c["text"], relief="flat",
                        font=self.font(10, "bold"), padding=(8, 6))
        style.map("Treeview.Heading", background=[("active", "#E0E7FF")])
        style.map("Treeview", background=[("selected", c["primary"])], foreground=[("selected", "white")])

    # --- Login -------------------------------------------------------------------
    def show_login(self):
        self._clear_root()
        page = ttk.Frame(self.root, style="Page.TFrame")
        page.pack(fill="both", expand=True)

        card = ttk.Frame(page, style="Card.TFrame", padding=36)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(card, text="🛒 ShopEase Admin", style="CardH1.TLabel").pack(anchor="w")
        ttk.Label(card, text="Sign in to manage products, orders and payments.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(4, 20))

        ttk.Label(card, text="Admin name", style="Card.TLabel").pack(anchor="w")
        self.name_entry = ttk.Entry(card, width=34)
        self.name_entry.pack(fill="x", pady=(4, 12))

        ttk.Label(card, text="Password", style="Card.TLabel").pack(anchor="w")
        self.password_entry = ttk.Entry(card, width=34, show="•")
        self.password_entry.pack(fill="x", pady=(4, 6))

        self.login_error = ttk.Label(card, text="", style="Error.TLabel")
        self.login_error.pack(anchor="w", pady=(0, 10))

        self.login_button = ttk.Button(card, text="Sign in", style="Primary.TButton", command=self.handle_login)
        self.login_button.pack(fill="x")

        backend = "SQLite demo database" if database.DB_BACKEND != "oracle" else "Oracle database"
        ttk.Label(card, text=f"Database: {backend}", style="CardMuted.TLabel").pack(pady=(16, 0))

        self.root.bind("<Return>", lambda e: self.handle_login())
        self.name_entry.focus_set()

    def handle_login(self):
        name = self.name_entry.get().strip()
        password = self.password_entry.get()

        if self.login_attempts >= MAX_LOGIN_ATTEMPTS:
            self.login_error.config(text="Too many failed attempts. Restart the app to try again.")
            return
        if not name or not password:
            self.login_error.config(text="Please enter both admin name and password.")
            return
        if not database.ADMIN_PASSWORD:
            self.login_error.config(text="ADMIN_PASSWORD is not set. Add it to your .env file.")
            return
        if not hmac.compare_digest(password.encode(), database.ADMIN_PASSWORD.encode()):
            self.login_attempts += 1
            remaining = MAX_LOGIN_ATTEMPTS - self.login_attempts
            self.login_error.config(text=f"Invalid credentials. {remaining} attempt(s) left.")
            self.password_entry.delete(0, "end")
            return

        try:
            self.conn = database.connect()
            self.cursor = self.conn.cursor()
        except Exception as e:
            self.login_error.config(text="Could not connect to the database.")
            messagebox.showerror("Database Error", f"Failed to connect to the database:\n{e}")
            return

        self.root.unbind("<Return>")
        self.admin_name = name
        self.show_dashboard()

    # --- Dashboard shell ---------------------------------------------------------
    def show_dashboard(self):
        self._clear_root()
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        sidebar = tk.Frame(self.root, bg=COLORS["sidebar"], width=220)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")
        sidebar.grid_propagate(False)
        tk.Label(sidebar, text="🛒 ShopEase", bg=COLORS["sidebar"], fg="white",
                 font=self.font(16, "bold")).pack(anchor="w", padx=20, pady=(22, 2))
        tk.Label(sidebar, text="Admin dashboard", bg=COLORS["sidebar"], fg=COLORS["on_dark"],
                 font=self.font(9)).pack(anchor="w", padx=20, pady=(0, 18))

        pages = [
            ("overview", "Overview", self.page_overview),
            ("stats", "Sales stats", self.page_stats),
            ("products", "Products", self.page_products),
            ("customer_orders", "Customer orders", self.page_customer_orders),
            ("payments", "Payments", self.page_payments),
        ] + [(t, label, (lambda tn=t: self.page_table(tn))) for t, label in TABLE_PAGES.items()]

        for key, label, handler in pages:
            self._nav_button(sidebar, key, label, handler)

        logout = self._nav_button(sidebar, "logout", "Log out  →", self.logout)
        logout.pack_forget()
        logout.pack(side="bottom", fill="x", pady=(0, 16))

        main = ttk.Frame(self.root, style="Page.TFrame")
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        header = ttk.Frame(main, style="Page.TFrame", padding=(28, 22, 28, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(header, text="", style="H1.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label = ttk.Label(header, text="", style="Muted.TLabel")
        self.subtitle_label.grid(row=1, column=0, sticky="w")
        ttk.Button(header, text="⟳ Refresh", style="Ghost.TButton",
                   command=lambda: self.current_page and self.current_page()).grid(row=0, column=1, rowspan=2)

        self.content = ttk.Frame(main, style="Page.TFrame", padding=(28, 8, 28, 16))
        self.content.grid(row=1, column=0, sticky="nsew")

        footer = ttk.Frame(self.root, style="Card.TFrame", padding=(28, 6))
        footer.grid(row=1, column=1, sticky="ew")
        self.status_label = ttk.Label(footer, text="Ready", style="Footer.TLabel")
        self.status_label.pack(side="left")
        backend = "Oracle" if database.DB_BACKEND == "oracle" else "SQLite demo"
        ttk.Label(footer, text=f"Signed in as {self.admin_name} · {backend}",
                  style="Footer.TLabel").pack(side="right")

        self.current_page = None
        self.navigate("overview", self.page_overview)

    def _nav_button(self, parent, key, label, handler):
        btn = tk.Label(parent, text=label, bg=COLORS["sidebar"], fg=COLORS["on_dark"], anchor="w",
                       font=self.font(10), padx=20, pady=9, cursor="hand2")
        btn.pack(fill="x")
        btn.bind("<Button-1>", lambda e: self.navigate(key, handler) if key != "logout" else handler())
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["sidebar_hover"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["primary"] if self._active == key else COLORS["sidebar"]))
        self.nav_buttons[key] = btn
        return btn

    _active = None

    def navigate(self, key, handler):
        self._active = key
        for k, btn in self.nav_buttons.items():
            active = k == key
            btn.config(bg=COLORS["primary"] if active else COLORS["sidebar"],
                       fg="white" if active else COLORS["on_dark"])
        self.current_page = handler
        handler()

    def set_header(self, title, subtitle=""):
        self.title_label.config(text=title)
        self.subtitle_label.config(text=subtitle)

    def begin_page(self, title, subtitle=""):
        """Clear the content area and show a loading state."""
        for widget in self.content.winfo_children():
            widget.destroy()
        for fig in self.chart_figures:
            fig.clf()
        self.chart_figures.clear()
        self.image_cache.clear()
        self.set_header(title, subtitle)
        self.status_label.config(text="Loading…")
        self.root.config(cursor="watch")
        self.root.update_idletasks()

    def end_page(self, status):
        self.status_label.config(text=status)
        self.root.config(cursor="")

    def run_query(self, sql, params=None):
        try:
            return database.query(self.cursor, sql, params)
        except Exception as e:
            self.end_page("Query failed")
            messagebox.showerror("Database Error", f"Query failed:\n{e}")
            return None, None

    def empty_state(self, parent, message, bg=COLORS["bg"]):
        tk.Label(parent, text=f"🗃️\n\n{message}", bg=bg, fg=COLORS["muted"],
                 font=self.font(11), justify="center").pack(expand=True, pady=60)

    # --- Reusable table view -------------------------------------------------------
    def build_table(self, parent, columns, rows, money_cols=(), tree_groups=None):
        """Searchable, striped Treeview. tree_groups = {parent_label: [row, ...]} for grouped data."""
        wrapper = ttk.Frame(parent, style="Page.TFrame")
        wrapper.pack(fill="both", expand=True)

        search_bar = ttk.Frame(wrapper, style="Page.TFrame")
        search_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(search_bar, text="🔍 Search", style="Muted.TLabel").pack(side="left", padx=(0, 8))
        query_var = tk.StringVar()
        search = ttk.Entry(search_bar, textvariable=query_var, width=40)
        search.pack(side="left", fill="x", expand=False)
        count_label = ttk.Label(search_bar, text="", style="Muted.TLabel")
        count_label.pack(side="right")

        card = ttk.Frame(wrapper, style="Card.TFrame", padding=1)
        card.pack(fill="both", expand=True)
        card.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)

        show = "tree headings" if tree_groups is not None else "headings"
        tree = ttk.Treeview(card, columns=columns, show=show, selectmode="browse")
        if tree_groups is not None:
            tree.heading("#0", text="Customer")
            tree.column("#0", width=200, stretch=True)
        vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(card, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree.tag_configure("odd", background=COLORS["stripe"])
        tree.tag_configure("group", font=self.font(10, "bold"), background="#EEF2FF")

        measure = tkfont.Font(family=self.family, size=10)
        all_rows = rows if tree_groups is None else [r for g in tree_groups.values() for r in g]
        for idx, col in enumerate(columns):
            label = col.replace("_", " ").title()
            tree.heading(col, text=label, command=lambda c=col: sort_by(c, False))
            widest = max([measure.measure(label) + 30] + [measure.measure(str(r[idx])) + 24 for r in all_rows[:200]])
            numeric = col in money_cols or all(isinstance(r[idx], (int, float)) for r in all_rows if r[idx] is not None)
            tree.column(col, width=min(max(widest, 90), 320), anchor="e" if numeric and all_rows else "w")

        def display(value, col):
            if value is None:
                return "—"
            return fmt_money(value) if col in money_cols else value

        def populate(text=""):
            tree.delete(*tree.get_children())
            text = text.lower().strip()
            match = lambda r: not text or any(text in str(v).lower() for v in r)
            shown = 0
            if tree_groups is None:
                for i, r in enumerate(filter(match, rows)):
                    tree.insert("", "end", values=[display(v, c) for v, c in zip(r, columns)],
                                tags=("odd",) if i % 2 else ())
                    shown += 1
            else:
                for group, group_rows in tree_groups.items():
                    matching = [r for r in group_rows if match(r) or text in group.lower()]
                    if not matching:
                        continue
                    node = tree.insert("", "end", text=group, open=True, tags=("group",))
                    for i, r in enumerate(matching):
                        tree.insert(node, "end", values=[display(v, c) for v, c in zip(r, columns)],
                                    tags=("odd",) if i % 2 else ())
                    shown += len(matching)
            count_label.config(text=f"{shown} of {len(all_rows)} records")

        def sort_by(col, descending):
            idx = columns.index(col)
            key = lambda r: (r[idx] is None, r[idx] if isinstance(r[idx], (int, float)) else str(r[idx]).lower())
            rows.sort(key=key, reverse=descending)
            if tree_groups is not None:
                for g in tree_groups.values():
                    g.sort(key=key, reverse=descending)
            populate(query_var.get())
            tree.heading(col, command=lambda: sort_by(col, not descending))

        query_var.trace_add("write", lambda *a: populate(query_var.get()))
        populate()
        return tree

    # --- Pages -----------------------------------------------------------------------
    def page_overview(self):
        self.begin_page("Overview", "A quick snapshot of your store.")
        kpis = [
            ("Total revenue", "SELECT COALESCE(SUM(Order_amount), 0) FROM ORDERS", True),
            ("Orders", "SELECT COUNT(*) FROM ORDERS", False),
            ("Customers", "SELECT COUNT(*) FROM CUSTOMER", False),
            ("Products", "SELECT COUNT(*) FROM PRODUCT", False),
        ]
        grid = ttk.Frame(self.content, style="Page.TFrame")
        grid.pack(fill="x")
        for i, (label, sql, money) in enumerate(kpis):
            _, rows = self.run_query(sql)
            if rows is None:
                return
            value = rows[0][0] or 0
            grid.columnconfigure(i, weight=1, uniform="kpi")
            card = ttk.Frame(grid, style="Card.TFrame", padding=(20, 16))
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            ttk.Label(card, text=label.upper(), style="CardMuted.TLabel").pack(anchor="w")
            ttk.Label(card, text=fmt_money(value) if money else f"{int(value):,}", style="KPI.TLabel").pack(anchor="w", pady=(6, 0))

        ttk.Label(self.content, text="Recent orders", style="H1.TLabel",
                  font=self.font(13, "bold")).pack(anchor="w", pady=(24, 10))
        columns, rows = self.run_query("""
            SELECT O.Order_id, C.Name AS Customer, TO_CHAR(O.Order_Date, 'YYYY-MM-DD') AS Order_date, O.Order_amount
            FROM ORDERS O JOIN CUSTOMER C ON C.Customer_id = O.Customer_id
            ORDER BY O.Order_Date DESC
            FETCH FIRST 8 ROWS ONLY""")
        if rows is None:
            return
        columns = [c.upper() for c in columns]
        if not rows:
            self.empty_state(self.content, "No orders yet.")
        else:
            self.build_table(self.content, columns, rows, money_cols={"ORDER_AMOUNT"})
        self.end_page("Overview loaded")

    def page_table(self, table_name):
        if table_name not in TABLE_PAGES:
            messagebox.showerror("Error", f"Unknown table: {table_name}")
            return
        self.begin_page(TABLE_PAGES[table_name], f"All records in the {table_name} table. Click a column to sort.")
        columns, rows = self.run_query(f"SELECT * FROM {table_name}")
        if rows is None:
            return
        columns = [c.upper() for c in columns]
        if not rows:
            self.empty_state(self.content, "No records to display.")
        else:
            money = {c for c in columns if "AMOUNT" in c or "PRICE" in c}
            self.build_table(self.content, columns, rows, money_cols=money)
        self.end_page(f"{len(rows)} records loaded from {table_name}")

    def page_customer_orders(self):
        self.begin_page("Customer orders", "Products bought by each customer.")
        _, rows = self.run_query("""
            SELECT C.Name AS Customer_Name, C.Customer_id, O.Order_id, P.Product_name, P.Product_price, OD.Quantity
            FROM CUSTOMER C
            JOIN ORDERS O ON C.Customer_id = O.Customer_id
            JOIN ORDER_DETAILS OD ON O.Order_id = OD.Order_id
            JOIN PRODUCT P ON OD.Product_id = P.Product_id
            ORDER BY C.Customer_id""")
        if rows is None:
            return
        if not rows:
            self.empty_state(self.content, "No customer orders to display.")
            self.end_page("No records")
            return
        groups = {}
        for name, cid, *details in rows:
            groups.setdefault(f"{name} ({cid})", []).append(tuple(details))
        flat = [r for g in groups.values() for r in g]
        self.build_table(self.content, ["ORDER_ID", "PRODUCT", "PRICE", "QUANTITY"], flat,
                         money_cols={"PRICE"}, tree_groups=groups)
        self.end_page(f"{len(groups)} customers · {len(rows)} line items")

    def page_payments(self):
        self.begin_page("Payments", "Payment history for every customer, newest first.")
        columns, rows = self.run_query("""
            SELECT C.Customer_id, C.Name AS Customer_name, P.Payment_no, P.Payment_amount,
                   TO_CHAR(P.Payment_date, 'YYYY-MM-DD') AS Payment_date, O.Order_id
            FROM CUSTOMER C
            JOIN ORDERS O ON C.Customer_id = O.Customer_id
            JOIN PAYMENT P ON O.Order_id = P.Order_id
            ORDER BY P.Payment_date DESC""")
        if rows is None:
            return
        columns = [c.upper() for c in columns]
        if not rows:
            self.empty_state(self.content, "No payment records to display.")
        else:
            self.build_table(self.content, columns, rows, money_cols={"PAYMENT_AMOUNT"})
        self.end_page(f"{len(rows)} payments")

    def page_products(self):
        self.begin_page("Products", "Click a product to see its details.")
        _, products = self.run_query("""
            SELECT P.Product_id, P.Product_name, P.Product_price, P.Image_path, P.Product_status, C.Category_name
            FROM PRODUCT P LEFT JOIN PRODUCT_CATEGORY C ON C.Category_id = P.Category_id
            ORDER BY P.Product_id""")
        if products is None:
            return
        if not products:
            self.empty_state(self.content, "No products to display.")
            self.end_page("No products")
            return

        scroller = ScrollFrame(self.content, style="Page.TFrame")
        scroller.pack(fill="both", expand=True)
        cards = [self._product_card(scroller.inner, p) for p in products]

        card_width = 200
        state = {"cols": 0}

        def relayout(event=None):
            width = scroller.canvas.winfo_width()
            cols = max(1, width // (card_width + 16))
            if cols == state["cols"]:
                return
            state["cols"] = cols
            for i in range(12):
                scroller.inner.columnconfigure(i, weight=1 if i < cols else 0, uniform="card" if i < cols else "")
            for i, card in enumerate(cards):
                card.grid(row=i // cols, column=i % cols, padx=8, pady=8, sticky="nsew")

        scroller.canvas.bind("<Configure>", lambda e: (
            scroller.canvas.itemconfigure(scroller._window, width=e.width), relayout()), add="+")
        self.root.after(50, relayout)
        self.end_page(f"{len(products)} products")

    def _load_image(self, path, size):
        try:
            full = database.BASE_DIR / path if path else None
            with Image.open(full) as img:
                img = img.convert("RGB")
                img.thumbnail(size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", size, "white")
                canvas.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
                photo = ImageTk.PhotoImage(canvas)
        except Exception:
            placeholder = Image.new("RGB", size, "#E5E7EB")
            photo = ImageTk.PhotoImage(placeholder)
        self.image_cache.append(photo)  # keep a reference so Tk doesn't garbage-collect it
        return photo

    def _product_card(self, parent, product):
        pid, name, price, image_path, status, category = product
        card = tk.Frame(parent, bg=COLORS["surface"], highlightthickness=1,
                        highlightbackground=COLORS["border"], cursor="hand2")
        photo = self._load_image(image_path, (160, 140))
        widgets = [
            tk.Label(card, image=photo, bg=COLORS["surface"]),
            tk.Label(card, text=category or "Uncategorised", bg=COLORS["surface"], fg=COLORS["muted"], font=self.font(8)),
            tk.Label(card, text=name, bg=COLORS["surface"], fg=COLORS["text"], font=self.font(10, "bold"),
                     wraplength=170, justify="center"),
            tk.Label(card, text=fmt_money(price), bg=COLORS["surface"], fg=COLORS["primary"], font=self.font(11, "bold")),
        ]
        for i, w in enumerate(widgets):
            w.pack(padx=12, pady=(12 if i == 0 else 2, 12 if i == len(widgets) - 1 else 0))

        def on_enter(e):
            card.config(highlightbackground=COLORS["primary"], highlightthickness=2)

        def on_leave(e):
            card.config(highlightbackground=COLORS["border"], highlightthickness=1)

        for w in [card] + widgets:
            w.bind("<Button-1>", lambda e: self.show_product_details(product))
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
        return card

    def show_product_details(self, product):
        pid, name, price, image_path, status, category = product
        win = tk.Toplevel(self.root)
        win.title(name)
        win.configure(bg=COLORS["surface"])
        win.resizable(False, False)
        win.transient(self.root)
        photo = self._load_image(image_path, (280, 240))
        tk.Label(win, image=photo, bg=COLORS["surface"]).pack(padx=24, pady=(24, 12))
        tk.Label(win, text=name, bg=COLORS["surface"], font=self.font(14, "bold")).pack(padx=24)
        tk.Label(win, text=fmt_money(price), bg=COLORS["surface"], fg=COLORS["primary"],
                 font=self.font(13, "bold")).pack(pady=(4, 8))
        for label, value in (("Product ID", pid), ("Category", category or "—"), ("Status", status or "—")):
            row = tk.Frame(win, bg=COLORS["surface"])
            row.pack(fill="x", padx=24)
            tk.Label(row, text=label, bg=COLORS["surface"], fg=COLORS["muted"], font=self.font(10)).pack(side="left")
            tk.Label(row, text=value, bg=COLORS["surface"], font=self.font(10, "bold")).pack(side="right")
        ttk.Button(win, text="Close", style="Primary.TButton", command=win.destroy).pack(fill="x", padx=24, pady=20)
        win.bind("<Escape>", lambda e: win.destroy())
        win.grab_set()
        win.focus_set()

    def page_stats(self):
        self.begin_page("Sales stats", "Sales performance across products, dates and categories.")
        last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        charts = [
            ("Product sales quantity", "bar", """
                SELECT P.Product_name, SUM(OD.Quantity)
                FROM PRODUCT P JOIN ORDER_DETAILS OD ON P.Product_id = OD.Product_id
                GROUP BY P.Product_name ORDER BY SUM(OD.Quantity) DESC""", None),
            ("Top 5 best-selling products", "barh", """
                SELECT P.Product_name, SUM(OD.Quantity)
                FROM PRODUCT P JOIN ORDER_DETAILS OD ON P.Product_id = OD.Product_id
                GROUP BY P.Product_name ORDER BY SUM(OD.Quantity) DESC
                FETCH FIRST 5 ROWS ONLY""", None),
            ("Sales in the last 7 days", "line", """
                SELECT TO_CHAR(O.Order_Date, 'YYYY-MM-DD') AS Order_Date, SUM(O.Order_amount)
                FROM ORDERS O
                WHERE O.Order_Date >= TO_DATE(:last_week_date, 'YYYY-MM-DD')
                GROUP BY TO_CHAR(O.Order_Date, 'YYYY-MM-DD')
                ORDER BY TO_CHAR(O.Order_Date, 'YYYY-MM-DD')""", {"last_week_date": last_week}),
            ("Daily sales trend", "line", """
                SELECT TO_CHAR(O.Order_Date, 'YYYY-MM-DD') AS Order_Date, SUM(O.Order_amount)
                FROM ORDERS O
                GROUP BY TO_CHAR(O.Order_Date, 'YYYY-MM-DD')
                ORDER BY TO_CHAR(O.Order_Date, 'YYYY-MM-DD')""", None),
            # Fixed: the original queried a non-existent CATEGORY table and summed whole
            # order amounts once per line item (double counting multi-item orders).
            ("Revenue by category", "pie", """
                SELECT C.Category_name, SUM(P.Product_price * OD.Quantity)
                FROM PRODUCT_CATEGORY C
                JOIN PRODUCT P ON C.Category_id = P.Category_id
                JOIN ORDER_DETAILS OD ON P.Product_id = OD.Product_id
                GROUP BY C.Category_name""", None),
        ]

        scroller = ScrollFrame(self.content, style="Page.TFrame")
        scroller.pack(fill="both", expand=True)
        grid = scroller.inner
        grid.columnconfigure(0, weight=1, uniform="chart")
        grid.columnconfigure(1, weight=1, uniform="chart")

        cards = []
        for title, kind, sql, params in charts:
            _, rows = self.run_query(sql, params)
            if rows is None:
                return
            card = ttk.Frame(grid, style="Card.TFrame", padding=12)
            ttk.Label(card, text=title, style="CardH2.TLabel").pack(anchor="w")
            if not rows:
                self.empty_state(card, "No data for this chart yet.", bg=COLORS["surface"])
            else:
                self._draw_chart(card, kind, [r[0] for r in rows], [float(r[1] or 0) for r in rows])
            cards.append(card)

        state = {"cols": 0}

        def relayout(event=None):
            cols = 2 if scroller.canvas.winfo_width() >= 900 else 1
            if cols == state["cols"]:
                return
            state["cols"] = cols
            grid.columnconfigure(1, weight=1 if cols == 2 else 0, uniform="chart" if cols == 2 else "")
            for i, card in enumerate(cards):
                card.grid(row=i // cols, column=i % cols, sticky="nsew", padx=6, pady=6)

        scroller.canvas.bind("<Configure>", lambda e: (
            scroller.canvas.itemconfigure(scroller._window, width=e.width), relayout()), add="+")
        self.root.after(50, relayout)
        self.end_page("Charts generated")

    def _draw_chart(self, parent, kind, labels, values):
        labels = [str(l) if len(str(l)) <= 18 else str(l)[:17] + "…" for l in labels]
        fig = Figure(figsize=(5.4, 3.2), dpi=96, facecolor=COLORS["surface"])
        self.chart_figures.append(fig)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLORS["surface"])
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(COLORS["border"])
        ax.tick_params(colors=COLORS["muted"], labelsize=8)

        if kind == "bar":
            ax.bar(labels, values, color=COLORS["primary"])
            ax.tick_params(axis="x", labelrotation=35)
            for t in ax.get_xticklabels():
                t.set_ha("right")
            ax.set_ylabel("Quantity sold", color=COLORS["muted"], fontsize=8)
        elif kind == "barh":
            ax.barh(labels[::-1], values[::-1], color=CHART_COLORS[1])
            ax.set_xlabel("Quantity sold", color=COLORS["muted"], fontsize=8)
        elif kind == "line":
            short = [l[5:] for l in labels]  # MM-DD keeps the axis readable
            ax.plot(short, values, marker="o", color=COLORS["primary"], linewidth=2)
            ax.fill_between(range(len(values)), values, alpha=0.08, color=COLORS["primary"])
            ax.grid(axis="y", color=COLORS["border"])
            ax.set_ylabel("Sales (₹)", color=COLORS["muted"], fontsize=8)
        elif kind == "pie":
            ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90, colors=CHART_COLORS,
                   wedgeprops={"linewidth": 2, "edgecolor": "white"}, textprops={"fontsize": 8})
            ax.axis("equal")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, pady=(6, 0))

    # --- Session ---------------------------------------------------------------------
    def logout(self):
        if not messagebox.askyesno("Log out", "Are you sure you want to log out?"):
            return
        self._close_connection()
        self.login_attempts = 0
        self.root.columnconfigure(1, weight=0)
        self.show_login()

    def _close_connection(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.conn = self.cursor = None

    def _clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.nav_buttons.clear()

    def on_close(self):
        self._close_connection()
        self.root.destroy()


def enable_high_dpi():
    """Render crisply on high-DPI Windows displays instead of a blurry bitmap-scaled window."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass  # not Windows, or not supported


def main():
    enable_high_dpi()
    root = tk.Tk()
    ShopAdminApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
