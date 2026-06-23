# TGravity Work Skill

TokenGravity Work Skill 是词元引力内部经营记录与资产交接 Skill。它面向商务总监和新员工，帮助把日常口喷、品牌线索、达人信息、商单推进、复盘记录整理成可保存、可导出、可交接的 Markdown 资产。

当前版本：`v0.1.2`

## 能做什么

- 新员工分步上手：用 `/tgravity-onboarding` 带着员工一步一步学会使用。
- 商务日报整理：把自然口喷整理成结构化日报。
- 达人资产卡：区分战略型达人和流水型达人，记录管理强度和是否接入 Eva-Skill。
- 品牌线索卡：记录品牌画像、对接状态、适配达人和历史合作。
- 商单推进：用状态机追踪从线索到回款的完整过程。
- 商单复盘：在结案、终止或长期停滞后沉淀复盘。
- 决策升级：报价、签约、合同、回款异常等事项触发 HITL。
- 资产导出：把标记为 `tgravity_asset: true` 的资产卡打包为可迁移资产包。

## 不能做什么

- 不能替人做最终商务判断。
- 不能替公司对外承诺报价、合同条款、退款、回款或合作结果。
- 不能默认扫描整台电脑。
- 不能默认保存真实客户、品牌、员工隐私资料。
- 不能把证照、公章、身份证、银行卡、合同扫描件等敏感材料写入公开仓库。

## npx 安装

正式 npm 包发布后，默认安装到 Codex 常见用户级 Skill 目录：

```bash
npx -y tgravity-work
```

安装到 Claude Code：

```bash
npx -y tgravity-work --target claude
```

安装到 CodeBuddy/WorkBuddy：

```bash
npx -y tgravity-work --target codebuddy
```

如果员工实际使用的客户端叫 WorkBuddy：

```bash
npx -y tgravity-work --target workbuddy
```

同时安装到 Codex、Claude Code、CodeBuddy、WorkBuddy：

```bash
npx -y tgravity-work --target all
```

覆盖旧版本：

```bash
npx -y tgravity-work --target all --force
```

自定义安装目录：

```bash
npx -y tgravity-work --dest ~/.agents/skills/tgravity-work --force
```

如果某个客户端实际识别的 Skill 目录和默认值不一致，用 `--dest` 指向该客户端的 Skill 目录。

安装后重启对应 Agent 应用。

## GitHub npx 临时安装

在 npm 包正式发布前，可以直接从 GitHub 执行安装器：

```bash
npx -y github:Lulu-Eva/TGravity-Work
```

安装到 Claude Code：

```bash
npx -y github:Lulu-Eva/TGravity-Work --target claude
```

安装到 CodeBuddy/WorkBuddy：

```bash
npx -y github:Lulu-Eva/TGravity-Work --target codebuddy
```

或：

```bash
npx -y github:Lulu-Eva/TGravity-Work --target workbuddy
```

覆盖旧版本：

```bash
npx -y github:Lulu-Eva/TGravity-Work --target all --force
```

## GitHub 安装备用方式

如果不使用 npx，也可以从 GitHub 安装到 Codex：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo Lulu-Eva/TGravity-Work --path .
```

## 常用触发词

```text
/tgravity-onboarding
/tgravity-daily
/tgravity-export
TGravity日报
品牌线索
商单推进
商单复盘
导出TGravity资产
决策请求
需要徒左判断
需要璐璐判断
```

## 新员工第一次怎么用

先输入：

```text
/tgravity-onboarding
```

然后按 Skill 的提示回复“开始”。不要一开始就让员工理解 Agent、Skill、Markdown、资产卡、HITL 这些概念。先让员工跑通一条训练日报。

## 真实日报示例

```text
/tgravity-daily
今天跟 A 达人聊了合作，她愿意试运行。B 品牌有一单预算 5000 到 8000 的测评，还没给 Brief。今天没有回款。需要徒左判断 A 达人抽成比例。明天催 B 品牌 Brief。
```

Skill 会整理日报，并提示建议生成或更新哪些资产卡。

## 资产卡规则

真实业务资产卡使用 YAML 头部：

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

`assets/templates/` 下的模板必须保持 `tgravity_asset: false`。复制模板生成真实资产卡时，先填完必填字段，再改为 `tgravity_asset: true`。

## 资产导出

触发：

```text
/tgravity-export 导出当前项目里的 TGravity 资产
```

导出脚本只扫描用户指定目录中的 Markdown 文件，只导出 `tgravity_asset: true` 的资产卡，并生成：

- `INDEX.csv`
- `MANIFEST.md`
- `EXPORT_SUMMARY.md`
- zip 资产包

## 人机边界

核心规则：

```text
AI 可以整理，不能承诺。
```

以下情况必须让人拍板：

- 报价超出达人历史报价区间 ±30%。
- 合同涉及独家、排他或长期绑定。
- 品牌要求达人修改已发布内容。
- 回款逾期超过 14 天。
- 达人提出终止合作或更换条款。
- 品牌出现负面舆情或法律风险信号。
- 单笔商单金额超过 5 万元。
- 流水型达人升级为战略型达人。
- 战略型达人接入 Eva-Skill 深度孵化。

## 仓库边界

这个仓库只保存 Skill 工具本体，不保存真实业务数据。

不要提交：

- `tgravity-work-data/`
- `tgravity-work-exports/`
- 导出 zip
- 真实日报
- 真实品牌资料
- 员工或客户隐私
- 证照、公章、合同扫描件

## 维护

修改 Skill 后至少执行：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
python3 scripts/validate_asset_cards.py --source assets/templates
```

如修改资产类型，还要测试：

```bash
python3 scripts/export_assets.py --source <测试资产目录> --output <测试导出目录>
```
