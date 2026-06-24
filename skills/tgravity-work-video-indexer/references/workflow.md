# Video Indexer Workflow

## 先定义项目

不要把“视频分析”当成单一任务。启动时先要求用户明确一个主目标：

| 主目标 | 输出重点 |
|---|---|
| 活动归档 | 每个素材是什么、发生在什么时间、是否可用 |
| 短视频切片 | 候选话题、候选时间码、金句、画面可用性 |
| 课程/工作坊复盘 | 章节、关键观点、可二次传播片段 |
| 客户交付 | 表格完整性、素材路径、风险备注 |
| 内部素材管理 | 文件命名、缺失素材、重复素材、低置信标记 |

如果用户没有目标，默认先做“素材索引草稿”，不直接给剪辑结论。

## 目录确认

必须确认：

- 项目根目录。
- 视频目录。默认优先找 `视频原始素材/`。
- 逐字稿目录。默认优先找 `线下工作坊逐字稿/`、`transcripts/`、`逐字稿/`。
- 输出目录。默认 `视频素材工作区/`。

禁止默认扫描：

- 用户整台电脑。
- 云盘根目录。
- 包含大量隐私材料的上级目录。

除环境检查外，所有真实项目命令都必须显式带 `--workspace "<项目根目录>"`。用户没有提供项目根目录时，不执行 `init`、`run`、`frames`、`export` 或 `validate`，只追问项目根目录。

## 标准流程

1. 检查环境。
2. 初始化项目配置。
3. 扫描视频，生成 `video_inventory.csv`。
4. 解析逐字稿，生成 `transcript_utterances.csv` 和 `transcript_chapters.csv`。
5. 按绝对时间把逐字稿对齐到视频，生成 `aligned_transcript_segments.csv`。
6. 生成关键帧和 contact sheet。
7. 生成 `video_material_draft.csv`。
8. 人工或多模态复核画面，填写 `visual-review-notes.csv`。
9. 导出 `视频素材切片表.xlsx` 或 CSV。
10. 运行验收。

## 命令

检查：

```bash
python3 scripts/video_pipeline.py check --json
```

初始化：

```bash
python3 scripts/video_pipeline.py init --workspace "<项目根目录>"
```

只生成索引和草稿表：

```bash
python3 scripts/video_pipeline.py run --workspace "<项目根目录>" --skip-frames
```

生成 contact sheet：

```bash
python3 scripts/video_pipeline.py frames --workspace "<项目根目录>"
```

本机 ASR 默认不执行。只有用户明确允许本机 Whisper 转写时，才加：

```bash
python3 scripts/video_pipeline.py run --workspace "<项目根目录>" --with-transcribe
```

导出：

```bash
python3 scripts/video_pipeline.py export --workspace "<项目根目录>"
```

验收：

```bash
python3 scripts/video_pipeline.py validate --workspace "<项目根目录>"
```

## 草稿表的置信度

必须区分三类信息：

- 高置信：来自文件元数据、ffprobe、明确绝对时间对齐的逐字稿。
- 中置信：来自章节标题、说话人文本和关键词的候选判断。
- 低置信：来自低质量 ASR、模糊画面、无逐字稿素材的推断。

低置信内容只能写成候选，不得写成事实。

## 人工复核规则

contact sheet 生成后，优先让人复核这些字段：

- `素材类型`
- `可用性`
- `主要话题`
- `具体内容`
- `建议切片时间码`
- `金句/亮点`
- `画面备注`
- `剪辑建议`

人工复核写入 `visual-review-notes.csv`。重新导出时，人工字段覆盖脚本草稿字段。

## 输出口径

跑完以后不要只说“完成”。必须报告：

- 扫描到多少个视频。
- 成功读取多少个视频元数据。
- 对齐到多少条逐字稿。
- 生成多少张 contact sheet。
- 还有哪些视频没有逐字稿或需要人工复核。
- Excel/CSV 输出路径。
