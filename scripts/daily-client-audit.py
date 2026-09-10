#!/usr/bin/env python3
"""Daily 24h query digest for ALL Pi-hole clients.
Categorizes domains queried in the last 24h by keyword/regex, flags anything
gaming/porn/gambling-adjacent that ISN'T already blocked by an existing
Pi-hole rule or adlist, per client, so new sites get caught before they
become a habit.

Run on the Pi itself (reads pihole-FTL.db + gravity.db directly).
"""
import re
import sqlite3
import time

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


def main():
    db = sqlite3.connect("file:/etc/pihole/pihole-FTL.db?mode=ro", uri=True, timeout=10)
    cutoff = time.time() - LOOKBACK_HOURS * 3600

    clients = db.execute(
        "SELECT id, ip, name FROM client_by_id ORDER BY ip"
    ).fetchall()

    BLOCKED_STATUSES = {1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16}

    any_output = False

    for cid, ip, name in clients:
        rows = db.execute(
            """
            SELECT d.domain, q.status, COUNT(*) n
            FROM query_storage q JOIN domain_by_id d ON q.domain = d.id
            WHERE q.client = ? AND q.timestamp >= ?
            GROUP BY d.domain
            ORDER BY n DESC
            """,
            (cid, cutoff),
        ).fetchall()

        if not rows:
            continue

        flagged_allowed = {}
        flagged_blocked = {}

        for domain, status, n in rows:
            cats = categorize(domain)
            if not cats:
                continue
            is_blocked = status in BLOCKED_STATUSES
            target = flagged_blocked if is_blocked else flagged_allowed
            for cat in cats:
                target.setdefault(cat, []).append((domain, n))

        if not flagged_allowed and not flagged_blocked:
            continue

        any_output = True
        label = name or ip
        print(f"=== {label} ({ip}) — last {LOOKBACK_HOURS}h — {len(rows)} distinct domains ===\n")

        if flagged_allowed:
            print("NOT BLOCKED — needs review:")
            for cat, items in sorted(flagged_allowed.items()):
                print(f"  [{cat}] ({len(items)} domains)")
                for dom, n in sorted(items, key=lambda x: -x[1])[:15]:
                    print(f"    {n:4d}  {dom}")
        else:
            print("Nothing flagged as unblocked in any watched category.")

        if flagged_blocked:
            print("\nAlready blocked (context only):")
            for cat, items in sorted(flagged_blocked.items()):
                doms = ", ".join(sorted({d for d, _ in items}))[:200]
                print(f"  [{cat}]: {doms}")
        print()

    if not any_output:
        print("No flagged activity across any client in the last 24h.")


if __name__ == "__main__":
    main()
