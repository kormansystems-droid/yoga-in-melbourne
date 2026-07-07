"""
probe_gomindbody.py  (v3 — diagnostic)

v1/v2 confirmed: NO block on a datacenter IP. But the schedule wouldn't populate
headless and my day-tab locator found 0 tabs. v3 stops guessing: it dumps every
button's text and a body snippet so we can SEE what's on the page, then clicks
the date-strip tabs by position (not regex) and measures what renders.

Send me the whole JSON. It tells us: locator bug (tabs present -> scrape viable)
vs genuine under-render (no tabs -> drop the scrape).
"""
import json, re, sys

WIDGET = "https://go.mindbodyonline.com/book/widgets/schedules/view/751447bfa/schedule"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

def metrics(text):
    return {
        "bytes": len(text),
        "times": len(re.findall(r"\d{1,2}:\d{2}\s?(?:am|pm)", text, re.I)),
        "challenge": bool(re.search(r"cloudflare|captcha|are you a human|access denied|attention required|blocked", text, re.I)),
    }

def main():
    from playwright.sync_api import sync_playwright
    out = {"widget": WIDGET, "day_clicks": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=UA)
        try:
            pg.goto(WIDGET, wait_until="load", timeout=60000)
        except Exception as e:
            out["goto_error"] = str(e)[:150]
        try:
            pg.wait_for_selector("text=Today", timeout=30000)
            out["shell_rendered"] = True
        except Exception as e:
            out["shell_rendered"] = False
            out["shell_error"] = str(e)[:120]
        pg.wait_for_timeout(6000)
        out["title"] = pg.title()
        out["initial"] = metrics(pg.inner_text("body"))
        out["initial_snippet"] = re.sub(r"\s+", " ", pg.inner_text("body"))[:500]

        # DIAGNOSTIC: dump every button's text
        btns = pg.locator("button")
        nb = btns.count()
        out["button_count"] = nb
        out["button_texts"] = []
        for i in range(min(nb, 30)):
            try:
                out["button_texts"].append(btns.nth(i).inner_text()[:24].replace("\n", "|"))
            except Exception:
                out["button_texts"].append("<err>")

        # click buttons that look like date tabs (short text ending in a number), by position
        clicked = 0
        for i in range(min(nb, 30)):
            try:
                txt = btns.nth(i).inner_text().replace("\n", " ").strip()
                if re.search(r"\d{1,2}$", txt) and len(txt) <= 8 and clicked < 6:
                    btns.nth(i).click(timeout=6000)
                    pg.wait_for_timeout(3500)
                    m = metrics(pg.inner_text("body"))
                    m["tab"] = txt
                    out["day_clicks"].append(m)
                    clicked += 1
            except Exception as e:
                out["day_clicks"].append({"tab_idx": i, "error": str(e)[:90]})
        b.close()

    total = out.get("initial", {}).get("times", 0) + sum(d.get("times", 0) for d in out["day_clicks"])
    challenged = out.get("initial", {}).get("challenge") or any(d.get("challenge") for d in out["day_clicks"])
    if challenged:
        verdict = "FAIL - challenge/block on datacenter IP."
    elif total >= 10:
        verdict = f"PASS - {total} class-times rendered headless, no block. Scraper viable."
    else:
        verdict = f"DIAGNOSTIC - {total} times, {out.get('button_count',0)} buttons. Read button_texts below."
    print("=" * 70)
    print("VERDICT:", verdict)
    print("=" * 70)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    sys.exit(main())
