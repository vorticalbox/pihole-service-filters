# Research — kid-inappropriate story / fanfic platforms

Living research for domains that should land in `services/*.txt` blocklists. Goal: catch Quotev-like sites (quizzes, social fic, mature romance serials) before they become a habit, using Pi-hole query logs + public “alternatives” lists.

## Active projects

| ID | Doc | Output list |
|----|-----|-------------|
| 01 | [quotev-ecosystem.md](projects/01-quotev-ecosystem.md) | `services/story_platforms.txt` |
| 02 | [fanfiction-archives.md](projects/02-fanfiction-archives.md) | `services/story_platforms.txt` |
| 03 | [webnovel-romance-apps.md](projects/03-webnovel-romance-apps.md) | same (romance/novel section) |
| 04 | [pi-audit-feedback-loop.md](projects/04-pi-audit-feedback-loop.md) | `scripts/daily-client-audit.py` category |

## Workflow

1. **Discover** — Reddit/Quora “Quotev alternative”, SimilarWeb competitors, Forbes/top-N fanfic articles, Pi-hole allowed queries (category `story_platforms`).
2. **Verify** — `python3 research/scripts/verify-candidates.py research/candidates/*.txt` (DNS A/AAAA; drop NXDOMAIN).
3. **Promote** — add apex domain to the right `services/<name>.txt`; note date + source in file header.
4. **Deploy** — push repo, add raw GitHub Adlist URL on Pi, Update Gravity.
5. **Validate** — `~/.cursor/skills/pihole-dns-check/scripts/pihole_check.sh quotev` after child device retries site.

## Candidate inbox

Drop one domain per line (comments `#` allowed) under `research/candidates/`. Run verify script before merging into `services/`.

## Out of scope (use other lists)

- **Hard porn** — existing `porn_nsfw` patterns in audit script + dedicated blocklists.
- **Reddit / Tumblr / Discord** — already in this repo as separate service files; blocking them is a bigger hammer.
- **Google Docs** — hosts drafts; DNS block breaks school/work.
