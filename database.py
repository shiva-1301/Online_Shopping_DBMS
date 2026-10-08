"""Configuration and database access shared by db_setup.py and app.py.

Credentials are read from environment variables (or a local .env file) instead of
being hardcoded. Two backends are supported:

* oracle - the original Oracle XE database (python-oracledb, falls back to cx_Oracle)
* sqlite - a self-contained demo database file, no install required
"""
import os
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "assets" / "images"
SQLITE_PATH = BASE_DIR / "shop_demo.db"


def load_env(path=BASE_DIR / ".env"):
    """Minimal .env loader so we don't need python-dotenv."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()

DB_BACKEND = os.environ.get("DB_BACKEND", "sqlite").lower()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


def connect():
    """Open a connection for the configured backend. Raises on failure."""
    if DB_BACKEND == "oracle":
        try:
            import oracledb as driver
        except ImportError:
            import cx_Oracle as driver
        missing = [k for k in ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN") if not os.environ.get(k)]
        if missing:
            raise RuntimeError(f"Missing environment variables: {', '.join(missing)} (see .env.example)")
        return driver.connect(
            user=os.environ["ORACLE_USER"],
            password=os.environ["ORACLE_PASSWORD"],
            dsn=os.environ["ORACLE_DSN"],
        )
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# --- SQL dialect helpers -----------------------------------------------------
# Queries are written in Oracle syntax; for SQLite we rewrite the few
# Oracle-only constructs the app uses.

def to_dialect(sql):
    if DB_BACKEND == "oracle":
        return sql
    sql = re.sub(r"TO_CHAR\(([\w.]+),\s*'YYYY-MM-DD'\)", r"strftime('%Y-%m-%d', \1)", sql)
    sql = re.sub(r"TO_DATE\((:\w+),\s*'YYYY-MM-DD'\)", r"\1", sql)
    sql = re.sub(r":\d+\b", "?", sql)  # Oracle positional binds -> SQLite
    sql = re.sub(r"FETCH FIRST (\d+) ROWS ONLY", r"LIMIT \1", sql)
    return sql


def query(cursor, sql, params=None):
    """Execute a SELECT and return (column_names, rows)."""
    cursor.execute(to_dialect(sql), params or {})
    columns = [col[0] for col in cursor.description]
    return columns, cursor.fetchall()
