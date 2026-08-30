#!/usr/bin/env python3
"""
pull.py — PRODUCTION: refresh every teacher's timetable from the studio feeds.

How each studio is pulled is declared in data/schedule.json, in a "feed" block
on each studio — never in this file:
    {"type": "momence",  "host": 34431}                  -> clean JSON API
    {"type": "healcode", "page": "https://.../timetable"} -> rendered widget
    {"type": "manual", ...}                               -> skipped, left as-is

For every studio it can read, it fetches the live schedule, normalizes it
(pull/normalizers.py), and merge.py folds the result into schedule.json —
alias-matched, substitute-flagged, with partial-failure safety (a feed that
fails or is "manual" leaves that studio's existing classes untouched). Then it
rebuilds the profile pages. The workflow opens a Pull Request, so nothing goes
live until a human reviews and merges.

Adding a studio to the automation = one registry entry with a feed block.
Belongs in the REAL site repo (with build_profiles.py, templates/, data/, *.html).
"""
import json, sys, re, os, datetime, subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalizers as N
import merge as M

ROOT = Path(__file__).resolve().parent.parent
SCHED = ROOT / "data" / "schedule.json"
ANOM = Path(__file__).resolve().parent / "_anomalies.md"
STATE = Path(__file__).resolve().parent / "_feed_state.json"
DARK_ESCALATE = 3  # consecutive failed runs before a feed is called "likely broken", not a blip
# A rolling fortnight, not a week. Seven days catches every *weekly* slot once, but
# silently misses anyone who teaches fortnightly, rotates, or is simply rostered
# further out — they render as an empty timetable, which reads as "no classes"
# rather than "outside our window" (Emma Strembickyj, 16 Aug: her only two classes
# were on 24 and 26 Aug). merge dedups on (studio, day, start, class), so a weekly
# class seen twice in the window still collapses to one row.
FORWARD_DAYS = 14
SESSION_TYPES = ["course-class", "fitness", "retreat", "special-event", "special-event-new"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; YIM-timetable/1.0)"}
MB_API_KEY = os.environ.get("MINDBODY_API_KEY", "")   # GitHub Actions secret
MB_BASE = "https://api.mindbodyonline.com/public/v6"

# Mindbody bw-widget ids for the direct load_markup endpoint (no browser needed).
# studio_id -> widget id. A feed may also carry its own "widget" to override this.
HEALCODE_WIDGETS = {"within-south-yarra": "188058"}

# go.mindbody branded-web V2 widget slugs (Warrior One). studio_id -> slug.
GOMINDBODY_SLUGS = {"warrior-one-brighton": "751447bfa", "warrior-one-mordialloc": "751457bfa"}


def shared_path_diagnosis(failed, covered, studios):
    """If every failing feed uses one platform adapter and *no* feed on that
    adapter succeeded, the adapter is broken — not the studios. Three separate
    'studio down' lines hide that; one line names the actual fix.

    (This is exactly what happened from 27 Jul 2026: Warrior One x2 and Happy
    Melon all went dark on the same run, and all three — and only those three —
    are `gomindbody`.)"""
    def ftype(sid):
        return (studios.get(sid, {}).get("feed") or {}).get("type")
    failed_types = {ftype(sid) for sid, *_ in failed}
    if len(failed_types) != 1:
        return None
    t = failed_types.pop()
    if not t or any(ftype(sid) == t for sid in covered):
        return None  # some feed on this adapter still works — so it's the studio
    return t


def write_anomalies(failed, missing, unknown_studios, recovered,
                    no_schedule=(), broken_adapter=None):
    """Write a human-readable anomaly report for the workflow to raise as an issue.
    Anomalies never block publishing — clean studios still go live; this is a heads-up.
    `failed`  = list of (sid, err, dark_runs, since); escalates at DARK_ESCALATE+ runs.
    `missing` = registered teachers who had classes last run but zero this run at a
                covered studio (a real disappearance — NOT the ~150 non-profiled teachers
                in the feeds, which are normal and never flagged)."""
    lines = []
    escalated = [f for f in failed if f[2] >= DARK_ESCALATE]
    blips = [f for f in failed if f[2] < DARK_ESCALATE]
    if broken_adapter:
        lines.append(
            f"**🔴 The `{broken_adapter}` adapter is down, not the studios.** Every feed that "
            f"failed this run uses `{broken_adapter}`, and no `{broken_adapter}` feed succeeded. "
            "Fix (or replace) that one code path and all of them come back together — "
            "chasing the studios individually will not find anything.")
        lines.append("")
    if escalated:
        lines.append(f"**🔴 Feeds DOWN {DARK_ESCALATE}+ runs — likely broken, not a blip. "
                     "Fix the scrape, switch the studio to `manual`, or move it to the official API:**")
        for sid, err, runs, since in escalated:
            lines.append(f"- `{sid}` — down **{runs} runs** since {since}. Last error: {err}")
    if blips:
        lines.append("")
        lines.append("**🟡 Feed down this run** — kept last-good data; only a concern if it repeats:")
        for sid, err, runs, since in blips:
            lines.append(f"- `{sid}` — {err}  _(run {runs} of the streak)_")
    if recovered:
        lines.append("")
        lines.append("**🟢 Recovered** — pulling cleanly again:")
        for sid, since in recovered:
            lines.append(f"- `{sid}` — was down since {since}")
    if missing:
        lines.append("")
        lines.append("**Profiled teacher dropped from the feed** — had classes last run, zero this "
                     "run at a studio that pulled cleanly. Likely their name changed in the studio's "
                     "system (update the alias in `schedule.json`) or they stopped teaching there:")
        for name in missing:
            lines.append(f"- {name}")
    if no_schedule:
        lines.append("")
        lines.append("**Registered teacher with an empty timetable everywhere** — her page is live "
                     f"but shows no classes at all. Either she is rostered beyond the {FORWARD_DAYS}-day "
                     "window, teaches somewhere YiM does not ingest yet (ask her where else she "
                     "teaches), or her name is spelled differently in the feed and needs an alias:")
        for name in no_schedule:
            lines.append(f"- {name}")
    if unknown_studios:
        lines.append("")
        lines.append("**Rows for unknown studio ids** — add them to the studios registry:")
        for sid, count in sorted(unknown_studios.items()):
            lines.append(f"- `{sid}` — {count} row(s)")
    if lines:
        header = ("The automated timetable pull flagged items needing a look. Schedules that "
                  "pulled cleanly were published as normal; nothing below blocked them.\n\n")
        ANOM.write_text(header + "\n".join(lines) + "\n")
        print(f"\n⚠ anomalies written to {ANOM.name} — the workflow will raise/append a GitHub issue.")
    else:
        print("\n✓ clean run — no anomalies.")


def momence_fetch(host):
    base = f"https://readonly-api.momence.com/host-plugins/host/{host}/host-schedule/sessions"
    nowdt = datetime.datetime.now(datetime.timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    frm = nowdt.strftime(fmt)
    to = (nowdt + datetime.timedelta(days=FORWARD_DAYS)).strftime(fmt)
    payload, page = [], 0
    while True:
        q = [("sessionTypes[]", t) for t in SESSION_TYPES] + \
            [("fromDate", frm), ("toDate", to), ("pageSize", "50"), ("page", str(page)), ("timeZone", "UTC")]
        req = Request(base + "?" + urlencode(q), headers=UA)
        d = json.loads(urlopen(req, timeout=30).read().decode("utf-8"))
        payload += d.get("payload", [])
        total = d.get("pagination", {}).get("totalCount", len(payload))
        page += 1
        if page * 50 >= total or page > 40:
            break
    return payload


def mindbody_fetch(site_id):
    """Mindbody Public API v6 GetClasses. Needs only Api-Key + SiteId once a
    studio has activated our key — no per-studio login. Paginated; local times."""
    now = datetime.datetime.now()
    frm = now.date().isoformat()
    to = (now + datetime.timedelta(days=FORWARD_DAYS)).date().isoformat()
    headers = {**UA, "Api-Key": MB_API_KEY, "SiteId": str(site_id)}
    out, offset = [], 0
    while True:
        q = urlencode({"StartDateTime": frm, "EndDateTime": to, "Limit": 100, "Offset": offset})
        req = Request(f"{MB_BASE}/class/classes?{q}", headers=headers)
        d = json.loads(urlopen(req, timeout=30).read().decode("utf-8"))
        batch = d.get("Classes", [])
        out += batch
        total = (d.get("PaginationResponse") or {}).get("TotalResults", len(out))
        offset += 100
        if len(batch) < 100 or offset >= total or offset > 4000:
            break
    return out


def healcode_fetch(feed, sid):
    """Direct load_markup GET — no browser. Returns the week's bw-session HTML.
    feed = {"type":"healcode","widget":"188058", ...}. The bw-widget returns 7 days
    from start_date; datetimes in the markup are already Melbourne-local."""
    wid = feed.get("widget") or HEALCODE_WIDGETS.get(sid)
    if not wid:
        raise RuntimeError(f"no healcode widget id for '{sid}'")
    start = datetime.datetime.now(ZoneInfo("Australia/Melbourne")).strftime("%Y-%m-%d")
    url = (f"https://widgets.mindbodyonline.com/widgets/schedules/{wid}"
           f"/load_markup?options[start_date]={start}")
    raw = urlopen(Request(url, headers=UA), timeout=45).read().decode("utf-8")
    try:
        data = json.loads(raw)
        return data.get("class_sessions") or data.get("contents") or raw
    except (ValueError, AttributeError):
        return raw  # response was already raw markup



def squarespace_fetch(feed, sid):
    """Plain GET of a static Squarespace page (Inndriya). No browser, no JS."""
    url = feed.get("url")
    if not url:
        raise RuntimeError(f"no squarespace url for '{sid}'")
    return urlopen(Request(url, headers=UA), timeout=45).read().decode("utf-8")

def gomindbody_fetch(feed, sid):
    """Render the go.mindbody branded-web V2 Schedules widget headless, click through
    the 7 day tabs (they're div[role=button], not <button>), and return per-day class
    data. Heavy (browser + interaction) but the only path for V2. keep-last-good and
    the 0-rows guard protect the live schedule if Mindbody changes the widget."""
    from playwright.sync_api import sync_playwright
    slug = feed.get("slug") or GOMINDBODY_SLUGS.get(sid)
    if not slug:
        raise RuntimeError(f"no gomindbody slug for '{sid}'")
    url = f"https://go.mindbodyonline.com/book/widgets/schedules/view/{slug}/schedule"
    extract = (
        "() => {"
        "const dh=(document.body.innerText.match(/(Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day, [A-Z][a-z]+ \\d+/)||[''])[0];"
        "const timeRe=/^\\d{1,2}:\\d{2}\\s?(AM|PM)$/i;"
        "const SKIP=new Set(['SCRIPT','STYLE','NOSCRIPT','SVG','PATH']);"
        "const leavesOf=el=>{const out=[];const w=n=>{if(n.nodeType===3){const s=n.textContent.trim();if(s)out.push(s);}else if(n.nodeType===1&&!SKIP.has((n.tagName||'').toUpperCase())){n.childNodes.forEach(w);}};w(el);return out;};"
        "const timeEls=[...document.querySelectorAll('*')].filter(e=>{const own=[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent.trim()).join('');return timeRe.test(own);});"
        "const seen=new Set(),cards=[];"
        "for(const te of timeEls){let c=te;for(let i=0;i<6&&c;i++){if(/BOOK MY MAT|Waitlist|(^|\\s)Book(\\s|$)/i.test(c.textContent||''))break;c=c.parentElement;}"
        # The .filter(s=>s.length<=90) below is the fix for a silent three-studio
        # outage. Diagnosed 31 Aug 2026 by running this extractor against the live
        # widget in a real browser.
        #
        # Every nightly run had been logging `[gomindbody:751447bfa] days=7
        # sample=[]` — seven day tabs found and clicked, zero cards returned — and
        # the workflow correctly concluded "the adapter is broken, not the studios".
        # Brighton, Mordialloc and Happy Melon were all dark and Warrior One's rows
        # had gone 13 days without a refresh.
        #
        # The cause was not the selectors. The time-element test still matched and
        # the card container was still found two levels up. Mindbody started
        # rendering each class's full description into the DOM behind "Show Details"
        # instead of fetching it on click, so a card's leaves grew from ~95
        # characters to 375-567 — and every card was discarded by the 200-char guard
        # below. One number, three studios, no error raised anywhere.
        #
        # So drop the prose, not the card. Every field this pipeline wants is short:
        # a time, a duration, a class name, a teacher, a studio. Nothing legitimate
        # comes near 90 characters. Descriptions all exceed it except their closing
        # line ("Leave feeling grounded nourished and connected."), which survives
        # harmlessly — gomindbody_rows takes core[0] and core[1] for class and
        # teacher, so a trailing leaf lands at core[2] and is ignored.
        #
        # The 200-char cap stays. Its job is rejecting a container that swallowed
        # more than one card, and it still does that: measured against live Brighton
        # markup the longest filtered card is 146 characters, so a two-card sweep is
        # still well over the line.
        #
        # If this returns zero again, do NOT start by tuning selectors. Open the
        # widget in a browser, run this extractor by hand, and print leaf lengths.
        "if(!c)continue;const lv=leavesOf(c).filter(s=>s.length<=90);"
        "if(lv.join(' ').length>200)continue;"
        "const sig=lv.join('|');if(seen.has(sig))continue;seen.add(sig);cards.push(lv);}"
        "return {date:dh,cards};}"
    )
    days = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=UA["User-Agent"])
        pg.goto(url, wait_until="load", timeout=60000)
        pg.wait_for_selector("text=Today", timeout=30000)
        pg.wait_for_timeout(4000)
        tabs = pg.locator("[role=button]").filter(
            has_text=re.compile(r"^(Today|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s*\d{1,2}$", re.I))
        try:
            ntab = tabs.count()
        except Exception:
            ntab = 0
        for i in range(min(ntab, 7)):
            try:
                tabs.nth(i).click(timeout=8000)
                pg.wait_for_timeout(2500)
                days.append(pg.evaluate(extract))
            except Exception:
                continue
        b.close()
    samp = next((d["cards"][:2] for d in days if d.get("cards")), [])
    print(f"    [gomindbody:{slug}] days={len(days)} sample={json.dumps(samp)[:400]}")
    return days


def main():
    if ANOM.exists():
        ANOM.unlink()  # start clean; only present if this run finds something
    schedule = json.loads(SCHED.read_text())
    rows, covered, failed = [], [], []

    for sid, meta in schedule["studios"].items():
        feed = meta.get("feed", {})
        ftype = feed.get("type")
        if ftype not in ("momence", "mindbody", "healcode", "gomindbody", "squarespace"):
            continue  # manual / unconfigured — left untouched, not expected to auto-pull
        try:
            if ftype == "momence":
                r = N.momence_rows(momence_fetch(feed["host"]), sid, feed.get("location"))
            elif ftype == "mindbody":
                r = N.mindbody_rows(mindbody_fetch(feed["site_id"]), sid, feed.get("location"))
            elif ftype == "squarespace":
                r = N.squarespace_rows(squarespace_fetch(feed, sid), sid)
            elif ftype == "healcode":
                r = N.healcode_rows(healcode_fetch(feed, sid), sid)
            else:  # gomindbody
                r = N.gomindbody_rows(gomindbody_fetch(feed, sid), sid)
            need = int(feed.get("min_rows", 1))
            if len(r) < need:
                # A feed that responds with nothing — or suspiciously little (a
                # half-rendered widget) — is a FAILURE, never "the studio shrank".
                # Otherwise a block, challenge, or partial render would silently
                # WIPE or THIN a real schedule. Tune per-feed via "min_rows".
                raise RuntimeError(
                    f"feed returned {len(r)} sessions (< min_rows {need}) — "
                    "block, markup change, or partial render?")
            rows += r
            covered.append(sid)
            print(f"  {sid}: {len(r)} rows [{ftype}]")
        except Exception as e:
            failed.append((sid, str(e)))
            print(f"  {sid}: FAILED — {e}  (kept last-good)")

    # ---- feed-failure streak tracking (dark-day escalation) ----
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    today = datetime.date.today().isoformat()
    new_state, recovered = {}, []
    for sid, _err in failed:
        prev = state.get(sid, {})
        new_state[sid] = {"dark_runs": prev.get("dark_runs", 0) + 1,
                          "since": prev.get("since", today)}
    for sid in covered:
        if sid in state:                       # was failing, pulled cleanly now
            recovered.append((sid, state[sid].get("since", "?")))
    STATE.write_text(json.dumps(new_state, indent=2) + "\n")
    failed_detail = [(sid, err, new_state[sid]["dark_runs"], new_state[sid]["since"])
                     for sid, err in failed]

    broken_adapter = shared_path_diagnosis(failed_detail, covered, schedule["studios"])
    if broken_adapter:
        print(f"\n⚠ every failed feed is '{broken_adapter}' and none succeeded — "
              "the adapter is broken, not the studios.")

    if not covered:
        print("No studios pulled successfully; leaving schedule.json untouched.")
        write_anomalies(failed_detail, [], {}, recovered, broken_adapter=broken_adapter)
        return

    # count each profiled teacher's classes AT COVERED STUDIOS, before the merge overwrites
    covset = set(covered)
    def _counts(sched):
        return {n: sum(1 for c in t.get("classes", []) if c.get("studio") in covset)
                for n, t in sched.get("teachers", {}).items()}
    old_counts = _counts(schedule)

    merged, report = M.merge(schedule, rows, covered)
    SCHED.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    print(f"\nmerged {report['matched']} rows; covered: {', '.join(covered)}")

    new_counts = _counts(merged)
    # only a REAL disappearance: had classes at a covered studio last run, none now.
    missing = sorted(n for n in old_counts if old_counts[n] > 0 and new_counts.get(n, 0) == 0)

    # Distinct from `missing`: a teacher who has never had a class at any studio,
    # covered or not. She never "disappeared", so the check above can't see her —
    # her page has simply been publishing an empty timetable, possibly for weeks.
    no_schedule = sorted(n for n, t in merged.get("teachers", {}).items()
                         if not t.get("classes"))

    write_anomalies(failed_detail, missing, report["unknown_studios"], recovered,
                    no_schedule=no_schedule, broken_adapter=broken_adapter)

    subprocess.run([sys.executable, str(ROOT / "build_profiles.py")], check=True, cwd=str(ROOT))
    print("profiles rebuilt.")


if __name__ == "__main__":
    main()
