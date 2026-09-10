#!/usr/bin/env python3
"""Daily 24h query digest for a specific Pi-hole client (default: iPad .72).
Categorizes domains queried in the last 24h by keyword/regex, flags anything
gaming/porn/gambling-adjacent that ISN'T already blocked by an existing
Pi-hole rule or adlist, so new sites get caught before they become a habit.

Run on the Pi itself (reads pihole-FTL.db + gravity.db directly).
"""
import re
import sqlite3
import time

CLIENT_IP = "192.168.1.72"
LOOKBACK_HOURS = 24

CATEGORIES = {
    "gaming": [
        r"game", r"play", r"crazy", r"yandex", r"poki\b", r"kongregate",
        r"miniclip", r"itch\.io", r"unity3d", r"webgl", r"roblox",
        r"minecraft", r"steam", r"epicgames", r"friv", r"\by8\.",
        r"coolmath", r"addictinggames", r"gamepix", r"twoplayergames",
        r"lagged", r"silvergames", r"playgama", r"gamedistribution",
        r"onlinegames", r"kizi", r"gamejolt", r"armorgames", r"agame",
        r"newgrounds", r"gogy", r"gamesgames", r"bloxd",
    ],
    "porn_nsfw": [
        r"porn", r"xxx", r"xvideos", r"xnxx", r"onlyfans", r"redtube",
        r"pornhub", r"xhamster", r"chaturbate", r"livejasmin", r"brazzers",
        r"nsfw", r"hentai", r"stripchat",
    ],
    "gambling": [
        r"bet\d", r"casino", r"poker", r"slots?\b", r"betway", r"betfair",
        r"blaze\.", r"betano", r"gambling", r"wager",
    ],
    "social": [
        r"tiktok", r"instagram", r"facebook", r"snapchat", r"reddit",
        r"twitter", r"\bx\.com", r"discord", r"pinterest",
    ],
    "vpn_proxy": [
        r"vpn", r"proxy", r"tunnel", r"nordvpn", r"expressvpn", r"tor-",
    ],
}

def categorize(domain: str):
    d = domain.lower()
    hits = []
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, d):
                hits.append(cat)
                break
    return hits


def already_blocked(cur_ftl, domain: str) -> bool:
    """0.0.0.0 / NXDOMAIN style check isn't available from FTL alone reliably,
    so we treat 'blocked' as: query had status indicating a block.
    FTL status codes: 1=blocked (gravity), 4=blocked (regex), 5=blocked (exact
    deny), 9=blocked (special domain), 10=blocked (deny, pre-fetch),
    11=blocked (adlist)."""
    return True  # placeholder, unused — see main() which reads status directly


def main():
    db = sqlite3.connect("file:/etc/pihole/pihole-FTL.db?mode=ro", uri=True, timeout=10)
    cid = db.execute("SELECT id FROM client_by_id WHERE ip = ?", (CLIENT_IP,)).fetchone()
    if not cid:
        print(f"No client found for {CLIENT_IP} — nothing to report.")
        return
    cid = cid[0]

    cutoff = time.time() - LOOKBACK_HOURS * 3600
    rows = db.execute(
        """
        SELECT d.domain, q.status, COUNT(*) n, MIN(q.timestamp), MAX(q.timestamp)
        FROM query_storage q JOIN domain_by_id d ON q.domain = d.id
        WHERE q.client = ? AND q.timestamp >= ?
        GROUP BY d.domain
        ORDER BY n DESC
        """,
        (cid, cutoff),
    ).fetchall()

    BLOCKED_STATUSES = {1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16}

    print(f"=== {CLIENT_IP} — last {LOOKBACK_HOURS}h — {len(rows)} distinct domains ===\n")

    flagged_allowed = {}   # category -> list of (domain, n)
    flagged_blocked = {}   # already blocked, for context

    for domain, status, n, mn, mx in rows:
        cats = categorize(domain)
        if not cats:
            continue
        is_blocked = status in BLOCKED_STATUSES
        target = flagged_blocked if is_blocked else flagged_allowed
        for cat in cats:
            target.setdefault(cat, []).append((domain, n))

    if flagged_allowed:
        print("### NOT BLOCKED — needs review ###")
        for cat, items in sorted(flagged_allowed.items()):
            print(f"\n[{cat}] ({len(items)} domains)")
            for dom, n in sorted(items, key=lambda x: -x[1])[:15]:
                print(f"  {n:4d}  {dom}")
    else:
        print("Nothing flagged as unblocked in any watched category. Clean.")

    if flagged_blocked:
        print("\n### Already blocked (for context, no action needed) ###")
        for cat, items in sorted(flagged_blocked.items()):
            doms = ", ".join(sorted({d for d, _ in items}))[:200]
            print(f"[{cat}]: {doms}")


if __name__ == "__main__":
    main()
