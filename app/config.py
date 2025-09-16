from pydantic import BaseModel
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
