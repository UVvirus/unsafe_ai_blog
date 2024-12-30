import sqlite3
import hashlib
import os

class ProductDatabase:
    def __init__(self):
        self.db_name='product_store.db'
        self.connection=sqlite3.connect(self.db_name)
        self.cursor=self.connection.cursor()
        self.db_exists= os.path.exists(self.db_name)
        if not self.db_exists:
            self.create_tables()
    
    def create_tables(self):
        try:
            self.product_info_table()
            self.user_info_table()
            self.purchase_history_table()
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
    def product_info_table(self):
        # product_info table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            url TEXT,
            price REAL,
            category TEXT,
            description TEXT)  ''')
        
    
    def user_info_table(self):
        # users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP) ''')
    
    def purchase_history_table(self):
        # purchase history table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_history (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            quantity INTEGER,
            total_price REAL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        ''')

    def table_exists(self, table_name):
        """Check if a table exists"""
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?;
        """, (table_name,))
    
    
    def insert_dummy_data(self):
        try:
            # Verify tables exist before inserting
            if not all(self.table_exists(table) for table in ['users', 'products', 'purchase_history']):
                print("Tables don't exist. Creating tables first...")
                self.create_tables()
            users = [
                ("admin", hashlib.sha256("admin".encode()).hexdigest(), "admin@admin.com"),
                ("uv", hashlib.sha256("P@$$w0rd@123".encode()).hexdigest(), "uv@virus.com"),
                ("test_user", hashlib.sha256("Dec@2024".encode()).hexdigest(), "testuser@gmail.com")
            ]

            self.cursor.executemany('''INSERT INTO users (username, password, email) VALUES (?, ?, ?)''', users)

            product_info= [
                ("Laptop", "https://example.com/laptop", 999.99, "Electronics", "High-end laptop"),
                ("Smartphone", "https://example.com/phone", 699.99, "Electronics", "Latest smartphone"),
                ("Headphones", "https://example.com/headphones", 199.99, "Electronics", "Noise-cancelling")
            ]

            self.cursor.executemany('''INSERT INTO products (product_name, url, price, category, description)
            VALUES (?, ?, ?, ?, ?)''', product_info)

            self.connection.commit()
            self.connection.close()
        except sqlite3.Error as e:
            print(f"Error inserting dummy data: {e}")
            self.connection.rollback()
