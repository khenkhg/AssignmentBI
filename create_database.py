import sqlite3

connection = sqlite3.connect("ventes.db")
cursor = connection.cursor()

# 1. CUSTOMERS TABLE
cursor.execute("""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    region TEXT NOT NULL
)
""")

# 2. PRODUCTS TABLE
cursor.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    base_price_5kg REAL NOT NULL,
    extra_price_per_kg REAL NOT NULL
)
""")

# 3. SALES TABLE
cursor.execute("""
CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    weight REAL NOT NULL,
    destination TEXT NOT NULL,
    receiver_phone TEXT NOT NULL,
    delivery_status TEXT NOT NULL,
    sale_date TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")

connection.commit()
connection.close()
print("Database created successfully!")