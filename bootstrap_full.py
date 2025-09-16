# bootstrap_full.py — writes all project files with the full working code
import os
from pathlib import Path

root = Path.cwd()
(root / "app").mkdir(exist_ok=True, parents=True)
(root / ".github" / "workflows").mkdir(exist_ok=True, parents=True)

files = {
"requirements.txt": """playwright==1.46.0
python-dotenv==1.0.1
APScheduler==3.10.4
pydantic==2.9.2
beautifulsoup4==4.12.3
lxml==5.3.0
""",
"app/__init__.py": "",
"app/config.py": '''from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    AMAZON_BASE_URL: str = os.getenv("AMAZON_BASE_URL", "https://www.amazon.com")
    ALERT_EMAIL_FROM: str = os.getenv("ALERT_EMAIL_FROM", "")
    ALERT_EMAIL_TO: str = os.getenv("ALERT_EMAIL_TO", "")
    ALERT_EMAIL_SMTP: str = os.getenv("ALERT_EMAIL_SMTP", "")
    ALERT_EMAIL_PORT: int = int(os.getenv("ALERT_EMAIL_PORT", "587"))
    ALERT_EMAIL_USER: str = os.getenv("ALERT_EMAIL_USER", "")
    ALERT_EMAIL_PASS: str = os.getenv("ALERT_EMAIL_PASS", "")
    SCRAPER_MIN_SLEEP_SEC: float = float(os.getenv("SCRAPER_MIN_SLEEP_SEC", "6"))
    SCRAPER_MAX_SLEEP_SEC: float = float(os.getenv("SCRAPER_MAX_SLEEP_SEC", "14"))
    SCRAPER_MAX_RETRIES: int = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    TIMEZONE: str = os.getenv("TIMEZONE", "America/New_York")

settings = Settings()
''',
"app/db.py": '''import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            asin TEXT,
            title TEXT,
            currency TEXT,
            threshold_pct REAL NOT NULL DEFAULT 10.0,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price_cents INTEGER NOT NULL,
            currency TEXT NOT NULL,
            snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            triggered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            message TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """)
        conn.commit()
''',
"app/models.py": '''from .db import get_conn
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
''',
"app/utils.py": '''import random, time, re
from contextlib import contextmanager

def human_delay(min_s: float, max_s: float):
    time.sleep(random.uniform(min_s, max_s))

def parse_asin_from_url(url: str):
    m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
    return m.group(1) if m else None

@contextmanager
def retry(max_retries: int, on_error_delay: float = 5.0):
    tries = 0
    while True:
        try:
            yield
            break
        except Exception:
            tries += 1
            if tries >= max_retries:
                raise
            time.sleep(on_error_delay)
''',
"app/parser.py": r'''import re
from bs4 import BeautifulSoup

def extract_title_and_price(html: str):
    soup = BeautifulSoup(html, "lxml")

    # Title
    title = None
    t = soup.select_one("#productTitle")
    if t: title = t.get_text(strip=True)
    if not title:
        t = soup.find("span", {"id": "title"})
        if t: title = t.get_text(strip=True)

    # Price
    price_text = None
    for sel in [
        "#corePrice_feature_div span.a-offscreen",
        "#apex_desktop span.a-offscreen",
        "#corePriceDisplay_desktop_feature_div span.a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
    ]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            price_text = el.get_text(strip=True)
            break
    if not price_text:
        for el in soup.select("span.a-offscreen"):
            txt = el.get_text(strip=True)
            if re.search(r"[¥£€$]\s*\d", txt):
                price_text = txt
                break
    if not price_text:
        raise ValueError("Could not find price on the page.")

    # Currency + number
    currency_symbol = re.findall(r"[^\d\s.,-]", price_text)
    currency = currency_symbol[0] if currency_symbol else "$"
    num = re.sub(r"[^\d.,-]", "", price_text)
    if num.count(",") > 0 and num.count(".") == 0:
        num = num.replace(".", "").replace(",", ".")
    else:
        num = num.replace(",", "")
    value = float(num)
    price_cents = int(round(value * 100))

    return title, price_cents, currency
''',
"app/scraper.py": '''from playwright.sync_api import sync_playwright
from .utils import human_delay
from .config import settings

def fetch_product_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) "
                        "Gecko/20100101 Firefox/131.0"),
            locale="en-US",
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Cookie banners (best-effort)
        for sel in ["#sp-cc-accept", "input#sp-cc-accept", "button[name='accept']"]:
            try:
                if page.is_visible(sel):
                    page.click(sel, timeout=2000)
                    page.wait_for_timeout(500)
            except Exception:
                pass

        human_delay(settings.SCRAPER_MIN_SLEEP_SEC, settings.SCRAPER_MAX_SLEEP_SEC)
        page.wait_for_timeout(1000)
        html = page.content()
        context.close()
        browser.close()
        return html
''',
"app/alerts.py": '''import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import settings

def send_email(subject: str, body_html: str):
    if not settings.ALERT_EMAIL_TO or not settings.ALERT_EMAIL_FROM:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.ALERT_EMAIL_FROM
    msg["To"] = settings.ALERT_EMAIL_TO
    msg.attach(MIMEText(body_html, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(settings.ALERT_EMAIL_SMTP, settings.ALERT_EMAIL_PORT) as server:
        server.starttls(context=ctx)
        server.login(settings.ALERT_EMAIL_USER, settings.ALERT_EMAIL_PASS)
        server.sendmail(settings.ALERT_EMAIL_FROM, [settings.ALERT_EMAIL_TO], msg.as_string())
''',
"app/logic.py": '''from statistics import mean
from .models import recent_prices, add_alert
from .alerts import send_email

def maybe_alert(product_row, latest_price_cents: int, product_url: str):
    """
    product_row: (id, url, asin, title, currency, threshold_pct)
    Rule: alert if latest <= (1 - threshold/100) * (max price in last 30 days)
    """
    product_id, url, asin, title, currency, threshold_pct = product_row
    history = recent_prices(product_id, days=30)
    prices = [p[0] for p in history]

    # Need at least a handful of points
    if len(prices) < 5:
        return

    max_30d = max(prices)
    trigger_price = int(round(max_30d * (1 - threshold_pct / 100.0)))

    if latest_price_cents <= trigger_price:
        drop_pct = (1 - latest_price_cents / max_30d) * 100
        avg_30d = mean(prices)
        msg = (
            f"🔔 <b>Deal alert</b> for <b>{title or 'Product'}</b><br>"
            f"Current: {currency}{latest_price_cents/100:.2f}<br>"
            f"30-day <b>max</b>: {currency}{max_30d/100:.2f} (−{drop_pct:.1f}% vs max)<br>"
            f"30-day avg: {currency}{avg_30d/100:.2f}<br>"
            f"<a href='{url}'>Open on Amazon</a>"
        )
        add_alert(product_id, message=msg)
        send_email(subject=f"Price drop (vs 30-day max): {title or 'Amazon Product'}",
                   body_html=msg)
''',
"app/scheduler.py": '''from apscheduler.schedulers.blocking import BlockingScheduler
from .config import settings
from .models import list_products, insert_price, update_product_title_currency
from .scraper import fetch_product_html
from .parser import extract_title_and_price
from .logic import maybe_alert
from .utils import retry, human_delay

def job_once():
    for row in list_products(active_only=True):
        (pid, url, asin, title, currency, threshold_pct) = row
        with retry(settings.SCRAPER_MAX_RETRIES, on_error_delay=10):
            html = fetch_product_html(url)
            t, price_cents, curr = extract_title_and_price(html)
            if t and curr:
                update_product_title_currency(pid, t, curr)
            insert_price(pid, price_cents, curr or currency or "$")
            maybe_alert((pid, url, asin, t or title, curr or currency or "$", threshold_pct),
                        latest_price_cents=price_cents,
                        product_url=url)
            human_delay(settings.SCRAPER_MIN_SLEEP_SEC, settings.SCRAPER_MAX_SLEEP_SEC)

def run_daily_scheduler():
    sched = BlockingScheduler(timezone=settings.TIMEZONE)
    sched.add_job(job_once, "cron", hour=8, minute=30)
    job_once()
    sched.start()
''',
"add_product.py": '''from app.db import init_db
from app.models import add_product
from app.utils import parse_asin_from_url
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_product.py <amazon_product_url> [threshold_pct]")
        sys.exit(1)
    url = sys.argv[1].strip()
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    init_db()
    asin = parse_asin_from_url(url)
    add_product(url=url, asin=asin, threshold_pct=threshold)
    print(f"Added: {url} (ASIN: {asin or 'n/a'}), threshold={threshold}%")
''',
"run_once.py": '''from app.db import init_db
from app.scheduler import job_once

if __name__ == "__main__":
    init_db()
    job_once()
    print("Completed one scrape+alert cycle.")
''',
".github/workflows/price-watch.yml": '''name: Amazon Price Watch

on:
  schedule:
    - cron: "30 12 * * *"  # ~08:30 America/New_York (UTC-based)
  workflow_dispatch: {}

jobs:
  scrape:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Python deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install Playwright browsers & system deps
        run: |
          python -m playwright install
          python -m playwright install-deps

      - name: Create .env from secrets
        run: |
          cat > .env << 'EOF'
          AMAZON_BASE_URL=${{ secrets.AMAZON_BASE_URL }}
          ALERT_EMAIL_FROM=${{ secrets.ALERT_EMAIL_FROM }}
          ALERT_EMAIL_TO=${{ secrets.ALERT_EMAIL_TO }}
          ALERT_EMAIL_SMTP=${{ secrets.ALERT_EMAIL_SMTP }}
          ALERT_EMAIL_PORT=${{ secrets.ALERT_EMAIL_PORT }}
          ALERT_EMAIL_USER=${{ secrets.ALERT_EMAIL_USER }}
          ALERT_EMAIL_PASS=${{ secrets.ALERT_EMAIL_PASS }}
          SCRAPER_MIN_SLEEP_SEC=6
          SCRAPER_MAX_SLEEP_SEC=14
          SCRAPER_MAX_RETRIES=3
          TIMEZONE=America/New_York
          EOF

      - name: Initialize DB (safe if exists)
        run: |
          python -c "from app.db import init_db; init_db()"

      - name: Run one scrape + alert cycle
        run: |
          python run_once.py

      - name: Commit DB back to repo (if changed)
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add db.sqlite3
          git diff --cached --quiet || (git commit -m "Update db.sqlite3 [ci skip]" && git push)
''',
}

for rel, content in files.items():
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

print("✅ Wrote full project files.")
