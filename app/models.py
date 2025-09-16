from .db import get_conn
from typing import Optional, List, Tuple

def add_product(url: str, asin: Optional[str] = None, threshold_pct: float = 10.0):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO products(url, asin, threshold_pct) VALUES (?, ?, ?)",
            (url, asin, threshold_pct)
        )
        conn.commit()

def list_products(active_only=True):
    q = "SELECT id, url, asin, title, currency, threshold_pct FROM products"
    if active_only:
        q += " WHERE active=1"
    with get_conn() as conn:
        return conn.execute(q).fetchall()

def update_product_title_currency(product_id: int, title: str, currency: str):
    with get_conn() as conn:
        conn.execute("UPDATE products SET title=?, currency=? WHERE id=?",
                     (title, currency, product_id))
        conn.commit()

def insert_price(product_id: int, price_cents: int, currency: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO price_history(product_id, price_cents, currency) VALUES (?, ?, ?)",
            (product_id, price_cents, currency)
        )
        conn.commit()

def recent_prices(product_id: int, days: int = 30) -> List[Tuple[int]]:
    with get_conn() as conn:
        return conn.execute(
            f"""
            SELECT price_cents FROM price_history
            WHERE product_id=? AND snapshot_at >= datetime('now', '-{days} day')
            ORDER BY snapshot_at DESC
            """,
            (product_id,)
        ).fetchall()

def add_alert(product_id: int, message: str):
    with get_conn() as conn:
        conn.execute("INSERT INTO alerts(product_id, message) VALUES (?, ?)", (product_id, message))
        conn.commit()
