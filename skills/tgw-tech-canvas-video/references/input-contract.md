# 输入契约

## 生产输入

```text
input/source.mp4
input/script.md
input/script.srt
input/script.vtt
input/style.md
input/assets/
```

`input/source.mp4` 是生产模式的关键输入。它必须是用户已经剪好气口的人像视频，用来锁定 `output/background.mp4` 的总时长。没有它时，不能声称背景动画已经和人像视频同步。

脚本输入可以是 `input/script.md`、`input/script.srt` 或 `input/script.vtt`。`plan` 和 `produce` 会按这个优先级读取：`script.md`、`script.srt`、`script.vtt`。`script.md` 可以来自：

- 用户提前写好的视频脚本。
- “得到大脑”转写后人工清理出的文稿。
- SRT/VTT 字幕内容。
- 带时间戳的逐字稿。
- 本地 Whisper 从 `input/source.mp4` 生成的转写草稿。

## script.md 推荐格式

纯文本可以跑通，但精准同步优先使用 `input/script.srt`、`input/script.vtt` 或带时间戳逐字稿。

结构化脚本：

```md
# 视频脚本

## 01 开场
文案：很多人以为 Codex 只能写代码，其实它也能帮你剪视频。
画面建议：Codex 首页 / 项目界面 / 成片效果展示
时长：4 秒

## 02 展示效果
文案：这种科技蓝图风格的视频，核心是脚本、素材和动效模板。
画面建议：效果预览页 / 科技感动效
时长：6 秒
```

SRT：

```srt
1
00:00:00,000 --> 00:00:03,200
很多人以为 Codex 只能写代码。

2
00:00:03,200 --> 00:00:06,500
其实它也能帮你把视频包装成科技画布。
```

简易时间戳：

```md
[00:00] 很多人以为 Codex 只能写代码。
[00:03] 其实它也能帮你把视频包装成科技画布。
```

没有时间戳时，脚本会按文本长度估算每段时长，并按 `input/source.mp4` 总时长缩放。这能生成可用背景层，但不是逐字级精确字幕。

## 缺少脚本时

默认不要调用腾讯云 ASR。先检查：

```bash
python3 scripts/tech_canvas_pipeline.py check --json
```

如果 `local_transcribe: true` 且 `input/source.mp4` 存在，用户允许后执行：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style "<style_id>" --transcribe-if-missing --model medium --language zh
```

也可以只转写：

```bash
python3 scripts/tech_canvas_pipeline.py transcribe --workspace "<项目根目录>" --model medium --language zh
```

输出：

```text
input/script.srt
input/script.md
analysis/transcript.json
```

本地转写后必须人工复核 `input/script.srt` 的错字、漏字和时间切分。`--model base` 只适合快速草稿。

如果本机不能转录，回复：

```text
这个流程需要脚本或逐字稿。当前版本优先读取 input/script.md、input/script.srt 或 input/script.vtt；如果没有逐字稿，需要先补 SRT/VTT、带时间戳逐字稿，或选择一个明确授权的转录方案，再进入背景动画生产。
```

可选转录方案：

- 用户自行提供 SRT/VTT 或带时间戳逐字稿：最稳。
- 本机 Whisper：当前脚本支持 Python `whisper` 包，适合隐私优先。
- 外部 ASR 服务：必须由用户明确授权，且不得把 API key 写入 Skill 仓库。

## 画面同步原则

- 人像视频决定总时长。
- 脚本文案决定信息画布的节奏和场景顺序。
- 时间戳优先于估算。
- 如果脚本和人像视频明显不一致，标注为需要人工复核，不要硬说已同步。
- 背景动画必须避开人像安全区，默认给右下角预留空间。
