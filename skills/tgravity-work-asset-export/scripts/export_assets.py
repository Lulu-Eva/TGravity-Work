#!/usr/bin/env python3
"""Export TGravity Work assets from a specified directory.

This script intentionally does not infer business meaning. It scans Markdown
files with YAML frontmatter containing `tgravity_asset: true`, copies them into an
export package, writes an index, and creates a zip archive.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import shutil
import zipfile
from pathlib import Path


ASSET_DIRS = {
    "daily_report": "daily",
    "creator_card": "creators",
    "brand_lead": "brands",
    "deal_progress": "deals",
    "deal_review": "reviews",
    "decision_request": "decisions",
    "escalation": "escalations",
}

REQUIRED_FIELDS = {
    "daily_report": ["asset_id", "asset_type", "title", "owner", "status"],
    "creator_card": ["asset_id", "asset_type", "title", "owner", "status"],
    "brand_lead": ["asset_id", "asset_type", "title", "owner", "status"],
    "deal_progress": ["asset_id", "asset_type", "title", "owner", "status"],
    "deal_review": ["asset_id", "asset_type", "title", "owner", "status"],
    "decision_request": ["asset_id", "asset_type", "title", "owner", "status"],
    "escalation": ["asset_id", "asset_type", "title", "owner", "status", "risk_level"],
}


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not match:
        return {}

    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def is_true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "yes", "1"}


def missing_fields(meta: dict[str, str]) -> list[str]:
    asset_type = meta.get("asset_type", "")
    fields = REQUIRED_FIELDS.get(asset_type, ["asset_id", "asset_type", "title", "owner", "status"])
    return [field for field in fields if not meta.get(field)]


def safe_name(path: Path) -> str:
    return re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", path.name)


def make_manifest(export_dir: Path, source: Path, rows: list[dict[str, str]]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["asset_type"]] = counts.get(row["asset_type"], 0) + 1

    lines = [
        "# TGravity资产包 Manifest",
        "",
        f"导出时间：{dt.datetime.now().isoformat(timespec='seconds')}",
        f"导出来源路径：{source}",
        "导出模式：当前指定目录",
        "",
        "## 资产数量",
        "",
        "| 类型 | 数量 |",
        "|---|---:|",
    ]
    for asset_type, count in sorted(counts.items()):
        lines.append(f"| {asset_type} | {count} |")
    if not counts:
        lines.append("| 无 | 0 |")

    lines.extend([
        "",
        "## 风险与缺失",
        "",
    ])
    missing_rows = [row for row in rows if row["missing_fields"]]
    if missing_rows:
        for row in missing_rows:
            lines.append(f"- {row['title'] or row['asset_id']}: 缺 {row['missing_fields']}")
    else:
        lines.append("- 未发现必填字段缺失。")

    lines.extend([
        "",
        "## 未导出内容",
        "",
        "- 未扫描指定目录之外的文件。",
        "- 未导出未标记 `tgravity_asset: true` 的 Markdown。",
        "- 未默认导出聊天记录、个人隐私、图片、视频或敏感证件材料。",
        "",
        "## 恢复说明",
        "",
        "按 `INDEX.csv` 中的 `export_path` 找到导出文件，按 `source_path` 可追溯原路径。",
    ])
    (export_dir / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_summary(export_dir: Path, rows: list[dict[str, str]]) -> None:
    open_items = [row for row in rows if row.get("status") not in {"closed", "archived"}]
    high_risk = [row for row in rows if row.get("risk_level") == "high"]
    missing_rows = [row for row in rows if row["missing_fields"]]

    lines = [
        "# TGravity资产导出摘要",
        "",
        "## 1. 本次导出了什么",
        "",
        f"- 共导出 {len(rows)} 个 TGravity 资产。",
        "",
        "## 2. 最重要的经营资产",
        "",
    ]
    if rows:
        for row in rows[:10]:
            lines.append(f"- {row['asset_type']}: {row['title'] or row['asset_id']}")
    else:
        lines.append("- 本次没有发现 TGravity 资产。")

    lines.extend(["", "## 3. 未闭环事项", ""])
    if open_items:
        for row in open_items[:20]:
            lines.append(f"- {row['title'] or row['asset_id']}（{row['status']}）")
    else:
        lines.append("- 未发现未闭环事项。")

    lines.extend(["", "## 4. 高风险事项", ""])
    if high_risk:
        for row in high_risk:
            lines.append(f"- {row['title'] or row['asset_id']}")
    else:
        lines.append("- 未发现 high 风险资产。")

    lines.extend(["", "## 5. 缺字段资产", ""])
    if missing_rows:
        for row in missing_rows:
            lines.append(f"- {row['title'] or row['asset_id']}: {row['missing_fields']}")
    else:
        lines.append("- 未发现必填字段缺失。")

    lines.extend([
        "",
        "## 6. 建议下次整理动作",
        "",
        "- 优先补齐缺字段资产。",
        "- 优先处理 pending_decision 状态的决策请求。",
        "- 对 high 风险事项做人工复核。",
    ])
    (export_dir / "EXPORT_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def zip_dir(export_dir: Path) -> Path:
    zip_path = export_dir.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in export_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(export_dir.parent))
    return zip_path


def export_assets(source: Path, output_root: Path) -> tuple[Path, Path, int]:
    timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    export_dir = output_root / f"{timestamp}_TGravity资产包"
    export_dir.mkdir(parents=True, exist_ok=True)

    for dirname in sorted(set(ASSET_DIRS.values()) | {"raw"}):
        (export_dir / dirname).mkdir(exist_ok=True)

    rows: list[dict[str, str]] = []
    for path in source.rglob("*.md"):
        if ".git" in path.parts:
            continue
        if "assets" in path.parts and "templates" in path.parts:
            continue
        meta = parse_frontmatter(path)
        if not is_true(meta.get("tgravity_asset")):
            continue
        asset_type = meta.get("asset_type", "raw")
        target_dir = export_dir / ASSET_DIRS.get(asset_type, "raw")
        target = target_dir / safe_name(path)
        if target.exists():
            target = target_dir / f"{path.stem}_{len(rows)+1}{path.suffix}"
        shutil.copy2(path, target)

        missing = missing_fields(meta)
        rows.append({
            "asset_id": meta.get("asset_id", ""),
            "asset_type": asset_type,
            "title": meta.get("title", ""),
            "source_path": str(path),
            "export_path": str(target),
            "owner": meta.get("owner", ""),
            "business_line": meta.get("business_line", ""),
            "status": meta.get("status", ""),
            "risk_level": meta.get("risk_level", ""),
            "source_daily_id": meta.get("source_daily_id", ""),
            "last_modified": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            "missing_fields": ";".join(missing),
            "tags": meta.get("tags", ""),
        })

    index_path = export_dir / "INDEX.csv"
    with index_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "asset_id",
            "asset_type",
            "title",
            "source_path",
            "export_path",
            "owner",
            "business_line",
            "status",
            "risk_level",
            "source_daily_id",
            "last_modified",
            "missing_fields",
            "tags",
        ])
        writer.writeheader()
        writer.writerows(rows)

    make_manifest(export_dir, source, rows)
    make_summary(export_dir, rows)
    zip_path = zip_dir(export_dir)
    return export_dir, zip_path, len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export TGravity Work assets.")
    parser.add_argument("--source", required=True, help="Directory to scan.")
    parser.add_argument("--output", required=True, help="Directory to write export packages.")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        raise SystemExit(f"source is not a directory: {source}")
    output.mkdir(parents=True, exist_ok=True)

    export_dir, zip_path, count = export_assets(source, output)
    print(f"export_dir={export_dir}")
    print(f"zip_path={zip_path}")
    print(f"asset_count={count}")


if __name__ == "__main__":
    main()
