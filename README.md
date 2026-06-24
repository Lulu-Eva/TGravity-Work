# TGravity Work Skills

TGravity Work Skills 是词元引力内部经营记录、资产交接和公开网页搜索 Skill 包。它面向词元引力员工，帮助员工先判断一项工作的人机分工，再把日常口喷、品牌线索、达人信息、商单推进、复盘记录整理成可保存、可导出、可交接的 Markdown 资产；需要公开资料搜索时，单独使用 `tgravity-work-search`。

当前版本：`v0.1.6`

## 包含的 Skill

- `tgravity-work`：通用新手学习、开工审查、日报、资产卡、商单推进、复盘和资产导出。
- `tgravity-work-search`：基于 Perplexity API 的公开网页搜索、资料核验、竞品/品牌/达人公开资料调研。

## 能做什么

- 新员工通用学习：用 `/tgravity-onboarding` 或“开启新手教程”进入学习模式，根据员工反馈调整下一步。
- 使用者信息卡：第一次使用先确认“我该怎么称呼你”，后续日报自动带入提交人。
- 开工前工作审查：用 `/tgravity-workcheck` 判断一件工作 AI 能不能做、该怎么配合、应该用 Codex / WorkBuddy / Manus 哪个工具。
- 工作日报整理：把自然口喷整理成结构化日报。
- 达人资产卡：区分战略型达人和流水型达人，记录管理强度和是否接入 Eva-Skill。
- 品牌线索卡：记录品牌画像、对接状态、适配达人和历史合作。
- 商单推进：用状态机追踪从线索到回款的完整过程。
- 商单复盘：在结案、终止或长期停滞后沉淀复盘。
- 决策升级：报价、签约、合同、回款异常等事项触发 HITL。
- 资产导出：把标记为 `tgravity_asset: true` 的资产卡打包为可迁移资产包。
- 公开资料搜索：用 `/tgravity-search` 调用 Perplexity Search API，输出带来源 URL 的搜索结果。

## 不能做什么

- 不能替人做最终商务判断。
- 不能替公司对外承诺报价、合同条款、退款、回款或合作结果。
- 不能默认扫描整台电脑。
- 不能默认保存真实客户、品牌、员工隐私资料。
- 不能把证照、公章、身份证、银行卡、合同扫描件等敏感材料写入公开仓库。
- 不能把 Perplexity API Key 写进 GitHub 仓库、README、资产卡或导出包。

## 安装

推荐使用和 Eva-skill 一样的安装方式：

```bash
npx skills add Lulu-Eva/TGravity-Work -g -y
```

只安装搜索 Skill：

```bash
npx skills add Lulu-Eva/TGravity-Work -g -y --skill tgravity-work-search
```

重新安装即可更新：

```bash
npx skills add Lulu-Eva/TGravity-Work -g -y
```

安装后重启对应 Agent 应用。

## GitHub 安装备用方式

如果不使用 `skills` 安装器，也可以从 GitHub 安装到 Codex：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo Lulu-Eva/TGravity-Work --path skills/tgravity-work
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo Lulu-Eva/TGravity-Work --path skills/tgravity-work-search
```

## 常用触发词

```text
/tgravity-onboarding
/tgravity-profile
/tgravity-workcheck
/tgravity-task
/tgravity-daily
/tgravity-export
/tgravity-search
/tgravity-search-init
/tgravity-search-status
开工前检查
开启新手教程
带我学TGravity Work
继续下一课
工作审查
工作任务拆解
这件工作你能做吗
这件工作AI能做吗
帮我拆工作
TGravity日报
TGravity搜索
Perplexity搜索
帮我查资料
核验这个信息
品牌线索
商单推进
商单复盘
导出TGravity资产
决策请求
需要璐璐判断
```

## 新员工第一次怎么用

先输入：

```text
/tgravity-onboarding
```

首次使用时，Skill 会先问“我该怎么称呼你？”。员工回答称呼后，再进入学习诊断。不要一开始就让员工理解 Agent、Skill、Markdown、资产卡、HITL 这些概念。先让员工选择最想学的模块，再按反馈推进。

也可以直接说：

```text
开启新手教程
```

新手教程不是固定脚本。它会根据员工反馈，在“完全新手、工作分配、日报生成、搜索技能、人机边界”之间调整下一步。

员工准备做任何新工作时，先输入：

```text
/tgravity-workcheck 我想做【这件工作】，请先判断 AI 能不能做，并拆分我和 AI 各自该做什么。
```

Skill 会先把工作定义清楚，再给出人类、Codex、WorkBuddy、Manus 的分工建议。

## 当前四个核心功能

### 1. 新手教程

当你不知道怎么使用 TGravity Work 时，说“开启新手教程”。它会进入学习模式，先判断你现在想学哪一块，再一步一步带你练。

### 2. 日报生成

你把今天干了什么告诉它，它会整理成 Markdown 日报。你不需要每天写作文；如果攒了一堆事，直接用语音转文字口喷给它即可。

### 3. 工作分配技能

这是工作前置要求。开展某项工作前，先用 `/tgravity-workcheck`。它会定义当前工作内容，再拆出哪些适合 AI 处理，哪些适合人类完成。

### 4. 搜索技能

需要公开互联网资料、近期信息核验、竞品/品牌/达人公开资料调研时，用 `/tgravity-search`。搜索 Skill 外接 Perplexity API，追求专业性和来源可追溯。Codex 使用时需要允许运行脚本和联网；如果权限受限，先切到完全访问权限或让管理员配置。

## 搜索 Skill 第一次怎么用

先输入：

```text
/tgravity-search-status
```

如果这台电脑还没配置 Perplexity API Key，Skill 会要求你提供。API Key 只保存到本机：

```text
~/.config/tgravity-work-search/config.json
```

公开 GitHub 仓库不包含 API Key。不要把 API Key 发进日报、资产卡、README 或任何要提交到 GitHub 的文件。

真实搜索示例：

```text
/tgravity-search 帮我查 2026 年小红书 AI 垂类 MCN 的公开竞品资料，列出来源链接。
```

## 真实日报示例

```text
/tgravity-daily
今天跟 A 达人聊了合作，她愿意试运行。B 品牌有一单预算 5000 到 8000 的测评，还没给 Brief。今天没有回款。需要璐璐判断 A 达人抽成比例。明天催 B 品牌 Brief。
```

Skill 会先确认提交人称呼，再整理日报，并提示建议生成或更新哪些资产卡。

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
- `tgravity-work-search-data/`
- 导出 zip
- 真实日报
- 真实品牌资料
- 员工或客户隐私
- 证照、公章、合同扫描件

## 维护

修改 Skill 后至少执行：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/tgravity-work
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/tgravity-work-search
python3 skills/tgravity-work/scripts/validate_asset_cards.py --source skills/tgravity-work/assets/templates
python3 skills/tgravity-work-search/scripts/perplexity_search.py --status
```

如修改资产类型，还要测试：

```bash
python3 skills/tgravity-work/scripts/export_assets.py --source <测试资产目录> --output <测试导出目录>
```

## 仓库结构

```text
TGravity-Work/
├── .claude-plugin/
│   └── marketplace.json
├── README.md
├── VERSION
└── skills/
    ├── tgravity-work/
    │   ├── SKILL.md
    │   ├── assets/
    │   ├── references/
    │   └── scripts/
    └── tgravity-work-search/
        ├── SKILL.md
        ├── references/
        └── scripts/
```
