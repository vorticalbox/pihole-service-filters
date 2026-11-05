#!/usr/bin/env python3
"""Daily 24h query digest for ALL Pi-hole clients.
Categorizes domains queried in the last 24h by keyword/regex, flags anything
gaming/porn/gambling/story-platform traffic that ISN'T already blocked by an existing
Pi-hole rule or adlist, per client, so new sites get caught before they
become a habit.

Reads pihole-FTL.db query log (read-only). Run on the Pi as root:

    sudo python3 /opt/pihole-scripts/daily-client-audit.py
    sudo python3 /opt/pihole-scripts/daily-client-audit.py --json

Use in cron; feed stdout to an agent to suggest blocklist additions.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time

LOOKBACK_HOURS = 24

# Pi-hole FTL treats these as non-blocked (see pihole-FTL query_storage stats SQL).
ALLOWED_STATUSES = (0, 2, 3, 12, 13, 14, 17)
FORWARDED_STATUS = 2

CATEGORIES = {
    "gaming": [
        r"crazygames", r"playhop", r"playgama", r"onlinegames", r"addictinggames",
        r"coolmath", r"gamepix", r"twoplayergames", r"lagged", r"silvergames",
        r"gamedistribution", r"kizi", r"gamejolt", r"armorgames", r"\bagame\b",
        r"newgrounds", r"gogy", r"gamesgames", r"bloxd", r"poki\b", r"kongregate",
        r"miniclip", r"itch\.io", r"roblox", r"minecraft", r"epicgames", r"friv",
        r"\by8\.", r"browsergame", r"html5game", r"games\.co\.",
        r"girlsgogames", r"arcadespot", r"minigames", r"solitaire",
        r"yandex-games", r"games\.yandex", r"stgames",
        r"krunker", r"slither", r"diep\.io", r"surviv\.io",
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
        r"nordvpn", r"expressvpn", r"tor-project", r"protonvpn", r"mullvad",
    ],
    "story_platforms": [
        r"quotev", r"wattpad", r"archiveofourown", r"\bao3\.", r"fanfiction\.net",
        r"fictionpress", r"scribblehub", r"inkitt", r"royalroad", r"tapas\.io",
        r"webnovel", r"penana", r"dreamwidth", r"livejournal", r"asianfanfics",
        r"ficbook", r"squidgeworld", r"spacebattles", r"sufficientvelocity",
        r"questionablequesting", r"fiction\.live", r"commaful", r"fanfics\.me",
        r"goodnovel", r"dreame", r"moboreader", r"readnovelfull", r"novelfull",
        r"lightnovelworld", r"boxnovel", r"fanmtl",
    ],
}

# Platform / CDN noise — matched by regex but not useful blocklist candidates.
IGNORE_SUFFIXES = (
    ".googleapis.com",
    ".google.com",
    ".googleusercontent.com",
    ".gstatic.com",
    ".apple.com",
    ".icloud.com",
    ".apple-dns.net",
    ".facebook.com",
    ".fbcdn.net",
    ".bamgrid.com",
    ".akamaized.net",
    ".cloudfront.net",
    ".amazonaws.com",
    ".unity3d.com",
    ".sentry.io",
    ".intercom.io",
    ".privacymanager.io",
    ".inmobi-choice.io",
    "blocklistproject.github.io",
)

IGNORE_EXACT = {
    "play.google.com",
    "play.googleapis.com",
    "play-lh.googleusercontent.com",
    "playstoregatewayadapter-pa.googleapis.com",
    "prod-lt-playstoregatewayadapter-pa.googleapis.com",
    "catalog.gamepass.com",
    "music.yandex.ru",
    "mc.yandex.ru",
    "mc.yandex.com",
    "yandex.ru",
    "yandex.com",
}


def categorize(domain: str) -> list[str]:
    d = domain.lower()
    hits = []
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, d):
                hits.append(cat)
                break
    return hits


def ignored(domain: str) -> bool:
    d = domain.lower()
    if d in IGNORE_EXACT:
        return True
    return any(d == sfx[1:] or d.endswith(sfx) for sfx in IGNORE_SUFFIXES)


def block_suggestions(domain: str) -> list[str]:
    d = domain.lower()
    out = [d]
    if d.startswith("www."):
        apex = d[4:]
        if apex not in out:
            out.append(apex)
    else:
        www = f"www.{d}"
        if www not in out:
            out.append(www)
    return out


def load_leaks(db: sqlite3.Connection, cutoff: float, categories: set[str], min_allowed: int):
    allowed_in = ",".join(str(s) for s in ALLOWED_STATUSES)
    rows = db.execute(
        f"""
        SELECT c.ip, c.name, d.domain,
               SUM(CASE WHEN q.status IN ({allowed_in}) THEN 1 ELSE 0 END) AS allowed_n,
               SUM(CASE WHEN q.status = ? THEN 1 ELSE 0 END) AS forwarded_n,
               COUNT(*) AS total_n
        FROM query_storage q
        JOIN domain_by_id d ON q.domain = d.id
        JOIN client_by_id c ON q.client = c.id
        WHERE q.timestamp >= ?
        GROUP BY c.id, d.id
        HAVING allowed_n >= ?
        ORDER BY forwarded_n DESC, allowed_n DESC
        """,
        (FORWARDED_STATUS, cutoff, min_allowed),
    ).fetchall()

    by_client: dict[str, dict] = {}
    all_candidates: dict[str, dict] = {}

    for ip, name, domain, allowed_n, forwarded_n, total_n in rows:
        if ignored(domain):
            continue
        cats = [c for c in categorize(domain) if c in categories]
        if not cats:
            continue

        label = name or ip
        client_bucket = by_client.setdefault(
            label,
            {"ip": ip, "name": name, "leaks": []},
        )
        entry = {
            "domain": domain,
            "allowed_queries": allowed_n,
            "forwarded_queries": forwarded_n,
            "total_queries": total_n,
            "categories": cats,
            "suggest_add": block_suggestions(domain),
        }
        client_bucket["leaks"].append(entry)

        agg = all_candidates.setdefault(
            domain,
            {
                "domain": domain,
                "allowed_queries": 0,
                "forwarded_queries": 0,
                "total_queries": 0,
                "categories": set(),
                "clients": set(),
                "suggest_add": block_suggestions(domain),
            },
        )
        agg["allowed_queries"] += allowed_n
        agg["forwarded_queries"] += forwarded_n
        agg["total_queries"] += total_n
        agg["categories"].update(cats)
        agg["clients"].add(label)

    return by_client, all_candidates


def print_report(by_client: dict, all_candidates: dict, lookback: int) -> None:
    if not all_candidates:
        print(f"No category-matched leaks in the last {lookback}h.")
        return

    print(f"# Pi-hole leak audit — last {lookback}h\n")
    print("## Suggest adding to blocklists (aggregated)\n")
    for domain, info in sorted(
        all_candidates.items(),
        key=lambda x: (-x[1]["forwarded_queries"], -x[1]["allowed_queries"], x[0]),
    ):
        cats = ",".join(sorted(info["categories"]))
        clients = ", ".join(sorted(info["clients"]))
        print(
            f"- {domain}  forwarded={info['forwarded_queries']}  "
            f"allowed={info['allowed_queries']}  [{cats}]  clients: {clients}"
        )
        print(f"  suggest: {', '.join(info['suggest_add'])}")

    print("\n## Per client\n")
    for label, block in sorted(by_client.items()):
        if not block["leaks"]:
            continue
        print(f"=== {label} ({block['ip']}) ===")
        for item in block["leaks"][:20]:
            cats = ",".join(item["categories"])
            print(
                f"  {item['forwarded_queries']:4d} fwd / {item['allowed_queries']:4d} allowed  "
                f"{item['domain']}  [{cats}]"
            )
        print()


def print_json(by_client: dict, all_candidates: dict, lookback: int) -> None:
    payload = {
        "lookback_hours": lookback,
        "candidates": [
            {
                "domain": info["domain"],
                "allowed_queries": info["allowed_queries"],
                "forwarded_queries": info["forwarded_queries"],
                "total_queries": info["total_queries"],
                "categories": sorted(info["categories"]),
                "clients": sorted(info["clients"]),
                "suggest_add": info["suggest_add"],
            }
            for info in sorted(
                all_candidates.values(),
                key=lambda x: (-x["forwarded_queries"], -x["allowed_queries"], x["domain"]),
            )
        ],
        "by_client": {
            label: {
                "ip": block["ip"],
                "name": block["name"],
                "leaks": block["leaks"],
            }
            for label, block in by_client.items()
            if block["leaks"]
        },
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find Pi-hole DNS leaks by category.")
    parser.add_argument(
        "--hours",
        type=int,
        default=LOOKBACK_HOURS,
        help=f"Lookback window (default: {LOOKBACK_HOURS})",
    )
    parser.add_argument(
        "--categories",
        default="gaming,porn_nsfw,gambling",
        help="Comma-separated categories (default: gaming,porn_nsfw,gambling)",
    )
    parser.add_argument(
        "--min-allowed",
        type=int,
        default=1,
        help="Minimum allowed queries before reporting (default: 1)",
    )
    parser.add_argument("--json", action="store_true", help="JSON output for agents/cron")
    args = parser.parse_args()

    unknown = set(args.categories.split(",")) - set(CATEGORIES)
    if unknown:
        print(f"Unknown categories: {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    categories = set(args.categories.split(","))
    cutoff = time.time() - args.hours * 3600

    try:
        db = sqlite3.connect(
            "file:/etc/pihole/pihole-FTL.db?mode=ro", uri=True, timeout=10
        )
    except sqlite3.OperationalError as exc:
        print(f"Cannot open FTL database (run with sudo?): {exc}", file=sys.stderr)
        return 1

    by_client, all_candidates = load_leaks(db, cutoff, categories, args.min_allowed)

    if args.json:
        print_json(by_client, all_candidates, args.hours)
    else:
        print_report(by_client, all_candidates, args.hours)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
