---
name: tgw-mcn-index
description: TGW MCN 关系索引 Skill。用于扫描本地 MCN Markdown 资产，校验稳定 ID、重复 ID、悬空 relationships、品牌-达人合作矩阵、达人合作历史，并可回填正文 Markdown 双链。触发方式：MCN关系索引、重建MCN索引、品牌达人互链、达人品牌互链、合作历史查询、达人合作过哪些品牌、品牌合作过哪些达人、悬空链接、检查MCN资产、生成品牌达人矩阵、填充Obsidian链接。
---

# TGW MCN Index

你负责校验和重建 MCN 资产关系视图。你不修改业务事实；只从 frontmatter 派生索引和正文阅读链接。品牌-达人合作事实只来自 `COL` 合作记录的 `brand_id`、`creator_id` 和 `brief_id`。

## 必读规则

执行前读取：

- `references/asset-contract.md`
- `references/index-contract.md`
- `references/index-workflow.md`

## 什么时候用

- 用户要点击品牌看到合作达人。
- 用户要点击达人看到合作品牌。
- 用户要查品牌-达人合作矩阵。
- 用户要检查关系是否悬空。
- 用户要填充 Obsidian `[[links]]`。
- 用户要在品牌页看到 `## 合作过的达人`，或在达人页看到 `## 合作过的品牌`。
- 用户要导出前校验 MCN 资产。

## 工作流

1. 确认扫描目录。默认使用当前项目的：

```text
tgw-data/mcn/
```

2. 运行：

```bash
python3 skills/tgw-mcn-index/scripts/mcn_index.py --root "<项目根目录>"
```

3. 如果用户要求填充正文双链，或要在品牌/达人档案内看到合作历史，先预演：

```bash
python3 skills/tgw-mcn-index/scripts/mcn_index.py --root "<项目根目录>" --fill-links --dry-run
```

4. 预演输出符合预期后，再正式回填：

```bash
python3 skills/tgw-mcn-index/scripts/mcn_index.py --root "<项目根目录>" --fill-links
```

正式回填默认会先把被修改的源 Markdown 备份到：

```text
tgw-data/mcn/.backups/fill-links-*/
```

除非用户明确要求且项目已有版本管理，不使用 `--no-backup`。

5. 输出生成文件路径、资产数、关系数、重复 ID、悬空关系数、正文回填文件数和备份目录。
6. 如果存在错误，不要假装完成；列出必须修复的 Markdown 文件。

## 生成文件

```text
tgw-data/mcn/indexes/关系索引.csv
tgw-data/mcn/indexes/关系总览.md
tgw-data/mcn/indexes/品牌-达人矩阵.csv
tgw-data/mcn/indexes/达人合作历史.csv
tgw-data/mcn/indexes/悬空关系检查.md
```

## 禁止

- 不把生成的 CSV 当源数据修改。
- 不凭正文 `[[链接]]` 判断合作事实。
- 不把推荐匹配当合作历史。
- 不接受手写 `合作过` relationship；它只能由索引从 `COL` 记录派生为阅读展示。
- 不默认扫描整台电脑。
- 不手改生成区；`<!-- TGRAVITY:GENERATED-START -->` 到 `<!-- TGRAVITY:GENERATED-END -->` 之间由脚本重建。
