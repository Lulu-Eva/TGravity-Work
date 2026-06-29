# MCN Index Workflow

## Commands

Validate and rebuild indexes:

```bash
python3 skills/tgw-mcn-index/scripts/mcn_index.py --root "<project-root>"
```

Also fill Markdown body backlinks:

```bash
python3 skills/tgw-mcn-index/scripts/mcn_index.py --root "<project-root>" --fill-links --dry-run
python3 skills/tgw-mcn-index/scripts/mcn_index.py --root "<project-root>" --fill-links
```

Run `--dry-run` first. It reports how many source Markdown files would change while leaving source files untouched. The normal `--fill-links` run backs up each changed source Markdown file once under `tgw-data/mcn/.backups/fill-links-*` before writing. Do not use `--no-backup` unless the user explicitly asks for it and the project is already protected by version control or a separate backup.

`--fill-links` also derives readable profile sections from collaboration records:

- brand profile: `## 合作过的达人`
- creator profile: `## 合作过的品牌`

These sections are generated between `<!-- TGRAVITY:GENERATED-START -->` and `<!-- TGRAVITY:GENERATED-END -->`; fix the source `COL-*` collaboration record and rebuild instead of editing generated lines.

If a Markdown file manually writes `relationships.type: 合作过`, the script reports it as `required_problems`; use a `COL-*` record instead.

Use a custom MCN data directory:

```bash
python3 skills/tgw-mcn-index/scripts/mcn_index.py --mcn-root "<project-root>/tgw-data/mcn"
```

For package development tests, prefer `python3 tests/smoke_tgw.py --quick`; it copies fixtures to a temporary directory before generating indexes.

## Output Interpretation

- `duplicate_ids > 0`: fix before trusting search or export.
- `missing_targets > 0`: some relationship points to an asset that does not exist.
- `required_problems > 0`: some MCN Markdown file is malformed, including files missing `asset_id`; fix before trusting indexes.
- `collaboration_count = 0`: brand-creator views will be empty even if profiles exist.

## Fix Order

1. Duplicate IDs.
2. Missing collaboration brand/creator IDs.
3. Missing relationship targets.
4. Body link fill.
