"""
Database connection and query utilities for E-commerce Product Reviews Analysis.
Uses context manager pattern for clean connection handling.
"""
import os
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error


# Database configuration (use env vars in production)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "your password"),
    "database": os.getenv("DB_NAME", "openfeedback"),
    "autocommit": False,
}


def get_connection():
    """Create and return a new database connection."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        raise ConnectionError(f"Database connection failed: {e}") from e


@contextmanager
def get_cursor(commit=False):
    """
    Context manager for database operations.
    Yields cursor, handles commit/rollback, and ensures resources are closed.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_query(query: str, params: tuple = None, fetch=True):
    """
    Execute a query and optionally fetch results.
    Optimized for read operations with proper connection handling.
    """
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
    return None


def execute_insert(query: str, params: tuple):
    """Execute insert and return last inserted ID."""
    with get_cursor(commit=True) as cursor:
        cursor.execute(query, params)
        return cursor.lastrowid


def execute_many(query: str, params_list: list):
    """Execute bulk insert/update."""
    with get_cursor(commit=True) as cursor:
        cursor.executemany(query, params_list)


def read_sql_dataframe(query: str):
    """Execute query and return results as pandas DataFrame."""
    import pandas as pd
    conn = get_connection()
    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()
