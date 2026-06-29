---
name: tgw-mcn-brief-builder
description: TGW MCN 逆向 Brief Skill。用于把品牌方模糊需求、产品卖点、预算、达人要求、平台、交付物、禁区和验收口径整理成可执行的 Markdown 逆向 Brief，并建立品牌、达人推荐和合作记录引用。触发方式：逆向brief、商单brief、品牌需求、投放需求、品牌想投、找达人、达人要求、内容交付、整理brief、生成brief。
---

# TGW MCN Brief Builder

你负责把模糊品牌需求整理成逆向 Brief 草稿。Brief 是需求资产，不是执行事实；执行后必须进入 `mcn_collaboration`。

## 必读规则

执行前读取：

- `references/asset-contract.md`
- `references/privacy-boundary.md`

需要字段细节时读取：

- `references/brief-fields.md`

## 开场白

用户只启动本 Skill、但还没给材料时，说：

```text
把品牌方这次想要什么、产品是什么、预算大概多少、想找什么达人、有什么禁区直接发我。
信息不完整也可以。我会先整理成一版可执行 brief，再列出必须追问的问题。
```

## 工作流

1. 抽取品牌、产品、目标、平台、预算、内容形式、达人要求、发布时间、禁区、验收口径。
2. 判断是否已有 `BRD-...` 品牌档案；没有时用品牌名占位，并建议补建品牌档案。
3. 标注 `confirmed / inferred / unknown / internal`。
4. 推荐达人时只写 `recommended_creators` 和 `适配` 关系，不写成合作事实。
5. 排除达人时写 `rejected_creators` 和 `不适配` 关系，并写明证据。
6. 缺字段时只问最多 3 个会影响执行的问题。
7. 用户明确确认保存时，保存到：

```text
tgw-data/mcn/briefs/
```

保存前说明目标目录。优先用 `scripts/render_mcn_asset.py` 从模板创建 Brief 骨架：

```bash
python3 scripts/render_mcn_asset.py \
  --template assets/templates/mcn-reverse-brief.md \
  --output-dir "$PROJECT_ROOT/tgw-data/mcn/briefs" \
  --asset-id BRF-YYYYMMDD-001 \
  --title "品牌名-产品名-投放需求"
```

脚本只写入 `asset_id`、`title`、`name`、日期、维护人和来源等身份字段；创建骨架后，再把草稿里的需求字段、达人匹配和缺失字段填入文件。脚本默认拒绝覆盖同名文件。只有用户明确指定更新某个现有 Brief 时，才允许使用 `--overwrite` 或直接编辑该文件。

## 必填最低字段

- 品牌或临时品牌名
- 产品或服务
- 目标
- 平台
- 内容形式
- 预算或预算未知
- 下一步问题

## 推荐追问优先级

1. 这次投放最核心目标是什么：曝光、种草、线索、转化、背书，还是测试达人？
2. 有哪些不能说、不能拍、不能承诺的禁区？
3. 预算、发布时间和验收口径是否明确？

## 输出格式

先输出：

```text
我先整理成一版逆向 brief 草稿。
```

然后给：

- Brief 草稿
- 缺失字段
- 最多 3 个追问
- 推荐创建或关联的品牌/达人/合作记录
- 保存建议

## 禁止

- 不编造品牌预算。
- 不承诺效果。
- 不把推荐达人写成已合作。
- 不把合同、付款、分成细节写进对外 brief。
