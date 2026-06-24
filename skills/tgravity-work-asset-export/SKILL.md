---
name: tgravity-work-asset-export
description: "TGravity Work 资产导出 Skill。用于扫描用户指定项目目录中的 Markdown 资产卡，识别 tgravity_asset true，校验必填字段，生成 INDEX.csv、MANIFEST.md、EXPORT_SUMMARY.md，并打包为可迁移、可交接、可审计的 TGravity 资产包。触发方式：/tgravity-export、导出TGravity资产、打包TGravity资产、一键导出资产卡、导出当前项目里的 TGravity 资产。"
---

# TGravity Work Asset Export

你只负责资产导出和打包。

## 边界

- 默认只扫描当前项目或用户明确指定目录。
- 不默认扫描整台电脑、个人文件夹、聊天记录或敏感资料目录。
- 不导出未标记 `tgravity_asset: true` 的普通文件。
- 不导出身份证、银行卡、社保、公章照片、未授权客户隐私、大量视频素材。

## 流程

```text
确认扫描范围
-> 扫描 Markdown YAML 头部
-> 识别 tgravity_asset: true
-> 按 asset_type 分目录复制
-> 校验必填字段
-> 生成 INDEX.csv
-> 生成 MANIFEST.md
-> 生成 EXPORT_SUMMARY.md
-> zip 打包
-> 返回导出路径
```

## 脚本

优先使用：

```bash
python3 scripts/export_assets.py --source <目录> --output <导出根目录>
```

如果用户没有给目录，使用当前项目目录作为 source，并把 output 放到：

```text
tgravity-work-data/exports/
```

如果当前项目目录不明确，只问：

```text
你要导出哪个目录里的 TGravity 资产？请给我一个项目路径。
```

## 导出目录

```text
tgravity-work-data/exports/YYYY-MM-DD_HHMM_TGravity资产包/
├── MANIFEST.md
├── INDEX.csv
├── EXPORT_SUMMARY.md
├── daily/
├── creators/
├── brands/
├── deals/
├── reviews/
├── decisions/
├── escalations/
└── raw/
```

## INDEX.csv 字段

```text
asset_id,asset_type,title,source_path,export_path,owner,business_line,status,risk_level,source_daily_id,last_modified,missing_fields,tags
```

## 校验

导出前或修改脚本后运行：

```bash
python3 scripts/validate_asset_cards.py --source <目录>
```

发现缺字段时，不自动补，只在导出摘要里列出。
