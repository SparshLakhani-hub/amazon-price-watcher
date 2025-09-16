from statistics import mean
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
