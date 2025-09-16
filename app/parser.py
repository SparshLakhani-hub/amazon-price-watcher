import re, json
from bs4 import BeautifulSoup

def _norm_price_text(price_text: str):
    # Keep digits, dot, comma, minus; infer decimal; return cents (int)
    num = re.sub(r"[^\d.,-]", "", price_text)
    if not num:
        return None
    # If there are commas but no dot, treat comma as decimal (e.g., 1.234,56)
    if num.count(",") > 0 and num.count(".") == 0:
        num = num.replace(".", "").replace(",", ".")
    else:
        num = num.replace(",", "")
    try:
        value = float(num)
    except ValueError:
        return None
    return int(round(value * 100))

def extract_title_and_price(html: str):
    soup = BeautifulSoup(html, "lxml")

    # ---- Title ----
    title = None
    for sel in ["#productTitle", "span#title", "h1.a-size-large.a-spacing-none"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break

    # ---- Try lots of price selectors first ----
    price_text = None
    candidates = [
        "#corePrice_feature_div span.a-offscreen",
        "#apex_desktop span.a-offscreen",
        "#corePriceDisplay_desktop_feature_div span.a-offscreen",
        "span#priceblock_ourprice",
        "span#priceblock_dealprice",
        "span#priceblock_saleprice",
        "span#price_inside_buybox",
        "#sns-base-price .a-offscreen",
        ".a-price .a-offscreen",
        ".a-price-whole",  # sometimes split whole+fraction
    ]
    for sel in candidates:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            price_text = el.get_text(strip=True)
            break

    # Handle split whole + fraction (e.g. $199<span class="a-price-fraction">99</span>)
    if not price_text:
        whole = soup.select_one(".a-price .a-price-whole")
        frac = soup.select_one(".a-price .a-price-fraction")
        if whole and whole.get_text(strip=True):
            price_text = whole.get_text(strip=True)
            if frac and frac.get_text(strip=True):
                price_text = f"{price_text}.{frac.get_text(strip=True)}"

    # ---- JSON-LD fallback (offers.price) ----
    currency = None
    if not price_text:
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.get_text(strip=True))
            except Exception:
                continue
            # Sometimes it's a list
            items = data if isinstance(data, list) else [data]
            for it in items:
                offers = it.get("offers")
                if isinstance(offers, dict):
                    price = offers.get("price") or offers.get("lowPrice")
                    currency = offers.get("priceCurrency") or currency
                    if price:
                        price_text = str(price)
                        break
            if price_text:
                break

    # ---- OpenGraph meta fallback ----
    if not price_text:
        og_price = soup.find("meta", {"property": "og:price:amount"})
        og_currency = soup.find("meta", {"property": "og:price:currency"})
        if og_price and og_price.get("content"):
            price_text = og_price.get("content")
        if og_currency and og_currency.get("content"):
            currency = og_currency.get("content")

    # ---- Final parse / normalization ----
    price_cents = None
    if price_text:
        # Guess currency symbol if not provided
        if not currency:
            sym = re.findall(r"[^\d\s.,-]", price_text)
            if sym:
                currency = sym[0]
        price_cents = _norm_price_text(price_text)

    # Currency fallback
    if not currency:
        currency = "$"

    # Return title and currency even if price is missing (None)
    return title, price_cents, currency
