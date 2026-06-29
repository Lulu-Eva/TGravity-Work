#!/usr/bin/env python3
"""Render a TGW MCN asset skeleton from a bundled Markdown template."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import tempfile
from pathlib import Path


FIELD_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def today() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value.strip(), flags=re.UNICODE)
    slug = slug.strip("-._")
    return slug[:80] or "untitled"


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def current_skill_dir() -> Path | None:
    script_path = Path(__file__).resolve()
    if script_path.parent.name != "scripts":
        return None
    return script_path.parent.parent


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.S)
    if not match:
        raise SystemExit("template must contain YAML frontmatter")
    return match.group(1), text[match.end() :]


def replace_frontmatter_fields(block: str, replacements: dict[str, str]) -> str:
    rendered: list[str] = []
    seen: set[str] = set()
    for line in block.splitlines():
        match = FIELD_PATTERN.match(line)
        if match and match.group(1) in replacements:
            key = match.group(1)
            rendered.append(f"{key}: {yaml_scalar(replacements[key])}")
            seen.add(key)
        else:
            rendered.append(line)
    missing = [key for key in replacements if key not in seen]
    if missing:
        raise SystemExit(f"template missing required frontmatter fields: {', '.join(missing)}")
    return "\n".join(rendered)


def yaml_scalar(value: str) -> str:
    raw = value.strip()
    if not raw:
        return '""'
    if re.match(r"^[A-Za-z0-9_\-\.\u4e00-\u9fff]+$", raw):
        return raw
    return json.dumps(raw, ensure_ascii=False)


def replace_heading(body: str, title: str) -> str:
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            lines[index] = f"# {title}"
            return "\n".join(lines) + ("\n" if body.endswith("\n") else "")
    return f"# {title}\n\n{body.lstrip()}"


def atomic_write(path: Path, text: str, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise SystemExit(f"refusing to overwrite existing file: {path}")
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(text)
    temp_path.replace(path)


def render(args: argparse.Namespace) -> Path:
    template = Path(args.template).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    skill_dir = current_skill_dir()
    if skill_dir and is_relative_to(output_dir, skill_dir):
        raise SystemExit(
            "output-dir points inside the skill package; pass the user's project data directory instead"
        )
    title = args.title.strip()
    name = (args.name or args.title).strip()
    date = args.date or today()
    if not title:
        raise SystemExit("--title must not be empty")
    if not args.asset_id.strip():
        raise SystemExit("--asset-id must not be empty")

    frontmatter, body = split_frontmatter(template.read_text(encoding="utf-8"))
    replacements = {
        "asset_id": args.asset_id.strip(),
        "title": title,
        "name": name,
        "owner": args.owner.strip(),
        "created_at": date,
        "updated_at": date,
    }
    if args.status:
        replacements["status"] = args.status.strip()
    if args.source:
        replacements["source"] = args.source.strip()

    rendered_frontmatter = replace_frontmatter_fields(frontmatter, replacements)
    rendered_body = replace_heading(body, title)
    filename = f"{args.asset_id.strip()}_{safe_slug(title)}.md"
    output_path = output_dir / filename
    atomic_write(output_path, f"---\n{rendered_frontmatter}\n---\n{rendered_body}", args.overwrite)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a TGW MCN Markdown asset skeleton.")
    parser.add_argument("--template", required=True, help="Path to the bundled asset template.")
    parser.add_argument("--output-dir", required=True, help="Directory to write the rendered asset into.")
    parser.add_argument("--asset-id", required=True, help="Stable asset ID, e.g. CRT-20260627-001.")
    parser.add_argument("--title", required=True, help="Human-readable title and file slug source.")
    parser.add_argument("--name", help="Primary display name. Defaults to --title.")
    parser.add_argument("--owner", default="unknown", help="Asset owner or maintainer.")
    parser.add_argument("--status", help="Override template status.")
    parser.add_argument("--source", help="Override template source.")
    parser.add_argument("--date", help="YYYY-MM-DD date for created_at and updated_at. Defaults to today.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing rendered file.")
    args = parser.parse_args()

    output_path = render(args)
    print(f"created={output_path}")


if __name__ == "__main__":
    main()
