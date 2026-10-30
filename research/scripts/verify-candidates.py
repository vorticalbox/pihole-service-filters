#!/usr/bin/env python3
"""DNS-check candidate domains from research/candidates/*.txt files.

Usage:
  python3 research/scripts/verify-candidates.py [path ...]

Prints OK / FAIL per domain. Use before promoting lines into services/*.txt.
"""
from __future__ import annotations

import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATHS = sorted((ROOT / "research" / "candidates").glob("*.txt"))


def load_domains(paths: list[Path]) -> list[str]:
    out: list[str] = []
    for path in paths:
        for line in path.read_text().splitlines():
            line = line.split("#", 1)[0].strip().lower()
            if line and "." in line:
                out.append(line)
    return sorted(set(out))


def resolves(name: str) -> bool:
    try:
        socket.getaddrinfo(name, None, type=socket.SOCK_STREAM)
        return True
    except socket.gaierror:
        return False


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else DEFAULT_PATHS
    if not paths:
        print("No candidate files found.", file=sys.stderr)
        return 1
    domains = load_domains(paths)
    ok = fail = 0
    for d in domains:
        if resolves(d):
            print(f"OK   {d}")
            ok += 1
        else:
            print(f"FAIL {d}")
            fail += 1
    print(f"\n{ok} ok, {fail} fail, {len(domains)} total")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
