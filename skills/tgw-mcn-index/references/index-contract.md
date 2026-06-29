# MCN Index Contract

The index is a rebuildable view over MCN Markdown assets.

## Source Roots

Scan these directories under a user project:

```text
tgw-data/mcn/creators/
tgw-data/mcn/brands/
tgw-data/mcn/briefs/
tgw-data/mcn/collaborations/
```

Write generated files to:

```text
tgw-data/mcn/indexes/
```

## Generated Files

- `关系索引.csv`: every relationship edge
- `关系总览.md`: counts, missing targets, duplicate IDs
- `品牌-达人矩阵.csv`: brand-to-creator view derived from collaboration records
- `达人合作历史.csv`: creator-to-brand history derived from collaboration records
- `悬空关系检查.md`: duplicate IDs, missing targets, malformed required fields

## Rebuild Rule

Do not edit generated files as source data. Fix the Markdown asset frontmatter, then rebuild.

## Link Fill Rule

Markdown `[[filename]]` links are optional reading aids. A valid asset library must pass ID and relationship validation even if no body links exist.

`合作过` is generated reading text only. Do not write it as a manual relationship type; use `mcn_collaboration.brand_id` and `mcn_collaboration.creator_id`, then rebuild indexes.
