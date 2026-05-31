"""
SQLite database layer for TelcoMax customer data.
Provides persistent storage for customers, plans, bills, usage, and support tickets.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

from config.settings import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database (creates file if needed)."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Schema Creation ───────────────────────────────────────────────────

def initialize_database():
    """Create all tables and seed sample data if the database is empty."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id   TEXT PRIMARY KEY,
        name          TEXT NOT NULL,
        email         TEXT,
        phone         TEXT,
        plan_id       TEXT,
        account_status TEXT DEFAULT 'active',
        created_at    TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS plans (
        plan_id       TEXT PRIMARY KEY,
        plan_name     TEXT NOT NULL,
        monthly_price REAL,
        data_limit_gb REAL,
        call_minutes  INTEGER,
        sms_limit     INTEGER,
        features      TEXT,
        plan_type     TEXT DEFAULT 'postpaid'
    );

    CREATE TABLE IF NOT EXISTS bills (
        bill_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id   TEXT,
        billing_month TEXT,
        amount        REAL,
        due_date      TEXT,
        status        TEXT DEFAULT 'unpaid',
        breakdown     TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS usage_records (
        record_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id   TEXT,
        record_date   TEXT,
        data_used_gb  REAL,
        calls_minutes INTEGER,
        sms_sent      INTEGER,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS support_tickets (
        ticket_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id   TEXT,
        category      TEXT,
        description   TEXT,
        status        TEXT DEFAULT 'open',
        created_at    TEXT DEFAULT (datetime('now')),
        resolved_at   TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)
    conn.commit()

    # Seed data only if tables are empty
    if cur.execute("SELECT COUNT(*) FROM plans").fetchone()[0] == 0:
        _seed_data(conn)

    conn.close()


def _seed_data(conn: sqlite3.Connection):
    """Insert realistic sample data for demonstration."""
    cur = conn.cursor()

    # ── Plans ─────────────────────────────────────────────────────────
    plans = [
        ("basic-01",   "TelcoMax Basic",      29.99,  5,   200,  500,  "Voicemail, Caller ID",                        "postpaid"),
        ("standard-02","TelcoMax Standard",    49.99,  20,  500,  1000, "Voicemail, Caller ID, Hotspot 5GB",           "postpaid"),
        ("premium-03", "TelcoMax Premium",     79.99,  50,  1500, 3000, "Voicemail, Caller ID, Hotspot 20GB, Intl 100","postpaid"),
        ("unlimited-04","TelcoMax Unlimited",  99.99, 999,  9999, 9999, "Everything Unlimited, Intl 500, Priority",    "postpaid"),
        ("prepaid-05", "TelcoMax Prepaid Lite",15.00,  2,   100,  200,  "Pay-as-you-go, No contract",                  "prepaid"),
        ("family-06",  "TelcoMax Family",     119.99, 100,  5000, 9999, "Up to 5 lines, Shared data, Disney+",         "postpaid"),
    ]
    cur.executemany("INSERT INTO plans VALUES (?,?,?,?,?,?,?,?)", plans)

    # ── Customers ─────────────────────────────────────────────────────
    customers = [
        ("CUST-1001", "Alice Johnson",  "alice@email.com",   "+1-555-0101", "standard-02", "active"),
        ("CUST-1002", "Bob Martinez",   "bob@email.com",     "+1-555-0102", "premium-03",  "active"),
        ("CUST-1003", "Carol Chen",     "carol@email.com",   "+1-555-0103", "basic-01",    "active"),
        ("CUST-1004", "David Williams", "david@email.com",   "+1-555-0104", "unlimited-04","active"),
        ("CUST-1005", "Eva Brown",      "eva@email.com",     "+1-555-0105", "prepaid-05",  "suspended"),
        ("CUST-1006", "Frank Davis",    "frank@email.com",   "+1-555-0106", "family-06",   "active"),
    ]
    cur.executemany("INSERT INTO customers (customer_id,name,email,phone,plan_id,account_status) VALUES (?,?,?,?,?,?)", customers)

    # ── Bills (last 3 months) ─────────────────────────────────────────
    price_map = {p[0]: p[2] for p in plans}
    for cust_id, _, _, _, plan_id, _ in customers:
        base = price_map.get(plan_id, 30.0)
        for m in range(3):
            month = (datetime.now() - timedelta(days=30 * m)).strftime("%Y-%m")
            amount = round(base + random.uniform(-5, 15), 2)
            due = (datetime.now() - timedelta(days=30 * m - 15)).strftime("%Y-%m-%d")
            status = "paid" if m > 0 else random.choice(["paid", "unpaid"])
            breakdown = f"Base: ${base}, Extras: ${round(amount - base, 2)}"
            cur.execute("INSERT INTO bills (customer_id,billing_month,amount,due_date,status,breakdown) VALUES (?,?,?,?,?,?)",
                        (cust_id, month, amount, due, status, breakdown))

    # ── Usage Records (last 7 days) ───────────────────────────────────
    for cust_id, *_ in customers:
        for d in range(7):
            date = (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")
            cur.execute("INSERT INTO usage_records (customer_id,record_date,data_used_gb,calls_minutes,sms_sent) VALUES (?,?,?,?,?)",
                        (cust_id, date, round(random.uniform(0.2, 4.0), 2), random.randint(5, 120), random.randint(0, 50)))

    # ── Support Tickets ───────────────────────────────────────────────
    tickets = [
        ("CUST-1001", "billing",    "Unexpected charge on March bill",         "resolved"),
        ("CUST-1002", "technical",  "Slow data speeds in downtown area",       "open"),
        ("CUST-1003", "account",    "Request to upgrade plan",                 "open"),
        ("CUST-1005", "billing",    "Account suspended but payment was made",  "open"),
    ]
    for cust_id, cat, desc, st in tickets:
        resolved = datetime.now().isoformat() if st == "resolved" else None
        cur.execute("INSERT INTO support_tickets (customer_id,category,description,status,resolved_at) VALUES (?,?,?,?,?)",
                    (cust_id, cat, desc, st, resolved))

    conn.commit()
