# TGravity Daily Report

## 目标

把商务总监的自然口喷、聊天记录或零散 bullet 整理成日报 Markdown，并列出应生成或更新的资产卡。

## 触发

`/tgravity-daily`、TGravity日报、生成今天日报、保存今天日报、商务总监日报、今天我口喷一下、把这段整理成日报。

## 流程

```text
用户输入
-> 抽取事实
-> 归类：达人 / 品牌 / 商单 / 金额 / 风险 / 决策 / 明日动作
-> 生成日报
-> 列出资产卡清单
-> 标注待补字段
-> 用户明确保存时，写入 tgravity-work-data/daily/
```

## 不得编造

- 对象。
- 金额。
- 回款。
- 合同状态。
- 沟通结果。
- 品牌 Brief。
- 达人承诺。

## 金额口径

必须区分：

```text
GMV
公司有效净佣金
达人分成
已回款
未回款
预算预估
未确认
```

只有实际到账才是已回款。

## 日报模板

使用 `assets/templates/daily-report.md`。不要在本文件维护第二份模板。

## 资产卡动作三档

| 用户说法 | 动作 |
|---|---|
| 未要求生成资产卡 | 只列出“建议生成 / 更新的资产卡清单” |
| “生成资产卡” | 生成资产卡草稿，不写入本地 |
| “保存资产卡”或“生成并保存资产卡” | 先确认保存目录，再按 `references/02_asset-cards.md` 写入 |
 
缺字段时只列清单或草稿，不硬补。

## 资产派生规则

日报中出现以下对象时，列入“建议生成 / 更新的资产卡清单”：

| 日报内容 | 建议动作 |
|---|---|
| 新达人、达人状态变化、达人分层判断 | 更新 `creator_card`，读取 `02_asset-cards.md` |
| 新品牌、品牌状态变化、品牌适配达人 | 更新 `brand_lead`，读取 `06_brand-cards.md` |
| 商单进入报价、合同、执行、验收、回款任一阶段 | 更新 `deal_progress`，读取 `07_deal-pipeline.md` |
| 商单结案、终止、停滞超过 14 天 | 生成 `deal_review` 草稿，读取 `08_deal-review.md` |
| 报价、签约、合同、回款异常、大额商单 | 生成决策请求卡，读取 `04_hitl-hotl-rules.md` |

## 保存规则

默认只输出草稿。

用户明确说“保存”“保存今天日报”“写入 tgravity-work-data”时，才保存日报。

保存前按 `references/shared/save-boundaries.md` 执行两步确认。

保存路径：

```text
tgravity-work-data/daily/YYYY/YYYY-MM/YYYY-MM-DD_商务总监日报.md
```

如需要保存，必须遵守 `references/shared/save-boundaries.md`。
