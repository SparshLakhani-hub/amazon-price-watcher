from apscheduler.schedulers.blocking import BlockingScheduler
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

            # Update title/currency if we saw them
            if t:
                update_product_title_currency(pid, t, curr or currency or "$")

            # If we still couldn't find a price, just skip gracefully
            if price_cents is None:
                # No exception — continue with next product
                human_delay(settings.SCRAPER_MIN_SLEEP_SEC, settings.SCRAPER_MAX_SLEEP_SEC)
                continue

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
