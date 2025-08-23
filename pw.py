# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright
import json, time, os

SAVE_DIR = "elhkpn_data"
os.makedirs(SAVE_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # not headless so you can solve CAPTCHA
    context = browser.new_context()
    page = context.new_page()

    # Step 1: go to site and solve captcha
    page.goto("https://elhkpn.kpk.go.id", wait_until="domcontentloaded")
    input("Solve CAPTCHA and navigate to the search form, then press Enter...")

    # Step 2: type search query
    page.fill("input[name='nama']", "Prabowo Subianto")
    page.click("button[type='submit']")  # adjust selector to actual search button

    # Step 3: wait for results (table should load via AJAX)
    page.wait_for_selector("table")  # adjust to the result table selector
    time.sleep(2)

    # Intercept JSON responses
    def handle_response(resp):
        url = resp.url
        if "lhkpn" in url and resp.request.resource_type in ("xhr", "fetch"):
            try:
                body = resp.json()
            except:
                return
            ts = int(time.time() * 1000)
            fname = os.path.join(SAVE_DIR, f"{ts}.json")
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(body, f, indent=2, ensure_ascii=False)
            print(f"Saved: {fname} from {url}")

    page.on("response", handle_response)

    # Step 4: click on rows for detail pages (collecting 5 years)
    rows = page.query_selector_all("table tr")  # adjust to row selector
    for row in rows:
        try:
            row.click()
            page.wait_for_timeout(2000)
        except:
            pass

    input("Done scraping? Press Enter to close...")
    browser.close()
