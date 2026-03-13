# db.py
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

DB_FILE = "vera.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS accounts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    balance REAL DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    category_id INTEGER,
    account_id INTEGER,
    target_account_id INTEGER,
    description TEXT,
    recurring_rule TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(category_id) REFERENCES categories(id),
    FOREIGN KEY(account_id) REFERENCES accounts(id),
    FOREIGN KEY(target_account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER,
    amount REAL NOT NULL,
    period TEXT NOT NULL, -- monthly, weekly, custom
    start_date TEXT,
    end_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    saved_amount REAL DEFAULT 0,
    target_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    amount REAL,
    type TEXT, -- mutual fund, stock, savings
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    principal REAL,
    balance REAL,
    interest_rate REAL,
    monthly_payment REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

DEFAULT_CATEGORIES = [
    "Education", "Entertainment", "Food", "Groceries", "Health", "Insurance", "Rent", "Salary", "Shopping", "Subscriptions", "Utilities", "Transport", "Transfer", "Other"
]

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.execute("SELECT count(*) as c FROM categories") #categorires
    if cur.fetchone()["c"] == 0:
        for cat in DEFAULT_CATEGORIES:
            cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

    cur.execute("SELECT count(*) as c FROM accounts") #default cassh account
    if cur.fetchone()["c"] == 0:
        cur.execute("INSERT INTO accounts (name, type, balance) VALUES (?, ?, ?)",
                    ("Cash", "cash", 0.0))
    conn.commit()
    conn.close()

# Accounts
def add_account(name: str, type_: str, balance: float=0.0, currency: str="INR"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (name, type, balance, currency) VALUES (?, ?, ?, ?)",
                (name, type_, balance, currency))
    conn.commit()
    conn.close()

def get_accounts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Categories
def get_categories():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def add_category(name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

# Transactions
def add_transaction(date: str, amount: float, type_: str, category_id: int, account_id: int,
                    description: str=None, target_account_id: int=None, recurring_rule: str=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions
        (date, amount, type, category_id, account_id, target_account_id, description, recurring_rule)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (date, amount, type_, category_id, account_id, target_account_id, description, recurring_rule))
    # Update account balances
    if type_ == "income":
        cur.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, account_id))
    elif type_ == "expense":
        cur.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, account_id))
    elif type_ == "transfer" and target_account_id:
        # subtract from source, add to target
        cur.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, account_id))
        cur.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, target_account_id))
    conn.commit()
    conn.close()

def get_transactions(limit:int=200, filters:Dict[str,Any]=None):
    filters = filters or {}
    conn = get_conn()
    cur = conn.cursor()
    q = "SELECT t.*, c.name as category, a.name as account, ta.name as target_account FROM transactions t LEFT JOIN categories c ON t.category_id=c.id LEFT JOIN accounts a ON t.account_id=a.id LEFT JOIN accounts ta ON t.target_account_id=ta.id"
    clauses = []
    params = []
    if "start_date" in filters:
        clauses.append("date >= ?"); params.append(filters["start_date"])
    if "end_date" in filters:
        clauses.append("date <= ?"); params.append(filters["end_date"])
    if "type" in filters:
        clauses.append("type = ?"); params.append(filters["type"])
    if "category_id" in filters:
        clauses.append("category_id = ?"); params.append(filters["category_id"])
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY date DESC LIMIT ?"
    params.append(limit)
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Budgets
def add_budget(category_id:int, amount:float, period:str="monthly", start_date:str=None, end_date:str=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO budgets (category_id, amount, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
                (category_id, amount, period, start_date, end_date))
    conn.commit()
    conn.close()

def get_budgets():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT b.*, c.name as category FROM budgets b LEFT JOIN categories c ON b.category_id=c.id ORDER BY b.id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Goals
def add_goal(name:str, target_amount:float, target_date:str=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO goals (name, target_amount, target_date) VALUES (?, ?, ?)", (name, target_amount, target_date))
    conn.commit()
    conn.close()

def update_goal_saved(goal_id:int, amount:float):
    conn = get_conn()
    cur = conn.cursor()
    # increment saved_amount
    cur.execute("UPDATE goals SET saved_amount = saved_amount + ? WHERE id = ?", (amount, goal_id))
    conn.commit()
    conn.close()

def get_goals():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM goals ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Investments
def add_investment(name:str, amount:float, type_:str="mutual fund"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO investments (name, amount, type) VALUES (?, ?, ?)", (name, amount, type_))
    conn.commit()
    conn.close()

def get_investments():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM investments ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Loans
def add_loan(name:str, principal:float, balance:float, interest_rate:float, monthly_payment:float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO loans (name, principal, balance, interest_rate, monthly_payment) VALUES (?, ?, ?, ?, ?)",
                (name, principal, balance, interest_rate, monthly_payment))
    conn.commit()
    conn.close()

def get_loans():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM loans ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Net worth
def calculate_net_worth():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT SUM(balance) as total FROM accounts")
    total = cur.fetchone()["total"] or 0.0
    # investments add value
    cur.execute("SELECT SUM(amount) as inv FROM investments")
    inv = cur.fetchone()["inv"] or 0.0
    # subtract loans balances
    cur.execute("SELECT SUM(balance) as loans FROM loans")
    loans = cur.fetchone()["loans"] or 0.0
    conn.close()
    return total + inv - loans

# Utility: run arbitrary queries (used for export)
def export_transactions_csv(path):
    import pandas as pd
    rows = get_transactions(limit=100000)
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
