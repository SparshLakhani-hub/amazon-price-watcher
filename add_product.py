from app.db import init_db
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
