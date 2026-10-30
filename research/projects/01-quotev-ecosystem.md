# 01 — Quotev ecosystem

#research #pihole #parental

## Summary

Quotev (`quotev.com`) mixes personality quizzes, social profiles, and user-published fiction. Mature and romantic content is common; age gating is weak. DNS block is apex-level — Pi-hole suffix match covers `www`, `m`, `secure`, etc.

## Confirmed domains

| Domain | Notes |
|--------|--------|
| `quotev.com` | Primary site |
| `quotev.net` | Alternate apex (resolves, community mentions) |

## Discovery sources (2026-10-30)

- crt.sh TLS names for `%.quotev.com` → `secure.quotev.com`, `www.secure.quotev.com` (covered by apex)
- r/Quotev threads on “Quotev alts” → Penana, ScribbleHub, Dreamwidth, Wattpad (tracked in project 02)

## Next steps

- [ ] After enabling block, watch Pi-hole FTL for `quotev` substring — any CDN bypass domains?
- [ ] Check child device for Quotev mobile app (may use non-obvious API hosts)

## List file

`services/story_platforms.txt` (Quotev apex domains at lines with `quotev.com` / `quotev.net`)
