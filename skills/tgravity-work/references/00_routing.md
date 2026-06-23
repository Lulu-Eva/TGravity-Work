# TGravity Routing Fallback

本文件只处理冲突、兜底和低置信度路由。常规触发词以 `SKILL.md` 为准。

## 冲突优先级

0. 如果当前对话正在 `/tgravity-onboarding` 带练，用户复制训练示例触发词时，继续按 `05_onboarding-manual.md`；不要切到正式工作入口。
1. 用户明确触发 `/tgravity-onboarding`、`/tgravity-daily`、`/tgravity-export` 时，进入对应入口。
2. 用户明确触发 `/tgravity-workcheck`、`/tgravity-task`，或问“这件工作你能做吗”“这件工作 AI 能不能做”“帮我拆工作”“我该用哪个 Agent 做”，进入 `10_workcheck-task-split.md`。
3. 用户涉及报价、签约、合同、回款异常、退款坏账、对外承诺时，进入 HITL 决策升级。
4. 用户涉及品牌线索、品牌状态、品牌适配达人时，读取 `06_brand-cards.md`。
5. 用户涉及商单状态、推进卡点、回款追踪、状态停留时间时，读取 `07_deal-pipeline.md`。
6. 用户涉及结案、终止、复盘、经验沉淀时，读取 `08_deal-review.md`。
7. 用户涉及达人分层、战略型/流水型、是否接入 Eva-Skill 时，读取 `02_asset-cards.md`。
8. 用户明显是在口喷每日商务进展时，进入日报。
9. 用户明显在问怎么用、不会用、刚入职、看不懂 Agent / Skill 时，进入入职教学。

保存、写入、导出、打包是叠加约束，不单独决定主入口。命中这些词时，同时读取 `shared/save-boundaries.md`；导出资产包时读取 `03_asset-export.md`。

## 日报识别

输入满足以下任意 3 项，可按日报处理：

- 提到“今天 / 明天 / 本周”等时间。
- 提到达人、品牌、商单、客户、回款、Brief、报价任一对象。
- 包含已完成动作。
- 包含下一步动作。
- 包含需要璐璐或用户指定判断人判断的事项。

低于 3 项时只问：

```text
你这段是要整理成今天日报，还是只是先聊一下？
```

## 新手语言替换

| 术语 | 对新员工说 |
|---|---|
| Agent | 助手 |
| Skill | 工具包 / 工作说明书 |
| Asset card | 重要事项记录卡 |
| Export package | 打包好的资料包 |
| HITL | 必须让人拍板 |
| HOTL | AI 先整理，人检查 |

## 不确定时

只问一个问题：

```text
你这次是想先拆这项工作、整理日报、更新品牌/商单记录，还是让我带你学怎么用？
```
