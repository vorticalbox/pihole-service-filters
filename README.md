# pihole-service-filters

One blocklist file per online service, sourced from [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome)'s built-in "Blocked services" catalogue — reformatted for **Pi-hole**.

Instead of toggling hundreds of individual domain rows, add/remove a service as a single **Adlist** in Pi-hole. Enable an adlist = block that service everywhere. Disable it = instantly allowed again (after `pihole updateGravity`).

## Usage

1. Pi-hole web UI → **Adlists** → Add a new adlist
2. URL: `https://raw.githubusercontent.com/vorticalbox/pihole-service-filters/main/services/<name>.txt`
   e.g. `.../services/netflix.txt`, `.../services/tiktok.txt`
3. Give it a comment (matches the service name) so it's easy to find later
4. Tools → Update Gravity
5. To turn a service off: disable that adlist, Update Gravity again — done, no digging through domain lists.

## Services

See [`services/_index.md`](services/_index.md) for the full list (137 services, one file each) — everything from streaming (Netflix, Disney+, Twitch) to social (Facebook, TikTok, Reddit), gaming (Steam, Epic, Roblox), shopping (Temu, Shein, AliExpress), AI chat (Gemini, Grok, Copilot), and gambling.

## Companion list: browser games

For broad browser/flash game coverage, this repo is meant to be used alongside [IREK-szef/games-blocklist](https://github.com/IREK-szef/games-blocklist) (8,000+ domains, AdGuard Home format):

```
https://raw.githubusercontent.com/IREK-szef/games-blocklist/main/AGH.txt
```

`services/online-games.txt` in this repo fills gaps found by cross-checking that list against top game-aggregator sites (Poki, AddictingGames, CoolMathGames, etc.) — add both as separate Adlists.

## Regenerating

`build.py` parses AdGuard Home's `internal/filtering/servicelist.go` and regenerates every file in `services/`. Re-run it against a fresh copy of that file to pick up new/updated services from upstream AdGuard.

## Notes

- Files are plain domain lists (one per line), the standard Pi-hole/AdGuard adlist format.
- WhatsApp is intentionally **not** included as a blockable service — carve it out manually via a Pi-hole allow rule if any file here ever nets it.
