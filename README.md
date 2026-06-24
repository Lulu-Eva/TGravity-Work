# TGravity Work Skills

TGravity Work Skills 是词元引力内部工作协作 Skill 包。

当前结构采用“主入口只路由、子 Skill 独立工作”的设计：`tgravity-work` 只负责判断用户该用哪个子 Skill，不做日报、资产卡、搜索、视频、发票、项目审视或文件夹整理。

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
| `tgravity-work-workcheck` | 开工前工作审查、任务定义、人机分工 |
| `tgravity-work-daily-report` | 口喷、语音转文字、流水账整理成 Markdown 日报 |
| `tgravity-work-asset-cards` | 达人卡、品牌卡、商单卡、复盘卡、决策请求卡 |
| `tgravity-work-asset-export` | 扫描 `tgravity_asset: true` 并打包导出资产 |
| `tgravity-work-preflight-review` | 大项目行动前审视，60/80/120 和 11 问闸门 |
| `tgravity-work-search` | Perplexity + Tavily 双引擎公开网页搜索 |
| `tgravity-work-video-indexer` | 视频素材索引、逐字稿对齐、contact sheet、切片表 |
| `tgravity-work-invoice-reimbursement` | 文本型 PDF 发票报销整理、去重和复查 |
| `tgravity-work-project-folder-organizer` | 项目文件夹审计、目录整理提案、极简 AGENTS/CLAUDE/SOURCE_OF_TRUTH 生成 |

## 常用触发词

```text
/tgravity
/tgravity-work
开启新手教程
我该怎么称呼你
开工前检查
工作任务拆解
TGravity日报
生成今天日报
品牌线索
达人卡
商单推进
商单复盘
导出TGravity资产
大项目行动前审视
搜索技能
视频分析技能
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

## 大项目行动前审视

当你准备投入大量时间、金钱、精力，或遇到业务转型、方向调整、反复纠结、做了一半感觉跑偏时，输入：

```text
大项目行动前审视：我正在考虑【事情】，帮我过一遍。
```

这个 Skill 会先判断是否值得跑框架，再强制选择 60 / 80 / 120 交付级别，然后一问一停跑 11 问。5 分钟内能做完的小事不要用它。

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
tgravity-work-exports/
tgravity-work-search-data/
视频素材工作区/
发票下载/
发票填写*.xlsx
发票填写*_复查报告.md
```

## 开发校验

```bash
for skill in skills/tgravity-work skills/tgravity-work-onboarding skills/tgravity-work-profile skills/tgravity-work-workcheck skills/tgravity-work-daily-report skills/tgravity-work-asset-cards skills/tgravity-work-asset-export skills/tgravity-work-preflight-review skills/tgravity-work-search skills/tgravity-work-video-indexer skills/tgravity-work-invoice-reimbursement skills/tgravity-work-project-folder-organizer; do
  python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill"
done

python3 skills/tgravity-work-asset-export/scripts/validate_asset_cards.py --source skills/tgravity-work-asset-cards/assets/templates
python3 skills/tgravity-work-search/scripts/dual_search.py --status
python3 skills/tgravity-work-video-indexer/scripts/video_pipeline.py check --json
python3 skills/tgravity-work-invoice-reimbursement/scripts/invoice_reimbursement.py check
```
