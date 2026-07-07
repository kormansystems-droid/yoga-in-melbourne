"""
probe_gomindbody.py — decisive test for the Warrior One / Happy Melon scrape.

Question it answers: does go.mindbodyonline.com serve its Schedules V2 widget to a
HEADLESS Chromium running on a GitHub Actions (datacenter) IP?

PASS = the widget renders and day-switching yields classes -> the scraper is a
       straightforward build (load widget, click 7 day tabs, scrape each day).
FAIL = challenge page / empty render -> drop the scraper, pursue official
       Mindbody API via the studio relationship.

Run in GitHub Actions (see probe.yml). Prints a verdict; exits 0 either way so
the log is always readable.
"""
import json, re, sys

WIDGET = "https://go.mindbodyonline.com/book/widgets/schedules/view/751447bfa/schedule"  # Warrior One Brighton

def txt_metrics(text):
    return {
        "bytes": len(text),
        "times": len(re.findall(r"\d{1,2}:\d{2}\s?(?:am|pm)", text, re.I)),
        "day_header": bool(re.search(r"(Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day, ", text)),
        "challenge": bool(re.search(r"cloudflare|captcha|are you a human|access denied|blocked", text, re.I)),
    }

def main():
    from playwright.sync_api import sync_playwright
    out = {"widget": WIDGET, "days": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"))
        try:
            pg.goto(WIDGET, wait_until="networkidle", timeout=60000)
        except Exception as e:
            out["goto_error"] = str(e)[:200]
        pg.wait_for_timeout(8000)
        out["initial"] = txt_metrics(pg.inner_text("body"))
        out["title"] = pg.title()

        # click through the day tabs (buttons whose text is like "Wed 8")
        tabs = pg.locator("button", has_text=re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s*\d{1,2}$"))
        n = min(tabs.count(), 6)
        out["day_tabs_found"] = tabs.count()
        for i in range(n):
            try:
                tabs.nth(i).click()
                pg.wait_for_timeout(3500)
                m = txt_metrics(pg.inner_text("body"))
                snip = re.sub(r"\s+", " ", pg.inner_text("body"))[:140]
                out["days"].append({"tab": i, **m, "snippet": snip})
            except Exception as e:
                out["days"].append({"tab": i, "error": str(e)[:150]})
        b.close()

    total_times = sum(d.get("times", 0) for d in out["days"])
    challenged = out["initial"]["challenge"] or any(d.get("challenge") for d in out["days"])
    if challenged:
        verdict = "FAIL — challenge/block page detected on a datacenter IP. Drop the scraper; go the official-API route."
    elif total_times >= 10 and out["day_tabs_found"] >= 5:
        verdict = "PASS — widget renders headless on a datacenter IP. The scraper is a viable build."
    else:
        verdict = "INCONCLUSIVE — no explicit block, but little/no schedule rendered. Inspect the metrics below."
    print("=" * 70)
    print("VERDICT:", verdict)
    print("=" * 70)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    sys.exit(main())
