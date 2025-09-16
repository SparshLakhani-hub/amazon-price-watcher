import random, time, re
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
