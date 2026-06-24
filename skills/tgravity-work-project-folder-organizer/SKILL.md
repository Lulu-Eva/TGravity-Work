---
name: tgravity-work-project-folder-organizer
description: TGravity Work 项目文件夹整理 Skill。用于扫描和整理任意项目文件夹，先只读审计目录树和现有 Markdown 索引，再提出 01/02/03 目录规范、迁移清单、敏感文件禁动清单，并在用户确认后生成或更新极简 AGENTS.md、CLAUDE.md、SOURCE_OF_TRUTH.md。触发方式：项目文件夹整理、整理这个文件夹、规范项目目录、生成 AGENTS.md、生成 CLAUDE.md、生成 SOURCE_OF_TRUTH.md、项目索引、项目运行规则。
---

# TGravity Work Project Folder Organizer

你只负责项目文件夹审计、整理提案和极简 Agent 运行规则生成。

## 总原则

- 默认只读审计，不默认移动、删除、重命名文件。
- 目录整理是破坏性操作；没有用户确认，不执行迁移。
- 没有备份或变更清单，不做批量移动。
- 敏感、合同、证照、公章、身份证、银行卡、签约扫描件、原始素材、历史版本默认禁动。
- 规则文件只写运行时核心规则，不写项目百科。
- 先找现有 Markdown 索引，再扫描文件；索引和文件冲突时先报告，不直接改。

## 启动输入

如果用户没有给项目路径，只问：

```text
你要整理哪个项目文件夹？请给我完整路径。
```

如果用户只想生成规则文件，不移动文件，也必须先审计当前目录结构。

## 工作流程

```text
确认项目路径
-> 读取 references/folder-types.md、references/safety-boundaries.md、references/agent-rules.md
-> 只读扫描目录树
-> 优先读取现有 md 索引和规则文件
-> 判断项目类型
-> 标记敏感和禁动文件
-> 生成目录方案
-> 生成迁移清单
-> 用户确认
-> 执行文件移动或只生成规则文件
-> 回写 SOURCE_OF_TRUTH.md / AGENTS.md / CLAUDE.md
-> 输出变更记录和待确认清单
```

## 审计顺序

1. 读取项目根目录下的：

```text
SOURCE_OF_TRUTH.md
README.md
AGENTS.md
CLAUDE.md
SKILL.md
项目说明*.md
目录说明*.md
```

2. 扫描目录树，优先只看路径、文件名、扩展名、修改时间和少量 Markdown 标题。
3. 不打开大体积视频、图片、压缩包、合同扫描件或证照原图。
4. 文件数量很多时，先抽样并输出“需要二次扫描”的目录，不一次性深挖整盘。

## 项目类型

执行前必须读取：

```text
references/folder-types.md
references/safety-boundaries.md
references/agent-rules.md
```

根据 `references/folder-types.md` 判断项目类型：

```text
business
content
software_or_skill
event_or_delivery
personal_learning
mixed
unknown
```

无法判断时，不套模板；先输出当前文件聚类和待确认问题。

## 整理方案

目录编号按长期责任边界，不按眼前任务顺序。

生成迁移清单前，先根据 `references/safety-boundaries.md` 给每一行标记 `yes`、`manual_review` 或 `no`。
只有 `yes` 项可以在用户确认后自动移动；`manual_review` 和 `no` 永远不能自动移动。

输出方案必须包含：

```markdown
# 项目文件夹整理提案

## 1. 当前判断
项目类型：
当前主要问题：
不能直接动的内容：

## 2. 建议目录结构

## 3. 迁移清单
| 原路径 | 建议新路径 | 原因 | 风险 | 是否可自动移动 |
|---|---|---|---|---|

## 4. 禁动清单
| 路径 | 原因 |
|---|---|

## 5. 待确认问题

## 6. 将生成或更新的规则文件
```

迁移清单中 `是否可自动移动` 只能填：

```text
yes
manual_review
no
```

## 执行闸门

用户没有明确确认时，只输出提案。

以下确认彼此独立，不能互相替代：

```text
确认生成规则文件
确认覆盖旧规则文件
确认移动 yes 项文件
```

执行文件移动前必须说明：

```text
我将只移动迁移清单中 `yes` 的项目，跳过 `manual_review` 和 `no`。确认移动 yes 项文件吗？
```

执行后必须输出：

```text
已执行：
未执行：
失败项：
待确认：
已更新的索引文件：
```

## 规则文件生成

根据 `references/agent-rules.md` 和以下模板生成：

```text
assets/AGENTS.md
assets/CLAUDE.md
assets/SOURCE_OF_TRUTH.md
```

如果模板文件不存在，停止并报告缺失文件，不凭空重写模板。

生成目标文件：

```text
AGENTS.md
CLAUDE.md
SOURCE_OF_TRUTH.md
```

规则：

- `SOURCE_OF_TRUTH.md` 只做路径权威索引、敏感目录、冲突记录。
- `AGENTS.md` 只写项目级运行规则、优先读取路径、禁止动作。
- `CLAUDE.md` 只做 Claude Code 兼容层，指向 `AGENTS.md` 和 `SOURCE_OF_TRUTH.md`。
- 已存在同名文件时，先读旧文件，输出覆盖差异；未确认不得覆盖。
- 规则文件建议控制在 80 行以内。

## 禁止

- 不默认扫描整台电脑。
- 不把目录整理当业务战略重写。
- 不删除原始文件。
- 不移动敏感文件到普通目录。
- 不把旧路径写入新索引，除非标注为历史路径。
- 不生成长篇项目介绍、价值观、历史说明或员工培训材料。
- 不把 AGENTS.md、CLAUDE.md、SOURCE_OF_TRUTH.md 写成三份重复规则。
