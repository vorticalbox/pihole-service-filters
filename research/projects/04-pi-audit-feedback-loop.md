# 04 — Pi-hole audit feedback loop

#research #pihole

## Summary

Close the loop: allowed DNS queries on child clients → `story_platforms` category → human review → `research/candidates/` → verify → `services/*.txt`.

## Script

On Pi (path may match deploy):

```bash
sudo -n python3 /opt/pihole-scripts/daily-client-audit.py
```

Repo copy: `scripts/daily-client-audit.py` — includes `story_platforms` regex category (sync to Pi when updated).

## Category: `story_platforms`

Matches domain substrings for Quotev, Wattpad, AO3, fanfiction.net, web-novel hosts, and related forums. Overlaps intentional with `services/fanfiction_story_platforms.txt` so audit highlights **gaps** (domains not yet on blocklist).

## Deploy checklist

1. Copy updated audit script to Pi if needed
2. Add Adlists:
   - `.../services/quotev.txt` (minimal)
   - `.../services/fanfiction_story_platforms.txt` (recommended superset)
3. Pi-hole → Update Gravity
4. Optional: assign Adlists to a **Kids** group in Pi-hole v6 if only child VLAN uses them

## Validation

```bash
~/.cursor/skills/pihole-dns-check/scripts/pihole_check.sh quotev 60
```

Expect status **1** (gravity) or **5** (denylist) after block is active.
