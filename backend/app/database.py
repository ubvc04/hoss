import sqlite3
import os
from .config import Config

def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    """Initialize the database from schema.sql."""
    if not os.path.exists(Config.DATABASE_PATH):
        conn = sqlite3.connect(Config.DATABASE_PATH)
        with open(Config.SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
        conn.close()
        return True
    return False

def query_db(query, args=(), one=False, commit=False):
    """Execute a query and return results."""
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        if commit:
            conn.commit()
            return cur.lastrowid
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=(), return_lastrowid=True):
    """Execute an INSERT/UPDATE/DELETE query."""
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        conn.commit()
        return cur.lastrowid if return_lastrowid else cur.rowcount
    finally:
        conn.close()

def execute_many(query, args_list):
    """Execute a query with multiple sets of parameters."""
    conn = get_db()
    try:
        conn.executemany(query, args_list)
        conn.commit()
    finally:
        conn.close()

def dict_from_row(row):
    """Convert a sqlite3.Row to a dict."""
    if row is None:
        return None
    return dict(row)

def dicts_from_rows(rows):
    """Convert a list of sqlite3.Row to list of dicts."""
    return [dict(row) for row in rows]
