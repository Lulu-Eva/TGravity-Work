#!/usr/bin/env python3
"""Validate TGW asset card frontmatter."""

from __future__ import annotations

import argparse
from pathlib import Path

from export_assets import is_tgw_asset, missing_fields, parse_frontmatter


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TGW asset cards.")
    parser.add_argument("--source", required=True, help="Directory to scan.")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    total = 0
    problems = 0

    for path in source.rglob("*.md"):
        if "assets" in path.parts and "templates" in path.parts:
            continue
        meta = parse_frontmatter(path)
        if not is_tgw_asset(meta):
            continue
        total += 1
        missing = missing_fields(meta)
        if missing:
            problems += 1
            print(f"{path}: missing {', '.join(missing)}")

    print(f"checked={total}")
    print(f"with_missing_fields={problems}")


if __name__ == "__main__":
    main()
