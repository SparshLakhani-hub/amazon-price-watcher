import re
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
