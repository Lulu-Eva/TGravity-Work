# TGravity Work Skills

TGravity Work Skills 是词元引力内部工作协作 Skill 包。

当前结构采用“主入口只路由、子 Skill 独立工作”的设计：`tgravity-work` 只负责判断用户该用哪个子 Skill，不做目标规范、提示词优化、提示词架构、日报、资产卡、MCN 资产、搜索、视频、科技画布、发票、项目审视或文件夹整理。

当前阶段：`0.1 beta`

版本规则：未发布到 GitHub 的本地修改不递增版本号。`VERSION` 只代表对外发布包版本。

## 安装

全量安装：

```bash
npx skills add Lulu-Eva/TGravity-Work -g -y
```

只安装单个 Skill：

```bash
npx skills add Lulu-Eva/TGravity-Work -g -y --skill tgravity-work-search
```

安装后重启对应 Agent 应用。

## 包含的 Skill

| Skill | 用途 |
|---|---|
| `tgravity-work` | 主入口，只路由，不做具体任务 |
| `tgravity-work-onboarding` | 新员工小白入门、动态教学、操作手册 |
| `tgravity-work-profile` | 本机使用者称呼、日报提交人、默认决策对象 |
| `tgravity-work-goal` | 混乱目标、问题或 AI 委托改写成 Agent 可用目标提示词 |
| `tgravity-work-prompt-optimizer` | 精简完整提示词，压缩冗余规则、重复表达和防御性指令 |
| `tgravity-work-prompt-architect` | 审核提示词架构，或从语料生成可执行智能体提示词框架 |
| `tgravity-work-workcheck` | 开工前工作审查、任务定义、人机分工 |
| `tgravity-work-daily-report` | 口喷、语音转文字、流水账整理成 Markdown 日报 |
| `tgravity-work-asset-cards` | 达人卡、品牌卡、商单卡、复盘卡、决策请求卡 |
| `tgravity-work-mcn` | MCN 资产系统主入口，只路由达人、品牌、Brief、合作记录和索引 |
| `tgravity-work-mcn-creator-profile` | MCN 达人档案采集、补全、内部/对外字段隔离 |
| `tgravity-work-mcn-brand-profile` | MCN 品牌档案采集、预算线索、投放偏好和风险记录 |
| `tgravity-work-mcn-brief-builder` | 品牌模糊需求整理成逆向 Brief 和达人匹配草稿 |
| `tgravity-work-mcn-collaboration` | 品牌-达人合作记录事实表，支撑互链和合作历史查询 |
| `tgravity-work-mcn-index` | 重建 MCN 关系索引、品牌-达人矩阵、达人合作历史和 Markdown 双链 |
| `tgravity-work-asset-export` | 扫描 `tgravity_asset: true` 并打包导出资产 |
| `tgravity-work-preflight-review` | 大项目行动前审视，60/80/120 和 11 问闸门 |
| `tgravity-work-search` | Perplexity + Tavily 双引擎公开网页搜索 |
| `tgravity-work-video-indexer` | 视频素材索引、逐字稿对齐、contact sheet、切片表 |
| `tgravity-work-tech-canvas-video` | 已剪好气口的人像视频 + 逐字稿 -> 本地 HTML 科技画布 -> 可验收背景动画 MP4 |
| `tgravity-work-invoice-reimbursement` | 文本型 PDF 发票报销整理、去重和复查 |
| `tgravity-work-project-folder-organizer` | 项目文件夹审计、目录整理提案、极简 AGENTS/CLAUDE/SOURCE_OF_TRUTH 生成 |

## 常用触发词

```text
/tgravity
/tgravity-work
开启新手教程
我该怎么称呼你
目标提示词
目标规范
提示词优化
提示词精简
优化算法
提示词架构
提示词审核
生成提示词框架
倒推提示词
开工前检查
工作任务拆解
TGravity日报
生成今天日报
品牌线索
达人卡
商单推进
商单复盘
MCN资产
达人档案
品牌档案
逆向brief
合作记录
品牌达人互链
MCN关系索引
导出TGravity资产
大项目行动前审视
搜索技能
视频分析技能
科技画布
Codex剪视频
发票报销
项目文件夹整理
生成 AGENTS.md
```

## 新员工第一次怎么用

输入：

```text
开启新手教程
```

新手教程会先识别当前安装的 TGravity 子 Skill，再按员工需求一步一步带练。它不是固定讲稿。

## 目标提示词规范

当你的表达还停在“我想做大”“我要做个人 IP”“这个问题怎么交给 AI”这种半成形状态时，先用：

```text
目标提示词：{把你脑子里的原话丢进来}
```

这个 Skill 只把目标、问题或 AI 委托规范成可检查、可交给 Agent 的目标提示词，不拆任务、不分配工作、不生成执行方案。目标清楚后，才交给 `tgravity-work-workcheck` 做任务审查。

## 提示词功能

提示词这一块有两个子功能：

| 功能 | Skill | 适用场景 |
|---|---|---|
| 优化算法 | `tgravity-work-prompt-optimizer` | 已经有一份完整提示词，要在不改变原意的前提下压缩、删减、重排 |
| 架构师 | `tgravity-work-prompt-architect` | 要审核提示词结构，或从语料、角色说明、输出样例生成提示词框架 |

优化已有提示词时，使用：

```text
提示词优化：{贴完整提示词}
```

这个 Skill 会一问一停地走质疑需求、删减、简化、加速、模板化和精简报告，不会给提示词新增原本没有的能力。

当你要检查一个提示词是否结构自洽，或从语料倒推出可执行的智能体提示词框架时，使用：

```text
提示词架构：{贴提示词、语料、角色说明或输出样例}
```

这个 Skill 只处理提示词内部逻辑，不做普通文案润色，不在提示词正文里写外部出处或制作过程。

## 大项目行动前审视

当你准备投入大量时间、金钱、精力，或遇到业务转型、方向调整、反复纠结、做了一半感觉跑偏时，输入：

```text
大项目行动前审视：我正在考虑【事情】，帮我过一遍。
```

这个 Skill 会先判断是否值得跑框架，再强制选择 60 / 80 / 120 交付级别，然后一问一停跑 11 问。5 分钟内能做完的小事不要用它。

## MCN 资产系统

MCN 资产系统采用“一个入口、多独立 Skill、共享数据契约”的设计。统一入口：

```text
/tgravity-mcn
```

也可以直接触发具体能力：

```text
达人档案：今天这个达人是……
品牌档案：这个品牌的情况是……
逆向brief：品牌这次想投……
合作记录：某品牌和某达人这次合作结果是……
MCN关系索引：重建品牌达人互链
```

核心规则：

- 达人档案和品牌档案是主数据。
- 逆向 Brief 是需求资产。
- 合作记录是品牌-达人合作历史的事实表；真实合作只以 `COL` 的 `brand_id`、`creator_id` 和 `brief_id` 为准。
- 关系索引、品牌-达人矩阵、达人合作历史和正文 `[[双链]]` 都是从 YAML frontmatter 派生的视图。
- `related_brands`、`related_creators`、`collaboration_ids` 只是派生阅读字段或待回填建议，不是合作事实源。
- 建档类子 Skill 确认保存时使用本地 `scripts/render_mcn_asset.py` 创建模板骨架，默认拒绝覆盖，也拒绝把运行时资产写进 Skill 包目录；业务字段需要在骨架创建后写入草稿文件。
- `shared/mcn/` 是 MCN 契约和建档脚本的开发真源；发版前运行 `python3 shared/mcn/sync_shared_resources.py --check`，有漂移先运行不带 `--check` 的同步命令再测试。
- 不用中文名做主键，使用稳定 ID：`CRT / BRD / BRF / COL`。

默认运行数据目录：

```text
tgravity-work-data/mcn/
├── creators/
├── brands/
├── briefs/
├── collaborations/
├── indexes/
└── exports/
```

重建索引：

```bash
python3 skills/tgravity-work-mcn-index/scripts/mcn_index.py --root "<项目根目录>"
```

填充 Markdown 双链：

```bash
python3 skills/tgravity-work-mcn-index/scripts/mcn_index.py --root "<项目根目录>" --fill-links --dry-run
python3 skills/tgravity-work-mcn-index/scripts/mcn_index.py --root "<项目根目录>" --fill-links
```

先跑 `--dry-run` 看会改多少源 Markdown。正式 `--fill-links` 会在写入前把被改文件备份到 `tgravity-work-data/mcn/.backups/fill-links-*`；不要在没有 Git 或备份的项目里使用 `--no-backup`。

## 搜索 Skill 初始化

搜索 Skill 需要两个 API Key：

```text
Perplexity API Key
Tavily API Key
```

初始化：

```text
搜索技能，初始化搜索。
这是 Perplexity API Key：******
这是 Tavily API Key：******
```

API Key 只保存到本机：

```text
~/.config/tgravity-work-search/config.json
```

公开 GitHub 仓库不保存 API Key。

## 视频 Skill 环境

视频 Skill 依赖：

```bash
ffmpeg
ffprobe
python3 -m pip install --user pillow
```

检查：

```text
/tgravity-video-check
```

## 科技画布视频 Skill 环境

科技画布视频 Skill 默认不调用腾讯云 ASR。生产模式推荐先提供已剪好气口的 `input/source.mp4`，以及 `input/script.md`、`input/script.srt` 或 `input/script.vtt`；没有脚本时可用本地 Python `whisper` 从 `input/source.mp4` 生成逐字稿草案。

本 Skill 不是“一键成片”系统，不负责调研、TTS、素材生成、音乐、字幕或人像合成。它负责生成可在剪映中叠人像的科技画布背景动画 MP4，并输出机器验收报告。

确定交付：

```text
analysis/script_segments.json
analysis/timeline.json
input/script.srt（走本地转写时）
input/script.vtt（用户提供 VTT 时）
analysis/transcript.json（走本地转写时）
overview/index.html
hyperframes/index.html
output/background.mp4
output/render_report.json
output/validation_report.json
output/production_manifest.json
output/validation_frames/
```

`input/source.mp4` 用于锁定背景动画时长。默认渲染链路是 Chrome 逐帧截图 + FFmpeg 编码，不调用 `npx hyperframes render`。

检查：

```text
/tgravity-tech-video-check
```

生产：

```bash
python3 skills/tgravity-work-tech-canvas-video/scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style cyber-blueprint
```

## 发票 Skill 环境

发票 Skill 依赖：

```bash
python3 -m pip install --user openpyxl pdfminer.six
```

第一版只承诺处理可抽取文本的 PDF。扫描件、图片发票和原生 OFD 会列为待处理或识别失败，不会硬猜。

## 项目文件夹整理

当你要整理某个项目目录，或想给项目生成极简 Agent 运行规则时，输入：

```text
项目文件夹整理：/完整/项目/路径
```

这个 Skill 会先只读扫描目录和现有 Markdown 索引，再输出目录方案、迁移清单和禁动清单。用户确认前不会移动文件。

## 不能做什么

- 不能替人做最终商务判断。
- 不能替公司对外承诺报价、合同条款、退款、回款或合作结果。
- 不能默认扫描整台电脑。
- 不能默认保存真实客户、品牌、员工隐私资料。
- 不能把证照、公章、身份证、银行卡、合同扫描件等敏感材料写入公开仓库。
- 不能把 Perplexity API Key 或 Tavily API Key 写进 GitHub 仓库、README、资产卡或导出包。
- 不能把未授权视频、逐字稿、缩略图或切片表写进 GitHub 仓库。
- 不能把真实发票、报销表、公司税号、OCR 密钥写进 GitHub 仓库。
- 不能在未确认迁移清单前移动、删除或重命名项目文件。

## 本地运行数据

以下内容必须留在本机，不提交 GitHub：

```text
tgravity-work-data/
tgravity-work-data/mcn/
tgravity-work-exports/
tgravity-work-search-data/
视频素材工作区/
发票下载/
发票填写*.xlsx
发票填写*_复查报告.md
```

## 开发校验

```bash
for skill in skills/tgravity-work skills/tgravity-work-onboarding skills/tgravity-work-profile skills/tgravity-work-goal skills/tgravity-work-prompt-optimizer skills/tgravity-work-prompt-architect skills/tgravity-work-workcheck skills/tgravity-work-daily-report skills/tgravity-work-asset-cards skills/tgravity-work-mcn skills/tgravity-work-mcn-creator-profile skills/tgravity-work-mcn-brand-profile skills/tgravity-work-mcn-brief-builder skills/tgravity-work-mcn-collaboration skills/tgravity-work-mcn-index skills/tgravity-work-asset-export skills/tgravity-work-preflight-review skills/tgravity-work-search skills/tgravity-work-video-indexer skills/tgravity-work-tech-canvas-video skills/tgravity-work-invoice-reimbursement skills/tgravity-work-project-folder-organizer; do
  python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill"
done

python3 skills/tgravity-work-asset-export/scripts/validate_asset_cards.py --source tests/fixtures/asset-cards
python3 skills/tgravity-work-search/scripts/dual_search.py --status
python3 skills/tgravity-work-video-indexer/scripts/video_pipeline.py check --json
python3 skills/tgravity-work-tech-canvas-video/scripts/tech_canvas_pipeline.py check --json
python3 skills/tgravity-work-invoice-reimbursement/scripts/invoice_reimbursement.py check
python3 tests/smoke_tgravity_work.py --quick
```

科技画布生产链路需要 `input/source.mp4` 和 `input/script.md` / `input/script.srt` / `input/script.vtt`，然后运行 `produce -> validate`；无脚本时可在用户允许后加 `--transcribe-if-missing`。
