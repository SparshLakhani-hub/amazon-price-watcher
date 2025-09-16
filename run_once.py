from app.db import init_db, get_conn
from app.scheduler import job_once

if __name__ == "__main__":
    init_db()
    job_once()
    with get_conn() as conn:
        rows = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()
        print(f"📊 Price history rows in DB: {rows[0]}")
