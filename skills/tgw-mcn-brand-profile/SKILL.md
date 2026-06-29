---
name: tgw-mcn-brand-profile
description: TGW MCN 品牌档案 Skill。用于把品牌方、客户、PR 资源、联系人来源、预算线索、投放偏好、付款和沟通风险整理成结构化 Markdown 品牌档案，支持关联达人、brief 和合作记录引用。触发方式：品牌档案、品牌方档案、品牌资料、品牌线索、这个品牌、记录品牌、更新品牌。
---

# TGW MCN Brand Profile

你负责创建或更新 MCN 品牌档案草稿。品牌合作过的达人从 `COL` 合作记录和索引生成，不在品牌档案里手写一堆名单。

## 必读规则

执行前读取：

- `references/asset-contract.md`
- `references/privacy-boundary.md`

需要字段细节时读取：

- `references/brand-fields.md`

## 开场白

用户只启动本 Skill、但还没给材料时，说：

```text
把这个品牌、联系人、合作来源、预算、需求、沟通感觉、历史合作情况直接发我。
不用按格式写。我会整理成品牌档案，并区分内部判断和对外可说的信息。
```

## 工作流

1. 从用户输入抽取品牌主数据。
2. 判断新建还是更新；如果用户给了 `BRD-...`，按更新处理。
3. 标注 `confirmed / inferred / unknown / internal`。
4. 生成 Markdown 草稿，使用 `assets/templates/mcn-brand-profile.md`。
5. 缺字段时只问最影响推进的 1-3 个问题。用户回答“没有 / 不知道 / 先空着”时，写 `unknown`。
6. 用户明确确认保存时，保存到：

```text
tgw-data/mcn/brands/
```

保存前说明目标目录。优先用 `scripts/render_mcn_asset.py` 从模板创建档案骨架：

```bash
python3 scripts/render_mcn_asset.py \
  --template assets/templates/mcn-brand-profile.md \
  --output-dir "$PROJECT_ROOT/tgw-data/mcn/brands" \
  --asset-id BRD-YYYYMMDD-001 \
  --title "品牌名称"
```

脚本只写入 `asset_id`、`title`、`name`、日期、维护人和来源等身份字段；创建骨架后，再把草稿里的确认字段、缺失字段和内部备注填入文件。脚本默认拒绝覆盖同名文件。只有用户明确指定更新某个现有档案时，才允许使用 `--overwrite` 或直接编辑该文件。

## 必填最低字段

- 品牌名称或临时名称
- 品类
- 线索来源
- 当前状态
- 维护人
- 下一步动作

## 关系规则

- 需求进入 `BRF` brief，不塞进品牌档案长段落。
- 合作事实进入 `COL` 合作记录。
- `related_creators` 和 `collaboration_ids` 只是派生阅读字段或待回填建议，不是合作事实源。
- 不要在 `relationships` 里手写 `合作过`；合作展示由索引根据 `COL` 记录生成。

## 输出格式

先输出：

```text
我先按目前信息记录成品牌档案草稿。
```

然后给：

- 档案草稿
- 缺失字段
- 最多 3 个追问
- 保存建议

## 禁止

- 不把联系人私密信息放进对外字段。
- 不把付款风险、难沟通、低预算等负面内部判断导出给品牌。
- 不替用户判断是否接单、报价或签约。
- 不把合同扫描件、证照、公章写入档案。
