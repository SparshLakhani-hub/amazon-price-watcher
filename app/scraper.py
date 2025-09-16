from playwright.sync_api import sync_playwright
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
