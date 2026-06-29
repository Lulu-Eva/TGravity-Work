# 工作流

## 0. 先判定视频生产类型

如果用户提到一键成片、从调研到成片、AI 全流程视频生产、自动调研脚本素材配音字幕合成，先读取：

```text
references/full-video-boundary.md
```

然后明确：本 Skill 只生产可叠人像的科技画布背景动画 MP4，不做人像合成、TTS、音乐、B-roll 素材生成或发布。

如果用户提到 Codex + HyperFrames、科技画布、口播视频包装、知识分享视频包装、脚本拆镜头、字幕重点、节奏安排、HTML 动效、背景动画 MP4，继续执行本工作流。

## 1. 输入闸门

生产模式默认需要：

```text
input/source.mp4
input/script.md / input/script.srt / input/script.vtt
```

`input/source.mp4` 必须是已经剪好气口的人像视频，用于锁定背景动画总时长。脚本输入可以是 `input/script.md`、`input/script.srt`、`input/script.vtt` 或带时间戳逐字稿。

如果没有可用脚本输入，但 `input/source.mp4` 有可转录音轨，并且用户允许本地 Whisper，走本地转写：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style "<style_id>" --transcribe-if-missing --model medium --language zh
```

如果缺少 `input/source.mp4`，不要声称能交付与人像同步的 MP4。只能要求补视频，或在用户明确接受草案模式时使用 `--allow-missing-source-video`。

## 2. 一口气生产

用户要完整交付时，优先使用生产命令：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style "<style_id>"
```

该命令执行：

```text
init
-> 必要时 transcribe
-> plan
-> overview
-> hyperframes
-> render
-> validate --require-source-video
-> output/production_manifest.json
```

产物：

```text
analysis/script_segments.json
analysis/timeline.json
overview/index.html
hyperframes/index.html
output/background.mp4
output/render_report.json
output/validation_report.json
output/production_manifest.json
output/validation_frames/
```

只有 `output/validation_report.json` 的 `passed` 为 `true`，才可以说机器验收通过。

## 3. 分步复核

如果用户要先看风格、先看 HTML，或担心转写错误，按分步流程执行。

初始化：

```bash
python3 scripts/tech_canvas_pipeline.py init --workspace "<项目根目录>"
```

本地转写，只有缺脚本且用户允许时执行：

```bash
python3 scripts/tech_canvas_pipeline.py transcribe --workspace "<项目根目录>" --model medium --language zh
```

生成脚本分段和 timeline：

```bash
python3 scripts/tech_canvas_pipeline.py plan --workspace "<项目根目录>"
```

`plan` 会读取 `input/script.md`、`input/script.srt` 或 `input/script.vtt`，输出：

```text
analysis/script_segments.json
analysis/timeline.json
```

如果脚本含 SRT/VTT 或 `[00:12] 文案` 时间戳，按时间戳排布；否则按文本长度估算，再按 `input/source.mp4` 总时长缩放。

生成风格总览站：

```bash
python3 scripts/tech_canvas_pipeline.py overview --workspace "<项目根目录>"
```

输出：

```text
overview/index.html
```

生成本地 HTML 科技画布：

```bash
python3 scripts/tech_canvas_pipeline.py hyperframes --workspace "<项目根目录>" --style "<style_id>"
```

输出：

```text
hyperframes/index.html
```

渲染背景动画 MP4：

```bash
python3 scripts/tech_canvas_pipeline.py render --workspace "<项目根目录>"
```

输出：

```text
output/background.mp4
output/render_report.json
```

验收：

```bash
python3 scripts/tech_canvas_pipeline.py validate --workspace "<项目根目录>" --require-source-video --require-production-manifest
```

输出：

```text
output/validation_report.json
output/validation_frames/
```

## 4. 风格选择

用户没有指定风格时，生产模式默认 `cyber-blueprint`。如果用户要先比较风格，再生成 `overview/index.html`，让用户选一个 canonical `style_id`。

| 用户输入 | style_id |
|---|---|
| `1` / `第一个` / `第1个` / `赛博蓝图` / `Cyber Blueprint` | `cyber-blueprint` |
| `2` / `第二个` / `第2个` / `黑金发布会` / `Dark Launch` | `dark-launch` |
| `3` / `第三个` / `第3个` / `玻璃仪表盘` / `Glass Dashboard` | `glass-dashboard` |
| `4` / `第四个` / `第4个` / `数据雷达` / `Data Radar` | `data-radar` |
| `5` / `第五个` / `第5个` / `极简科技` / `Minimal Tech` | `minimal-tech` |
| `6` / `第六个` / `第6个` / `产品路线图` / `Product Roadmap` | `product-roadmap` |

## 5. 交付定义

可交付背景动画 MP4 必须同时满足：

- `output/background.mp4` 存在。
- `output/background.mp4` 能被 `ffprobe` 读取。
- `output/background.mp4` 分辨率符合参数，默认 1080x1920。
- `output/background.mp4` 时长与 `input/source.mp4` 误差不超过 0.25 秒。
- `output/validation_report.json` 的 `passed` 为 `true`。
- `output/validation_frames/` 至少包含 3 张非空抽帧。

人工仍需复核：转写错字、节奏、遮挡、品牌调性、人像叠加后的安全区。
