# 02 — Fanfiction & social story archives

#research #pihole #parental

## Summary

Sites where kids go after Quotev for the same content shape: long-form fic, fandom communities, forums with story threads. AO3 and FanFiction.net are the largest; many smaller archives explicitly allow explicit ratings.

## In blocklist (`story_platforms.txt`)

| Domain | Role |
|--------|------|
| `archiveofourown.org` / `ao3.org` | AO3 (+ common short domain) |
| `fanfiction.net` / `fictionpress.com` | Same operator, shared infra |
| `scribblehub.com` | Quotev alt per r/Quotev |
| `squidgeworld.org` | AO3-style archive |
| `asianfanfics.com` | K-pop / Asian fandom fic |
| `ficbook.net` | Russian/EN fic host |
| `fanfics.me` | Smaller fic host |
| `livejournal.com` / `dreamwidth.org` | Legacy social + fic (privacy-focused DW) |
| `penana.com` | Quotev-like social + stories |
| `spacebattles.com` / `sufficientvelocity.com` / `questionablequesting.com` | Forum fic (QQ skews NSFW-friendly) |
| `fiction.live` | Interactive / quest fiction |
| `royalroad.com` | Progression fantasy; much teen traffic |
| `scribblehub.com` | Fic hosting |
| `tapas.io` / `webnovel.com` / `wattpad.com` / `wattpad.co.uk` | Serial fiction apps |
| `inkitt.com` | Self-publishing + reader app |
| `commaful.com` | Short story / poetry social |

## Researched but excluded

| Domain | Why |
|--------|-----|
| `fanlore.org` | Fandom wiki, not a reader |
| `harrypotterfanfiction.com` | Niche; add if Pi audit shows hits |
| `mibba.com` | No DNS A record at verify time |

## Sources

- Forbes “10 Popular Fanfiction Websites” (traffic + archive size)
- r/FanFiction, r/FanfictionNet, r/Quotev recommendation threads (2025–2026)

## Next steps

- [ ] Pi audit category `story_platforms` — promote any new allowed domains
- [ ] Tier-2 niche archives only after they appear in FTL logs
