# Decision Request Card

## 触发条件

出现以下事项时生成决策请求卡：

- 报价。
- 抽成比例变化。
- 签约。
- 合同。
- 回款异常。
- 退款坏账。
- 对外承诺。
- 声誉风险。
- 资源排期冲突。
- 是否占用璐璐或用户指定判断人深度时间。

## 模板

```md
---
tgravity_asset: true
asset_id:
asset_type: decision_request
title:
owner:
business_line: 词元引力
status: pending_decision
risk_level:
hitl_level: HITL
created_at:
updated_at:
source:
tags:
---

# 决策请求卡

## 决策事项

## 关联对象

## 背景

## 为什么需要人判断

## 可选方案

| 方案 | 好处 | 风险 | 财务影响 |
|---|---|---|---|

## 推荐

## 截止时间

## 需要谁判断

## 当前状态
```
