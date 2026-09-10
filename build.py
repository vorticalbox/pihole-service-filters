#!/usr/bin/env python3
"""Convert AdGuard Home's internal/filtering/servicelist.go into individual
Pi-hole-compatible blocklist files, one per service, so each can be added/
removed as a single Pi-hole Adlist entry (Settings -> Adlists) instead of a
pile of custom domain rows.

Output: services/<service_id>.txt  (one domain per line, Pi-hole adlist format)
Also writes services/_index.md listing every service + domain count.
"""
import re
from pathlib import Path

SRC = Path("/tmp/servicelist.go")
OUT = Path("services")
OUT.mkdir(exist_ok=True)

cat = SRC.read_text()
blocks = re.split(r"\}, \{(?=\n\tID:)", cat)

index = []
for b in blocks:
    m = re.search(r'ID:\s+"([^"]+)"', b)
    if not m:
        continue
    sid = m.group(1)
    domains = sorted(set(re.findall(r'\|\|([a-z0-9.\-]+\.[a-z]{2,})\^', b)))
    if not domains:
        continue
    path = OUT / f"{sid}.txt"
    path.write_text(
        f"# {sid} — blocklist for Pi-hole Adlists\n"
        f"# Source: AdGuard Home servicelist.go (github.com/AdguardTeam/AdGuardHome)\n"
        f"# {len(domains)} domains\n"
        + "\n".join(domains) + "\n"
    )
    index.append((sid, len(domains)))

index.sort()
with open(OUT / "_index.md", "w") as f:
    f.write("# Service filter index\n\n")
    f.write("| Service | Domains | File |\n|---|---|---|\n")
    for sid, n in index:
        f.write(f"| {sid} | {n} | `services/{sid}.txt` |\n")

print(f"wrote {len(index)} service files")
