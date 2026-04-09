# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beautifulsoup4>=4.14.3",
#     "lxml>=6.0.2",
# ]
# ///
import csv
from bs4 import BeautifulSoup
from pathlib import Path

def txt(node):
    return node.get_text(strip=True) if node else ""

html = Path("t.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "lxml")

rows = []

# Each order card root
for order in soup.select("div.J632se"):
    shop_name = txt(order.select_one("div.UDaMW3"))
    # Prefer the short status (e.g. "rated"); fall back to delivery message.
    status = txt(order.select_one("div.bv3eJE")) or txt(order.select_one("span.O2yAdQ"))
    order_link = order.select_one("a.lXbYsi")
    order_href = order_link["href"] if order_link and order_link.has_attr("href") else ""

    # order total might be inside the same card or a nearby sibling
    order_total = ""
    total_node = order.select_one("div.NWUSQP div.t7TQaf")
    if total_node:
        order_total = txt(total_node)
    else:
        # try next siblings if the total is outside the order block
        for sib in order.find_all_next("div", class_="NWUSQP", limit=3):
            order_total = txt(sib.select_one("div.t7TQaf"))
            if order_total:
                break

    # item rows inside this order
    items = order.select("span.DWVWOJ")
    if not items:
        # still write an order-level row even if no items found
        rows.append({
            "shop": shop_name,
            "status": status,
            "order_href": order_href,
            "item_name": "",
            "qty": "",
            "item_price": "",
            "order_total": order_total,
        })
        continue

    for item_name_node in items:
        item_name = txt(item_name_node)
        # walk up to item container to find qty/price nearby
        item_container = item_name_node.find_parent("section") or item_name_node.parent
        qty = txt(item_container.select_one("div.j3I_Nh"))
        item_price = txt(item_container.select_one("span.nW_6Oi"))

        rows.append({
            "shop": shop_name,
            "status": status,
            "order_href": order_href,
            "item_name": item_name,
            "qty": qty,
            "item_price": item_price,
            "order_total": order_total,
        })

with open("transactions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "shop", "status", "order_href", "item_name", "qty", "item_price", "order_total"
    ])
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to transactions.csv")
