#!/usr/bin/env python3
"""Sync shared MCN resources into self-contained child skills."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


CONTRACT_SKILLS = (
    "tgravity-work-mcn-creator-profile",
    "tgravity-work-mcn-brand-profile",
    "tgravity-work-mcn-brief-builder",
    "tgravity-work-mcn-collaboration",
    "tgravity-work-mcn-index",
)

RENDER_SKILLS = (
    "tgravity-work-mcn-creator-profile",
    "tgravity-work-mcn-brand-profile",
    "tgravity-work-mcn-brief-builder",
    "tgravity-work-mcn-collaboration",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sync_file(source: Path, target: Path, *, check: bool) -> bool:
    source_text = source.read_text(encoding="utf-8")
    target_exists = target.exists()
    target_text = target.read_text(encoding="utf-8") if target_exists else ""
    if target_exists and target_text == source_text:
        return False
    if check:
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync shared MCN resources into child skills.")
    parser.add_argument("--check", action="store_true", help="Fail if any generated child copy is stale.")
    args = parser.parse_args()

    root = repo_root()
    shared_root = root / "shared" / "mcn"
    contract_source = shared_root / "asset-contract.md"
    render_source = shared_root / "render_mcn_asset.py"

    changed: list[str] = []
    for skill_name in CONTRACT_SKILLS:
        target = root / "skills" / skill_name / "references" / "asset-contract.md"
        if sync_file(contract_source, target, check=args.check):
            changed.append(str(target.relative_to(root)))
    for skill_name in RENDER_SKILLS:
        target = root / "skills" / skill_name / "scripts" / "render_mcn_asset.py"
        if sync_file(render_source, target, check=args.check):
            changed.append(str(target.relative_to(root)))

    if args.check and changed:
        print("drifted=" + ",".join(changed))
        return 1
    for item in changed:
        print(f"updated={item}")
    print(f"checked={len(CONTRACT_SKILLS) + len(RENDER_SKILLS)}")
    print(f"updated_count={len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
