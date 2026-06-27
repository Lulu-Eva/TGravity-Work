#!/usr/bin/env python3
"""Build and validate TGravity Work MCN relationship indexes."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SCAN_DIRS = ("creators", "brands", "briefs", "collaborations")
INDEX_FILES = {
    "relations": "关系索引.csv",
    "summary": "关系总览.md",
    "brand_creator": "品牌-达人矩阵.csv",
    "creator_history": "达人合作历史.csv",
    "problems": "悬空关系检查.md",
}


@dataclass
class Asset:
    path: Path
    rel_path: str
    meta: dict[str, Any]
    body: str
    relationships: list[dict[str, str]] = field(default_factory=list)
    load_problem: str = ""

    @property
    def asset_id(self) -> str:
        return str(self.meta.get("asset_id") or self.meta.get("id") or "").strip()

    @property
    def asset_type(self) -> str:
        return str(self.meta.get("asset_type") or self.meta.get("type") or "").strip()

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or self.meta.get("name") or self.asset_id).strip()


@dataclass
class WriteContext:
    mcn_root: Path
    dry_run: bool = False
    backup: bool = True
    backup_root: Path | None = None
    backed_up: set[Path] = field(default_factory=set)
    changed_files: set[str] = field(default_factory=set)


def today() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")


def backup_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.S)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def parse_scalar(value: str) -> Any:
    raw = value.strip()
    if raw in {"[]", ""}:
        return [] if raw == "[]" else ""
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    return raw.strip('"').strip("'")


def parse_frontmatter_block(block: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    meta: dict[str, Any] = {}
    relationships: list[dict[str, str]] = []
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith("relationships:"):
            if line.strip() == "relationships: []":
                meta["relationships"] = []
                i += 1
                continue
            i += 1
            current: dict[str, str] | None = None
            while i < len(lines) and lines[i].startswith("  "):
                item = lines[i].strip()
                if item.startswith("- "):
                    if current:
                        relationships.append(current)
                    current = {}
                    item = item[2:].strip()
                    if item:
                        key, _, value = item.partition(":")
                        if key and _:
                            current[key.strip()] = str(parse_scalar(value))
                elif current is not None and ":" in item:
                    key, value = item.split(":", 1)
                    current[key.strip()] = str(parse_scalar(value))
                i += 1
            if current:
                relationships.append(current)
            meta["relationships"] = relationships
            continue
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            arr: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("  - "):
                arr.append(str(parse_scalar(lines[j].strip()[2:])))
                j += 1
            if arr:
                meta[key] = arr
                i = j
                continue
        meta[key] = parse_scalar(value)
        i += 1
    return meta, relationships


def load_asset(path: Path, mcn_root: Path) -> Asset | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = split_frontmatter(text)
    rel_path = path.relative_to(mcn_root).as_posix()
    if not frontmatter:
        return Asset(
            path=path,
            rel_path=rel_path,
            meta={},
            body=body,
            relationships=[],
            load_problem="missing frontmatter",
        )
    meta, relationships = parse_frontmatter_block(frontmatter)
    return Asset(
        path=path,
        rel_path=rel_path,
        meta=meta,
        body=body,
        relationships=relationships,
    )


def walk_assets(mcn_root: Path) -> list[Asset]:
    assets: list[Asset] = []
    for dirname in SCAN_DIRS:
        root = mcn_root / dirname
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            asset = load_asset(path, mcn_root)
            if asset:
                assets.append(asset)
    return assets


def csv_write(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def relation_rows(assets: list[Asset], by_id: dict[str, Asset]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    for asset in assets:
        for rel in asset.relationships:
            target_id = rel.get("target", "").strip()
            target = by_id.get(target_id)
            row = {
                "source_id": asset.asset_id,
                "source_type": asset.asset_type,
                "source_title": asset.title,
                "relation_type": rel.get("type", ""),
                "target_id": target_id,
                "target_type": target.asset_type if target else "",
                "target_title": target.title if target else "",
                "project_id": rel.get("project_id", ""),
                "date": rel.get("date", ""),
                "evidence": rel.get("evidence", ""),
                "note": rel.get("note", ""),
                "source_file": asset.rel_path,
                "target_file": target.rel_path if target else "",
                "status": "有效" if target else "目标缺失",
            }
            rows.append(row)
            if not target:
                missing.append(row)
    rows.sort(key=lambda r: (r["source_id"], r["relation_type"], r["target_id"]))
    return rows, missing


def first(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def collaboration_rows(assets: list[Asset], by_id: dict[str, Asset]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    brand_rows: list[dict[str, str]] = []
    creator_rows: list[dict[str, str]] = []
    for asset in assets:
        if asset.asset_type != "mcn_collaboration":
            continue
        brand_id = str(asset.meta.get("brand_id") or "").strip()
        creator_id = str(asset.meta.get("creator_id") or "").strip()
        brief_id = str(asset.meta.get("brief_id") or "").strip()
        brand = by_id.get(brand_id)
        creator = by_id.get(creator_id)
        common = {
            "collaboration_id": asset.asset_id,
            "collaboration_title": asset.title,
            "brief_id": brief_id,
            "project_name": str(asset.meta.get("project_name") or asset.title),
            "status": str(asset.meta.get("status") or ""),
            "platforms": ";".join(asset.meta.get("platforms") or []) if isinstance(asset.meta.get("platforms"), list) else str(asset.meta.get("platforms") or ""),
            "deliverables": ";".join(asset.meta.get("deliverables") or []) if isinstance(asset.meta.get("deliverables"), list) else str(asset.meta.get("deliverables") or ""),
            "quoted_price": str(asset.meta.get("quoted_price") or ""),
            "final_price": str(asset.meta.get("final_price") or ""),
            "payment_status": str(asset.meta.get("payment_status") or ""),
            "result_summary": str(asset.meta.get("result_summary") or ""),
            "source_file": asset.rel_path,
        }
        brand_rows.append({
            "brand_id": brand_id,
            "brand_title": brand.title if brand else str(asset.meta.get("brand_name") or ""),
            "creator_id": creator_id,
            "creator_title": creator.title if creator else str(asset.meta.get("creator_name") or ""),
            **common,
        })
        creator_rows.append({
            "creator_id": creator_id,
            "creator_title": creator.title if creator else str(asset.meta.get("creator_name") or ""),
            "brand_id": brand_id,
            "brand_title": brand.title if brand else str(asset.meta.get("brand_name") or ""),
            **common,
        })
    brand_rows.sort(key=lambda r: (r["brand_title"], r["creator_title"], r["collaboration_id"]))
    creator_rows.sort(key=lambda r: (r["creator_title"], r["brand_title"], r["collaboration_id"]))
    return brand_rows, creator_rows


def duplicate_ids(assets: list[Asset]) -> dict[str, list[Asset]]:
    seen: dict[str, list[Asset]] = {}
    for asset in assets:
        seen.setdefault(asset.asset_id, []).append(asset)
    return {asset_id: items for asset_id, items in seen.items() if asset_id and len(items) > 1}


def required_problems(assets: list[Asset]) -> list[str]:
    problems: list[str] = []
    for asset in assets:
        if asset.load_problem:
            problems.append(f"{asset.rel_path}: {asset.load_problem}")
        if not asset.asset_id:
            problems.append(f"{asset.rel_path}: missing asset_id")
        if not asset.asset_type:
            problems.append(f"{asset.rel_path}: missing asset_type")
        if not asset.title:
            problems.append(f"{asset.rel_path}: missing title")
        for rel in asset.relationships:
            if rel.get("type", "").strip() == "合作过":
                problems.append(f"{asset.rel_path}: relationship type 合作过 is generated-only")
        if asset.asset_type == "mcn_collaboration":
            if not str(asset.meta.get("brand_id") or "").strip() or str(asset.meta.get("brand_id")).strip() == "unknown":
                problems.append(f"{asset.rel_path}: collaboration missing brand_id")
            if not str(asset.meta.get("creator_id") or "").strip() or str(asset.meta.get("creator_id")).strip() == "unknown":
                problems.append(f"{asset.rel_path}: collaboration missing creator_id")
    return problems


def id_to_link(assets: list[Asset]) -> dict[str, str]:
    return {asset.asset_id: f"[[{asset.path.stem}]]" for asset in assets if asset.asset_id}


def ensure_backup(asset: Asset, context: WriteContext) -> None:
    if context.dry_run or not context.backup or asset.path in context.backed_up:
        return
    if context.backup_root is None:
        context.backup_root = context.mcn_root / ".backups" / f"fill-links-{backup_stamp()}"
    relative = asset.path.relative_to(context.mcn_root)
    backup_path = context.backup_root / relative
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(asset.path, backup_path)
    context.backed_up.add(asset.path)


def write_asset_text(asset: Asset, text: str, context: WriteContext) -> bool:
    context.changed_files.add(asset.rel_path)
    if context.dry_run:
        return True
    ensure_backup(asset, context)
    asset.path.write_text(text, encoding="utf-8")
    return True


def fill_body_links(asset: Asset, links: dict[str, str], context: WriteContext) -> bool:
    frontmatter, body = split_frontmatter(asset.path.read_text(encoding="utf-8", errors="replace"))
    targets = [rel.get("target", "") for rel in asset.relationships if rel.get("target") in links]
    if not targets:
        return False
    unique_links = []
    for target in targets:
        link = links[target]
        if link not in unique_links:
            unique_links.append(link)
    bullets = "\n".join(f"- {link}" for link in unique_links)
    match = re.search(r"(?m)^## 关联资产\s*$", body)
    if not match:
        next_body = body.rstrip() + "\n\n## 关联资产\n\n" + bullets + "\n"
    else:
        section_start = match.end()
        next_header = re.search(r"(?m)^## ", body[section_start:])
        section_end = section_start + next_header.start() if next_header else len(body)
        section_text = body[section_start:section_end]
        existing_lines = {line.strip() for line in section_text.splitlines()}
        missing_links = [link for link in unique_links if f"- {link}" not in existing_lines]
        if not missing_links:
            return False
        missing_bullets = "\n".join(f"- {link}" for link in missing_links)
        if section_text.strip():
            next_section = section_text.rstrip() + "\n" + missing_bullets + "\n"
        else:
            next_section = "\n\n" + missing_bullets + "\n"
        next_body = body[:section_start] + next_section + body[section_end:]
    if next_body == body:
        return False
    return write_asset_text(asset, f"---\n{frontmatter}\n---\n{next_body}", context)


def collaboration_backlinks(assets: list[Asset], by_id: dict[str, Asset]) -> dict[str, dict[str, list[str]]]:
    backlinks: dict[str, dict[str, list[str]]] = {}
    links = id_to_link(assets)
    for asset in assets:
        if asset.asset_type != "mcn_collaboration":
            continue
        brand_id = str(asset.meta.get("brand_id") or "").strip()
        creator_id = str(asset.meta.get("creator_id") or "").strip()
        if not brand_id or not creator_id:
            continue
        brand = by_id.get(brand_id)
        creator = by_id.get(creator_id)
        if brand:
            creator_label = links.get(creator_id) or str(asset.meta.get("creator_name") or creator_id)
            backlinks.setdefault(brand_id, {}).setdefault("合作过的达人", []).append(
                f"- {creator_label}：[[{asset.path.stem}]]"
            )
        if creator:
            brand_label = links.get(brand_id) or str(asset.meta.get("brand_name") or brand_id)
            backlinks.setdefault(creator_id, {}).setdefault("合作过的品牌", []).append(
                f"- {brand_label}：[[{asset.path.stem}]]"
            )
    return backlinks


def replace_generated_section(body: str, title: str, lines: list[str]) -> tuple[str, bool]:
    section_header = f"## {title}"
    start_marker = "<!-- TGRAVITY:GENERATED-START -->"
    end_marker = "<!-- TGRAVITY:GENERATED-END -->"
    rendered_lines = list(dict.fromkeys(lines))
    section = (
        f"{section_header}\n\n"
        f"{start_marker}\n"
        + ("\n".join(rendered_lines) if rendered_lines else "- 暂无记录")
        + f"\n{end_marker}\n"
    )
    pattern = re.compile(
        rf"^## {re.escape(title)}\n\n<!-- TGRAVITY:GENERATED-START -->\n[\s\S]*?<!-- TGRAVITY:GENERATED-END -->\n?",
        flags=re.M,
    )
    if pattern.search(body):
        next_body = pattern.sub(section, body)
    else:
        next_body = body.rstrip() + "\n\n" + section
    return next_body, next_body != body


def fill_derived_backlinks(asset: Asset, sections: dict[str, list[str]], context: WriteContext) -> bool:
    if not sections:
        return False
    frontmatter, body = split_frontmatter(asset.path.read_text(encoding="utf-8", errors="replace"))
    next_body = body
    changed = False
    for title, lines in sections.items():
        next_body, section_changed = replace_generated_section(next_body, title, lines)
        changed = changed or section_changed
    if not changed:
        return False
    return write_asset_text(asset, f"---\n{frontmatter}\n---\n{next_body}", context)


def build_indexes(mcn_root: Path, fill_links: bool = False, dry_run: bool = False, backup: bool = True) -> dict[str, Any]:
    mcn_root.mkdir(parents=True, exist_ok=True)
    index_root = mcn_root / "indexes"
    index_root.mkdir(parents=True, exist_ok=True)

    assets = walk_assets(mcn_root)
    by_id = {asset.asset_id: asset for asset in assets if asset.asset_id}
    duplicates = duplicate_ids(assets)
    relations, missing = relation_rows(assets, by_id)
    brand_rows, creator_rows = collaboration_rows(assets, by_id)
    required = required_problems(assets)

    csv_write(index_root / INDEX_FILES["relations"], [
        "source_id", "source_type", "source_title", "relation_type", "target_id", "target_type",
        "target_title", "project_id", "date", "evidence", "note", "source_file", "target_file", "status",
    ], relations)
    csv_write(index_root / INDEX_FILES["brand_creator"], [
        "brand_id", "brand_title", "creator_id", "creator_title", "collaboration_id", "collaboration_title",
        "brief_id", "project_name", "status", "platforms", "deliverables", "quoted_price", "final_price",
        "payment_status", "result_summary", "source_file",
    ], brand_rows)
    csv_write(index_root / INDEX_FILES["creator_history"], [
        "creator_id", "creator_title", "brand_id", "brand_title", "collaboration_id", "collaboration_title",
        "brief_id", "project_name", "status", "platforms", "deliverables", "quoted_price", "final_price",
        "payment_status", "result_summary", "source_file",
    ], creator_rows)

    summary_lines = [
        "# MCN 关系总览",
        "",
        f"最后更新：{today()}",
        "",
        "## 当前统计",
        "",
        f"- MCN 资产总数：{len(assets)}",
        f"- 关系总数：{len(relations)}",
        f"- 合作记录数：{sum(1 for asset in assets if asset.asset_type == 'mcn_collaboration')}",
        f"- 品牌-达人合作行数：{len(brand_rows)}",
        f"- 重复 ID 数：{len(duplicates)}",
        f"- 悬空关系数：{len(missing)}",
        f"- 必填问题数：{len(required)}",
        "",
        "## 生成文件",
        "",
    ]
    for file_name in INDEX_FILES.values():
        summary_lines.append(f"- `tgravity-work-data/mcn/indexes/{file_name}`")
    (index_root / INDEX_FILES["summary"]).write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    problem_lines = [
        "# MCN 悬空关系检查",
        "",
        f"最后更新：{today()}",
        "",
        "## 重复 ID",
        "",
    ]
    if duplicates:
        for asset_id, items in sorted(duplicates.items()):
            problem_lines.append(f"- {asset_id}: " + "; ".join(item.rel_path for item in items))
    else:
        problem_lines.append("- 未发现重复 ID。")
    problem_lines.extend(["", "## 悬空关系", ""])
    if missing:
        for row in missing:
            problem_lines.append(f"- {row['source_id']} -> {row['target_id']} ({row['relation_type']}): {row['source_file']}")
    else:
        problem_lines.append("- 未发现悬空关系。")
    problem_lines.extend(["", "## 必填问题", ""])
    if required:
        for item in required:
            problem_lines.append(f"- {item}")
    else:
        problem_lines.append("- 未发现必填问题。")
    (index_root / INDEX_FILES["problems"]).write_text("\n".join(problem_lines) + "\n", encoding="utf-8")

    write_context: WriteContext | None = None
    if fill_links:
        write_context = WriteContext(mcn_root=mcn_root, dry_run=dry_run, backup=backup)
        links = id_to_link(assets)
        for asset in assets:
            fill_body_links(asset, links, write_context)
        backlinks = collaboration_backlinks(assets, by_id)
        for asset_id, sections in backlinks.items():
            asset = by_id.get(asset_id)
            if asset:
                fill_derived_backlinks(asset, sections, write_context)

    return {
        "mcn_root": str(mcn_root),
        "index_root": str(index_root),
        "asset_count": len(assets),
        "relation_count": len(relations),
        "collaboration_count": sum(1 for asset in assets if asset.asset_type == "mcn_collaboration"),
        "brand_creator_rows": len(brand_rows),
        "duplicate_ids": len(duplicates),
        "missing_targets": len(missing),
        "required_problems": len(required),
        "changed_link_files": len(write_context.changed_files) if write_context else 0,
        "fill_links_dry_run": dry_run if fill_links else False,
        "fill_links_backup": backup if fill_links else False,
        "backup_root": str(write_context.backup_root) if write_context and write_context.backup_root else "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build TGravity Work MCN relationship indexes.")
    parser.add_argument("--root", help="Project root containing tgravity-work-data/mcn.")
    parser.add_argument("--mcn-root", help="Direct path to the MCN data root.")
    parser.add_argument("--fill-links", action="store_true", help="Fill Markdown body backlinks from relationships.")
    parser.add_argument("--dry-run", action="store_true", help="Preview --fill-links source Markdown changes without writing them.")
    parser.add_argument("--no-backup", action="store_true", help="Do not back up source Markdown files before --fill-links writes.")
    args = parser.parse_args()

    if args.mcn_root:
        mcn_root = Path(args.mcn_root).expanduser().resolve()
    elif args.root:
        mcn_root = Path(args.root).expanduser().resolve() / "tgravity-work-data" / "mcn"
    else:
        mcn_root = Path.cwd() / "tgravity-work-data" / "mcn"

    result = build_indexes(
        mcn_root,
        fill_links=args.fill_links,
        dry_run=args.dry_run,
        backup=not args.no_backup,
    )
    for key, value in result.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
