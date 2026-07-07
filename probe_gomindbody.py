"""
probe_gomindbody.py  (v2)

v1 was inconclusive for a dumb reason: it waited for `networkidle`, but the
Schedules V2 widget streams telemetry forever, so networkidle never fires and
goto timed out before the schedule rendered. v1 DID confirm the important thing:
no challenge/block on a GitHub Actions (datacenter) IP.

v2 fixes the waits: load the DOM, wait for the schedule shell to hydrate, then
click through the day tabs and count what renders.

PASS = classes render headless on a datacenter IP -> scraper is a viable build.
FAIL = challenge/block detected -> drop scraper, pursue official Mindbody API.
"""
import json, re, sys

WIDGET = "https://go.mindbodyonline.com/book/widgets/schedules/view/751447bfa/schedule"  # Warrior One Brighton
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
    out = {"widget": WIDGET, "days": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=UA)
        try:
            pg.goto(WIDGET, wait_until="load", timeout=60000)  # NOT networkidle
        except Exception as e:
            out["goto_error"] = str(e)[:150]
        try:
            pg.wait_for_selector("text=Today", timeout=30000)
            out["shell_rendered"] = True
        except Exception as e:
            out["shell_rendered"] = False
            out["shell_error"] = str(e)[:150]
        pg.wait_for_timeout(5000)
        out["title"] = pg.title()
        out["initial"] = metrics(pg.inner_text("body"))

        tabs = pg.locator("button", has_text=re.compile(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b"))
        try:
            out["day_tabs_found"] = tabs.count()
        except Exception:
            out["day_tabs_found"] = 0
        for i in range(min(out["day_tabs_found"], 7)):
            try:
                tabs.nth(i).click(timeout=8000)
                pg.wait_for_timeout(3500)
                body = pg.inner_text("body")
                m = metrics(body)
                m["snippet"] = re.sub(r"\s+", " ", body)[:110]
                out["days"].append(m)
            except Exception as e:
                out["days"].append({"error": str(e)[:110]})
        b.close()

    total = out.get("initial", {}).get("times", 0) + sum(d.get("times", 0) for d in out["days"])
    challenged = out.get("initial", {}).get("challenge") or any(d.get("challenge") for d in out["days"])
    if challenged:
        verdict = "FAIL - challenge/block on datacenter IP. Drop the scraper; pursue the official Mindbody API."
    elif total >= 10:
        verdict = f"PASS - {total} class-times rendered headless on a datacenter IP, no block. Scraper is viable."
    else:
        verdict = f"INCONCLUSIVE - no block, but only {total} class-times rendered. Metrics below (send me the JSON)."
    print("=" * 70)
    print("VERDICT:", verdict)
    print("=" * 70)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    sys.exit(main())
