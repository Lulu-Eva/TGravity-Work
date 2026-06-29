# TGW MCN Asset Contract

This file is the shared source of truth for all MCN asset skills.

## Hard Rules

- Runtime assets live in the user's project under `tgw-data/mcn/`, never inside the skill package.
- YAML frontmatter is the source of truth. Markdown `[[links]]`, CSV files, and summaries are rebuildable views.
- Executed creator-brand cooperation is sourced only from `mcn_collaboration` records, especially `brand_id`, `creator_id`, and `brief_id`.
- Every MCN asset must have a stable `asset_id`; do not use names as primary keys.
- A creator-brand cooperation is not a sentence inside either profile. It is a `mcn_collaboration` record.
- Missing information stays `unknown`; do not invent contacts, prices, budgets, results, dates, or platform data.
- Internal pricing, split rules, contact info, negative notes, payment risk, and contract details must stay out of brand-safe exports.

## Asset Types

| Type | Prefix | Default directory |
|---|---|---|
| `mcn_creator_profile` | `CRT` | `tgw-data/mcn/creators/` |
| `mcn_brand_profile` | `BRD` | `tgw-data/mcn/brands/` |
| `mcn_reverse_brief` | `BRF` | `tgw-data/mcn/briefs/` |
| `mcn_collaboration` | `COL` | `tgw-data/mcn/collaborations/` |

## ID Rules

Use:

```text
{PREFIX}-YYYYMMDD-001
```

Examples:

```text
CRT-20260627-001
BRD-20260627-001
BRF-20260627-001
COL-20260627-001
```

File names should be:

```text
{asset_id}_{short-human-name}.md
```

Names can change; IDs cannot.

## Required Frontmatter

All MCN assets must include:

```yaml
tgw_asset: true
asset_type: mcn_creator_profile
asset_id: CRT-YYYYMMDD-001
title: Human readable title
name: Primary display name
aliases: []
owner: unknown
business_line: 词元引力
status: draft
risk_level: unknown
confidence: low
privacy: internal
export_ready: false
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
source: unknown
source_evidence: []
tags: []
relationships: []
```

Use arrays for lists. Empty relationships must be:

```yaml
relationships: []
```

## Relationship Shape

```yaml
relationships:
  - type: 执行达人
    target: CRT-20260627-001
    project_id: COL-20260627-001
    date: 2026-06-27
    evidence: 用户口述
    note: 某品牌小红书种草合作
```

Required relationship fields:

- `type`
- `target`

Optional relationship fields:

- `project_id`
- `date`
- `evidence`
- `note`

## Allowed Relationship Types

First version only allows:

- `执行达人`: collaboration -> creator
- `执行品牌`: collaboration -> brand
- `来源brief`: collaboration -> brief
- `适配`: creator -> brief
- `不适配`: creator -> brief
- `同品类`: brand -> brand
- `风险冲突`: any asset -> any asset

Do not add relationship types casually. Add them only after changing this contract and tests.

`合作过` is a generated reading label only. Do not write it manually in `relationships`; rebuild it from `mcn_collaboration` records with the index skill.

## Entity Specific Fields

### Creator

```yaml
platforms: []
content_direction: unknown
audience_profile: unknown
follower_snapshot: unknown
performance_snapshot: unknown
rate_hint: unknown
fit_categories: []
delivery_risks: []
related_brands: []
matched_briefs: []
collaboration_ids: []
internal_fields_present: false
```

### Brand

```yaml
category: unknown
contact_source: unknown
relationship_strength: unknown
budget_hint: unknown
preferred_scenarios: []
payment_cycle: unknown
review_rounds: unknown
communication_cost: unknown
related_creators: []
brief_ids: []
collaboration_ids: []
internal_fields_present: false
```

### Reverse Brief

```yaml
brand_id: unknown
brand_name: unknown
product_name: unknown
campaign_goal: unknown
platforms: []
budget_hint: unknown
content_formats: []
creator_requirements: []
prohibitions: []
recommended_creators: []
rejected_creators: []
collaboration_ids: []
```

### Collaboration

```yaml
brand_id: BRD-YYYYMMDD-001
brand_name: unknown
creator_id: CRT-YYYYMMDD-001
creator_name: unknown
brief_id: unknown
project_name: unknown
platforms: []
deliverables: []
quoted_price: unknown
final_price: unknown
status: draft
payment_status: unknown
result_summary: unknown
review_summary: unknown
```

## Derived / Cache Fields

These fields are reading aids or pending backfill suggestions, not source data:

- `related_brands`
- `related_creators`
- `collaboration_ids`

Do not use them to prove that a creator and brand have cooperated. A real cooperation must exist as a `mcn_collaboration` record with `brand_id` and `creator_id`.

## Status Values

Creator:

```text
候选 / 接触中 / 评估中 / 已签约 / 合作中 / 暂停 / 淘汰 / 归档
```

Brand:

```text
线索 / 已验证 / 有需求 / 提案中 / 合作中 / 沉睡 / 归档
```

Brief:

```text
采集 / 澄清中 / 已确认 / 匹配中 / 执行中 / 复盘中 / 归档
```

Collaboration:

```text
草稿 / 报价中 / 合同推进 / 执行中 / 验收中 / 回款中 / 已结案 / 暂停 / 终止
```

## Markdown Body Sections

All assets should include:

```text
## 已确认信息
## 推断信息
## 缺失字段
## 建议追问
## 关联资产
## 内部备注
## 来源依据
```

`建议追问` must contain at most 3 questions.

## Save Boundary

Default behavior is draft output. Write files only when the user clearly asks to save or confirms saving.

If saving, explain the target directory first. Do not overwrite an existing file. Create a new file or update only when the user explicitly identifies the existing asset.

When a child skill includes `scripts/render_mcn_asset.py`, use it to create a first-time asset skeleton. The script renders the bundled template, writes identity fields such as `asset_id`, `title`, `name`, dates, owner, and source, then refuses accidental overwrites by default. It does not save all extracted business fields; fill the generated draft after rendering or edit the identified existing asset.
