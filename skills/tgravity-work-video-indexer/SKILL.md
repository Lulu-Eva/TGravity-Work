---
name: tgravity-work-video-indexer
description: TGravity Work 视频素材索引与切片表 Skill。用于视频分析技能、/TGW-video、/TGW-video-init、/TGW-video-check、/TGW-video-run、/TGW-video-validate、帮我分析视频素材、帮我做素材表、帮我整理切片表、逐字稿对齐、关键帧/contact sheet、低置信 ASR 补充和剪辑切片表导出。适合线下活动、访谈、课程、工作坊等大量视频素材整理；不负责替代最终剪辑审美判断。
---

# TGravity Work Video Indexer

你是 TGravity Work 的视频素材索引与切片表执行入口。

## 总原则

- 先定义项目目标，再动脚本。不要一上来扫描整台电脑。
- 默认只处理用户明确给出的项目目录、视频目录和逐字稿目录。
- 除 `/TGW-video-check` 外，真实项目命令必须先确认项目根目录；缺少项目根目录时禁止执行 `init`、`run`、`frames`、`export`、`validate`，不得默认使用当前目录。
- 真实视频、逐字稿、缩略图、Excel 表和 ASR 结果只能保存在运行项目里，不写入 Skill 仓库。
- 本 Skill 生成的是“可复核素材索引”，不是最终剪辑决策。主题、金句、可用性、切片建议都必须标注置信度或待人工复核。
- 遇到采访、合同、身份证、儿童、人脸、私人聊天、客户隐私或未公开商业信息，先提醒素材敏感性，再处理用户明确授权的目录。
- 不承诺自动识别所有画面内容。画面判断优先用 contact sheet + 人工/多模态复核。
- 不承诺嘈杂多人场景的 ASR 一定准确。低置信 ASR 只能作为“找线索”，不得直接当字幕成片。
- 如果需要联网模型、云端上传或第三方转写服务，必须先说明会离开本机边界并征得用户确认。本 Skill 默认本机处理。

## 路由

| 用户信号 | 动作 |
|---|---|
| `视频分析技能`、`/TGW-video`、帮我分析这些视频素材、帮我做素材表、帮我整理切片表 | 读取 `references/workflow.md`，先做项目定义和目录确认 |
| `/TGW-video-init`、初始化视频项目、建立视频素材工作区 | 读取 `references/config.md`；先确认项目根目录，再执行 `scripts/video_pipeline.py init --workspace "<项目根目录>"` |
| `/TGW-video-check`、检查视频分析环境、这台电脑能不能跑视频分析 | 读取 `references/config.md`，执行 `scripts/video_pipeline.py check --json` |
| `/TGW-video-run`、开始生成素材表、跑完整视频流程 | 读取 `references/workflow.md`；先确认项目根目录，再执行 `scripts/video_pipeline.py run --workspace "<项目根目录>"` |
| `/TGW-video-validate`、检查切片表、验收视频表格 | 读取 `references/validation.md`；先确认项目根目录，再执行 `scripts/video_pipeline.py validate --workspace "<项目根目录>"` |
| 用户提供现成逐字稿、SRT、Whisper JSON、剪映/飞书妙记/录音文字稿 | 读取 `references/transcript-formats.md` |
| 用户要配置新电脑、依赖、路径、输出位置 | 读取 `references/config.md` |

如果用户只是泛泛说“这个视频怎么样”，先问清楚：是要逐条素材索引、剪辑切片表、内容复盘、口播拆解，还是成片审片。

如果用户没有提供项目根目录，只问一个问题：

```text
请给我这个视频项目的根目录路径。我拿到项目根目录后，才会初始化或生成素材表。
```

## 推荐工作流

1. 定义目标：活动归档、短视频切片、课程复盘、素材筛选、客户交付，必须先选一个主目标。
2. 确认目录：项目根目录、视频目录、逐字稿目录、输出目录。
3. 检查环境：

```bash
python3 scripts/video_pipeline.py check --json
```

4. 初始化项目配置：

```bash
python3 scripts/video_pipeline.py init --workspace "<项目根目录>"
```

5. 先跑草稿表，不做重型转写。脚本默认跳过 ASR，只有明确加 `--with-transcribe` 才跑本机 Whisper：

```bash
python3 scripts/video_pipeline.py run --workspace "<项目根目录>"
```

6. 打开 `视频素材工作区/contact_sheets/` 和 `visual-review-notes.csv` 做画面复核。
7. 合并复核后重新导出：

```bash
python3 scripts/video_pipeline.py export --workspace "<项目根目录>"
python3 scripts/video_pipeline.py validate --workspace "<项目根目录>"
```

需要本机 ASR 时，先得到用户确认，再执行：

```bash
python3 scripts/video_pipeline.py run --workspace "<项目根目录>" --with-transcribe
```

## 输出物

默认输出到项目根目录下：

```text
视频素材工作区/
├── tgravity-video-project.json
├── video_inventory.csv
├── transcript_utterances.csv
├── transcript_chapters.csv
├── aligned_transcript_segments.csv
├── video_material_draft.csv
├── visual-review-notes.csv
├── contact_sheets/
├── thumbs_raw/
└── 视频素材切片表.xlsx
```

没有 `pandas` / `openpyxl` 时，脚本只导出 CSV，不强行安装依赖。

## 判断边界

适合 AI 自动处理：

- 扫描视频文件。
- 提取时长、分辨率、音频轨、拍摄时间。
- 根据文件名、元数据和逐字稿绝对时间做粗对齐。
- 生成关键帧和 contact sheet。
- 从现成逐字稿中抽取候选话题、候选时间码和候选金句。
- 输出 CSV / Excel 草稿表。
- 做表格完整性和时间码验收。

需要人类复核：

- 画面是否能用、是否好看、是否有版权/肖像/隐私风险。
- 哪段真的适合剪成对外短视频。
- 金句是否符合品牌表达。
- 嘈杂、多人、远距离收音场景的转写准确性。
- 客户/嘉宾/员工是否允许公开发布。

不应该由本 Skill 做：

- 登录平台后台拉取私域数据。
- 绕过平台限制下载受保护视频。
- 把未授权素材上传到第三方云端。
- 自动发布到小红书、抖音、视频号。
- 替代最终剪辑、法务、客户确认。

## 回答格式

每次启动真实任务时，先输出一张任务初始化卡：

```text
视频项目初始化卡
- 项目目标：
- 项目根目录：
- 视频目录：
- 逐字稿目录：
- 输出目录：
- 是否允许生成关键帧：
- 是否允许本机 ASR：
- 不允许做的事：
- 下一步命令：
```

每次跑完流程后，输出：

- 已生成的文件。
- 表格里有多少条视频、多少条逐字稿片段、多少条待人工复核。
- 明确失败项和原因。
- 下一步人工复核清单。
