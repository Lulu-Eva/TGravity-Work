# TGravity Asset Cards

## 目标

把日报中的关键对象沉淀为可交接、可导出、可审计的 Markdown 资产卡。

真实业务资产保存到运行项目的 `tgravity-work-data/`，不要保存到 Skill 仓库本体。

`assets/templates/` 中的空模板必须保持 `tgravity_asset: false`。复制模板生成真实资产卡时，先填完 `asset_id`、`title`、`owner` 等必填字段，再改为 `tgravity_asset: true`。

## 统一 YAML 头部

所有 TGravity 资产卡必须包含：

```yaml
---
tgravity_asset: true
asset_id: TGRAVITY-YYYYMMDD-TYPE-001
asset_type:
title:
owner:
business_line: 词元引力
status: draft
risk_level: low
hitl_level: HOTL
created_at:
updated_at:
source:
tags:
---
```

## 首版 asset_type

```text
daily_report
creator_card
brand_lead
deal_progress
deal_review
decision_request
escalation
```

## status

```text
draft
active
pending_decision
closed
archived
```

## risk_level

```text
low
medium
high
```

## hitl_level

```text
HOTL
HITL
human_only
```

## 保存目录

```text
tgravity-work-data/
├── daily/
├── creators/
├── brands/
├── deals/
├── reviews/
├── decisions/
├── escalations/
└── exports/
```

## 生成动作三档

| 用户说法 | 动作 |
|---|---|
| 没明确说生成资产卡 | 只列出建议生成 / 更新的资产卡清单 |
| “生成资产卡” | 输出 Markdown 草稿，不保存 |
| “保存资产卡”或“生成并保存资产卡” | 先确认保存目录，再写入 `tgravity-work-data/` |

保存前必须确认：

```text
我会把资产卡保存到当前项目的 `tgravity-work-data/`。如果要换目录，请告诉我；如果确认，请回复“确认保存”。
```

## 文件命名

```text
日报：YYYY-MM-DD_商务总监日报.md
达人：creator_达人昵称_asset-id.md
品牌：brand_品牌名_asset-id.md
商单：deal_品牌_达人_asset-id.md
决策：decision_主题_asset-id.md
异常：escalation_主题_asset-id.md
```

## 达人画像卡

必填：

```text
达人昵称：
来源：
平台：
内容方向：
用户人群：
当前状态：
商业标签：
适合品牌类型：
交付风险：
维护人：
下一步动作：
```

分层字段：

```text
达人类型：战略型 / 流水型
管理强度：深度孵化 / 轻量维护
是否接入 Eva-Skill：是 / 否
创始人介入级别：高 / 中 / 低
```

战略型达人额外记录：

```text
孵化目标：
商业化方向：
内容定位：
当前阶段：观察期 / 签约期 / 孵化期 / 商业化期
最近一次创始人判断时间：
最近一次创始人判断结论：
```

流水型达人额外记录：

```text
当前合作状态：活跃 / 暂停 / 结束
近三个月商单数量：
近三个月到账金额：
维护成本评估：低 / 中 / 高
```

HITL 触发：

- 要签约。
- 要改变分成规则。
- 要投入创始人深度孵化时间。
- 要把流水型达人升级为战略型达人。
- 要接入 Eva-Skill 做深度内容孵化。

## 品牌线索卡

必填：

```text
品牌名：
来源：
联系人：
需求：
预算口径：
适配达人：
当前阶段：
下一步动作：
是否需要决策：
```

HITL 触发：

- 大额合作。
- 合同条款不清。
- 对外承诺超出常规。
- 品牌风险高。

## 商单推进卡

必填：

```text
品牌：
达人：
平台：
内容形式：
Brief 状态：
报价：
GMV：
公司有效净佣金：
达人分成：
回款状态：
当前阶段：
风险：
下一步动作：
```

HITL 触发：

- 报价低于利润红线。
- 抽成比例变化。
- 合同签署。
- 内容发布前最终审核。
- 回款异常。

## 决策请求卡

必填：

```text
决策事项：
关联对象：
背景：
选项：
推荐：
财务影响：
风险：
截止时间：
需要谁判断：
当前状态：
```

状态：待决策、已决定、暂缓、过期。

## 缺字段处理

缺必填字段时，不要硬补。写入 `缺失字段`，并给用户一个最短补齐问题。

例：

```text
这张品牌线索卡还缺“预算口径”。你可以告诉我：这是已确认预算，还是品牌口头预估？
```
