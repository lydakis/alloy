#!/usr/bin/env python3
"""
Sync brand assets from the public alloy-brand repo into docs/assets/.

Defaults to GitHub Pages URLs so it works without local clones.
Override base via ALLOY_BRAND_BASE_URL if needed.
"""
from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "alloy-docs-sync/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def main() -> int:
    base = os.environ.get(
        "ALLOY_BRAND_BASE_URL",
        "https://cdn.jsdelivr.net/gh/lydakis/alloy-brand@main",
    ).rstrip("/")
    targets = {
        f"{base}/logo-mark.svg": Path("docs/assets/logo.svg"),
        f"{base}/favicon.svg": Path("docs/assets/favicon.svg"),
    }

    wrote = 0
    for url, out_path in targets.items():
        try:
            data = fetch(url)
        except Exception as e:  # noqa: BLE001 - keep it simple for CI logs
            print(f"[brand-sync] skip {url}: {e}")
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
        wrote += 1
        print(f"[brand-sync] wrote {out_path} from {url}")

    if wrote == 0:
        print("[brand-sync] no assets synced; kept existing local copies")
    else:
        print(f"[brand-sync] synced {wrote} assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
