# 环境与依赖

## 必需

- `python3`
- `ffmpeg`
- `ffprobe`

## 可选

- Python `whisper` 包，用于本地转写 `input/source.mp4`
- Google Chrome 或 Chromium
- Node.js 22+
- `npx hyperframes`

生产 `output/background.mp4` 需要本机 Chrome/Chromium 和 FFmpeg。脚本会用 Chrome DevTools Protocol 逐帧截图，再用 FFmpeg 编码为 MP4。

本地转写需要 FFmpeg 和 Python `whisper` 包。没有本地转写能力时，用户必须提供 `input/script.md`、`input/script.srt`、`input/script.vtt` 或其他带时间戳逐字稿。

只有用户要求人工验证真实 HyperFrames CLI 兼容性时，才需要 Node.js 和 HyperFrames。前置的项目初始化、脚本分段、timeline、总览站、本 Skill 生成的 `hyperframes/index.html` 和默认 MP4 渲染链路不依赖 HyperFrames CLI。

默认不调用 `npx hyperframes render`。

生产命令：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style cyber-blueprint
```

缺少脚本但允许本地转写时：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style cyber-blueprint --transcribe-if-missing --model medium --language zh
```

生产模式默认要求 `input/source.mp4`。如果用户显式接受无源视频草案，才允许加 `--allow-missing-source-video`；此时不能声称与人像视频同步。

## 检查命令

```bash
python3 scripts/tech_canvas_pipeline.py check --json
```

检查结果只说明本机能力，不自动安装依赖。

字段含义：

```text
node_available：本机是否有 node。
npx_available：本机是否有 npx。
hyperframes_global_cli_available：本机 PATH 中是否存在 hyperframes 命令。
hyperframes_via_npx_checked：是否实际联网检查 npx hyperframes，本脚本默认不联网，所以为 false。
python_whisper_available：Python 环境是否可 import whisper。
local_transcribe：是否具备本地视频转写能力。
chrome_available：本机是否有 Chrome 或 Chromium。
local_render：是否具备本地 HTML -> MP4 渲染能力。
```

`produce` 需要 `local_render: true`。如果缺脚本且要本地转写，还需要 `local_transcribe: true`。

## 本机边界

默认只在项目目录内读写：

```text
input/
analysis/
overview/
hyperframes/
output/
```

不得把用户素材、脚本、关键帧、预览文件或 MP4 写入 Skill 仓库。
