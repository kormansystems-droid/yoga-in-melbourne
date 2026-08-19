#!/usr/bin/env python3
"""
pull_events.py — refresh data/events.json from the studio feeds and event pages.

Deliberately a SEPARATE entry point from pull.py. The nightly class refresh is
load-bearing and runs unattended at 5am; events are new and their scraper is the
brittle part. Keeping them apart means an events failure can never take the
timetable down with it. Wire it into pull.py only once it has run clean for a
few days.

    python3 pull/pull_events.py             # PROPOSE only — writes no published data
    python3 pull/pull_events.py --publish    # write data/events.json (needs a human yes)

**Events are never published without Mark seeing them first** (his instruction,
18 Aug 2026). A pull cannot change what is on the site: by default it writes only
`_events_proposed.json` and a readable `_events_proposed.md` summarising what is
new, what changed and what is about to expire. Publishing is a separate, explicit
act. This is not a lint rule — the flag is the gate, so a scheduled run or a
mistyped command cannot put an unreviewed event in front of a reader.

Sources, in the order of how much they can be trusted:

  momence  — events sit in the same endpoint as classes, tagged by `type`.
             Reliable, structured, carries price and booking link.
  page     — a studio's own event page, scraped. Within publishes workshops ONLY
             this way (its booking widget was checked 18 Aug 2026 and returns
             classes and nothing else). Hand-typed prose; expect it to break.
  manual   — entered by hand, never overwritten by any pull.

A configured event page that yields nothing is reported loudly. Silence is the
failure mode that matters here: the homepage events section had already decayed
from 7 cards to 3 by expiry alone, with nothing refilling it.
"""
import argparse, datetime, json, re, sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import events as EV

ROOT = Path(__file__).resolve().parent.parent
SCHED = ROOT / "data" / "schedule.json"
EVENTS = ROOT / "data" / "events.json"
ANOM = Path(__file__).resolve().parent / "_event_anomalies.md"
PROPOSED_JSON = Path(__file__).resolve().parent / "_events_proposed.json"
PROPOSED_MD = Path(__file__).resolve().parent / "_events_proposed.md"
ACTIONABLE = Path(__file__).resolve().parent / "_events_actionable"

UA = {"User-Agent": "Mozilla/5.0 (compatible; YIM-events/1.0)"}
FORWARD_DAYS = 180          # events are booked months out; classes are not
SESSION_TYPES = ["course-class", "fitness", "retreat", "special-event",
                 "special-event-new", "course"]


def momence_fetch(host):
    base = f"https://readonly-api.momence.com/host-plugins/host/{host}/host-schedule/sessions"
    now = datetime.datetime.now(datetime.timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    payload, page = [], 0
    while True:
        q = [("sessionTypes[]", t) for t in SESSION_TYPES] + [
            ("fromDate", now.strftime(fmt)),
            ("toDate", (now + datetime.timedelta(days=FORWARD_DAYS)).strftime(fmt)),
            ("pageSize", "50"), ("page", str(page)), ("timeZone", "UTC")]
        d = json.loads(urlopen(Request(base + "?" + urlencode(q), headers=UA),
                               timeout=30).read().decode("utf-8"))
        payload += d.get("payload", [])
        total = d.get("pagination", {}).get("totalCount", len(payload))
        page += 1
        if page * 50 >= total or page > 40:
            break
    return payload


def page_text(url):
    """A studio event page as plain text. <article> where the builder gives us
    one (Squarespace does), else the whole document."""
    html = urlopen(Request(url, headers=UA), timeout=30).read().decode("utf-8", "replace")
    art = re.search(r"<article[\s\S]*?</article>", html, re.I)
    src = art.group(0) if art else html
    src = re.sub(r"<script[\s\S]*?</script>", " ", src, flags=re.I)
    src = re.sub(r"<style[\s\S]*?</style>", " ", src, flags=re.I)
    txt = re.sub(r"<[^>]+>", "\n", src)
    for a, b in [("&nbsp;", " "), ("&amp;", "&"), ("&#8217;", "'"), ("&rsquo;", "'"),
                 ("&#8212;", "—"), ("&mdash;", "—"), ("&#8211;", "–"), ("&ndash;", "–")]:
        txt = txt.replace(a, b)
    txt = re.sub(r"[ \t]+", " ", txt)
    return re.sub(r"\n\s*\n+", "\n", txt).strip()


def _fmt(e):
    when = (e.get("starts") or "")[:10] or "date unknown"
    price = e.get("price")
    price = "free" if price == 0 else (f"${price:g}" if price is not None else "price n/a")
    who = f" · {e['teacher']}" if e.get("teacher") else ""
    return f"**{e.get('title','(untitled)')}** — {when} · {e.get('studio') or 'studio n/a'}{who} · {price}"


def write_proposal(before, after, problems):
    """A diff a human can read on a phone. Everything a pull wants to change to
    the public events list, and nothing applied."""
    old = {e["id"]: e for e in before}
    new = {e["id"]: e for e in after}
    added = [new[i] for i in new if i not in old]
    removed = [old[i] for i in old if i not in new]
    changed = [(old[i], new[i]) for i in new
               if i in old and {k: old[i].get(k) for k in ("title", "starts", "price", "url")}
               != {k: new[i].get(k) for k in ("title", "starts", "price", "url")}]

    L = ["# Events — proposed changes", "",
         f"{len(added)} new · {len(changed)} changed · {len(removed)} dropped · "
         f"{len(after)} live after this.", "",
         "Nothing here is on the site. Reply with what to keep and I will publish it.", ""]
    if added:
        L += ["## New", ""] + [f"- {_fmt(e)}  \n  {e.get('url','')}" for e in added] + [""]
    if changed:
        L += ["## Changed", ""]
        for o, n in changed:
            bits = [f"{k}: {o.get(k)!r} → {n.get(k)!r}" for k in ("title", "starts", "price", "url")
                    if o.get(k) != n.get(k)]
            L.append(f"- **{n.get('title')}** — " + "; ".join(bits))
        L.append("")
    if removed:
        L += ["## Dropped (past, or no longer in the feed)", ""] + \
             [f"- {_fmt(e)}" for e in removed] + [""]
    if problems:
        L += ["## Needs a human", ""] + [f"- {p}" for p in problems] + [""]
    PROPOSED_MD.write_text("\n".join(L), encoding="utf-8")

    # A weekly run that found nothing new must not raise an issue — a
    # notification that fires every week regardless stops being read, and then
    # the one that matters is missed too. Dropped-only diffs are expiry doing its
    # job and need no decision.
    if added or changed or problems:
        ACTIONABLE.write_text(
            f"{len(added)} new, {len(changed)} changed, {len(problems)} needing a human\n",
            encoding="utf-8")
    elif ACTIONABLE.exists():
        ACTIONABLE.unlink()
    PROPOSED_JSON.write_text(json.dumps({"events": after}, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true",
                    help="write data/events.json. Only after Mark has reviewed the proposal.")
    a = ap.parse_args()

    schedule = json.loads(SCHED.read_text(encoding="utf-8"))
    studios = schedule["studios"]
    existing = EV.load(EVENTS)

    fresh, covered, problems = [], set(), []

    # --- Momence hosts ------------------------------------------------------
    hosts = {}
    for sid, meta in studios.items():
        feed = meta.get("feed") or {}
        if feed.get("type") == "momence":
            hosts.setdefault(feed["host"], []).append((sid, feed.get("location")))
    momence_ok = bool(hosts)
    for host, targets in sorted(hosts.items()):
        try:
            payload = momence_fetch(host)
        except Exception as e:                                   # noqa: BLE001
            problems.append(f"momence host {host} failed: {e}")
            momence_ok = False
            continue
        for sid, location in targets:
            got = EV.momence_events(payload, sid, location)
            fresh += got
            print(f"  momence {sid:28} {len(got)} event(s)")
    if momence_ok:
        covered.add("momence")

    # --- Studio event pages -------------------------------------------------
    pages = [(sid, p) for sid, meta in studios.items()
             for p in (meta.get("event_pages") or [])]
    page_ok = bool(pages)
    for sid, p in pages:
        url = p["url"] if isinstance(p, dict) else p
        cfg = p if isinstance(p, dict) else {}
        try:
            txt = page_text(url)
        except Exception as e:                                   # noqa: BLE001
            problems.append(f"event page {url} unreachable: {e}")
            page_ok = False
            continue
        if cfg.get("list"):
            # An index page listing many events (Warrior One's /workshops/).
            got, probs = EV.page_events(
                txt, sid, url, kind=cfg.get("kind", "workshop"),
                locations=cfg.get("locations"), expect=cfg.get("expect"))
            fresh += got
            problems += probs
            for e in got:
                print(f"  list    {e['studio']:28} {e['title'][:40]} — {e['starts'][:10]}")
            if not got:
                problems.append(f"index page {url} loaded but no events could be read "
                                f"— the studio has changed its layout")
                print(f"  list    {sid:28} NO EVENTS PARSED — {url}")
            continue

        ev = EV.page_event(txt, sid, url, title=cfg.get("title"),
                           kind=cfg.get("kind", "workshop"))
        if ev:
            fresh.append(ev)
            print(f"  page    {sid:28} {ev['title'][:40]} — {ev['starts'][:10]}")
        else:
            # The page loaded and we could not find a date in it. That is a
            # format change, not an empty page — say so.
            problems.append(f"event page {url} loaded but no date could be read "
                            f"— the studio has changed its wording; needs a manual entry")
            print(f"  page    {sid:28} NO DATE PARSED — {url}")
    if page_ok:
        covered.add("page")

    merged = EV.merge_events(existing, fresh, covered)
    print(f"\n{len(merged)} events "
          f"({sum(1 for e in merged if e.get('source')=='manual')} manual, "
          f"{sum(1 for e in merged if e.get('source')=='momence')} momence, "
          f"{sum(1 for e in merged if e.get('source')=='page')} page)")

    if problems:
        ANOM.write_text("The events refresh needs a look:\n\n"
                        + "\n".join(f"- {p}" for p in problems) + "\n")
        print("\n⚠ " + "\n⚠ ".join(problems))

    if a.publish:
        EV.save(EVENTS, merged)
        print(f"published {EVENTS.relative_to(ROOT)}")
        return

    write_proposal(existing, merged, problems)
    print(f"\nproposal written to {PROPOSED_MD.name} and {PROPOSED_JSON.name}. "
          f"Nothing published — run with --publish once Mark has said yes.")


if __name__ == "__main__":
    main()
