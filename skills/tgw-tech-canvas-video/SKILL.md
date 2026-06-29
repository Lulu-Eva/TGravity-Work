---
name: tgw-tech-canvas-video
description: TGW 科技画布视频生产 Skill。用于把已剪好气口的人像视频和逐字稿或可本地转录音轨，生成按时间同步变化的本地 HTML 科技信息画布，并渲染、验收可交付的背景动画 MP4，供后续在剪映中与人像视频合成。触发方式：科技画布、Codex剪视频、脚本驱动剪辑、HyperFrames背景动画、HTML动画、HTML/GSAP动画、背景动画MP4、可交付MP4、/TGW-tech-video-produce、/TGW-tech-video-render、/TGW-tech-video-validate。
---

# TGW Tech Canvas Video

你是 TGW 的科技画布背景动画 MP4 生产入口。

## 总原则

- 生产目标是：`input/source.mp4` + `input/script.md` / `input/script.srt` / `input/script.vtt`，或 `input/source.mp4` 中可本地转录的音轨 -> `analysis/timeline.json` -> `hyperframes/index.html` -> `output/background.mp4` -> `output/validation_report.json`。
- 默认生产的是“给剪映叠人像用的背景动画层”，不是含人像的最终成片。不要默认把人像合成进 MP4。
- 生产模式默认要求 `input/source.mp4`，用它锁定总时长。没有人像视频时，只能做草案或显式使用 `--allow-missing-source-video`，不能声称已完成与人像同步。
- 优先使用用户提供的 `input/script.md`、SRT/VTT 或带时间戳逐字稿。没有逐字稿时，只能在用户允许后用本地 Whisper 从 `input/source.mp4` 生成草稿；`base` 模型结果必须人工复核。
- 默认不调用腾讯云 ASR，不上传用户视频，不要求用户提供云端转写 key。
- 所有用户素材、中间件、HTML、MP4 和验收报告都必须写入用户项目目录，不写入 Skill 仓库。
- 只有实际运行 `produce` 或 `render + validate`，且 `output/validation_report.json` 的 `passed` 为 `true`，才可以说背景动画 MP4 已通过机器验收。
- 未实际运行 `npx hyperframes lint` 前，不称为“已验证 HyperFrames 工程”。本 Skill 默认用本机 Chrome + FFmpeg 渲染 MP4。
- 遇到一键完整成片、从调研到成片、自动生成脚本素材配音字幕合成等需求，先读 `references/full-video-boundary.md`，再把能力边界收敛到背景动画 MP4 生产。

## 路由

| 用户信号 | 动作 |
|---|---|
| 科技画布、Codex剪视频、脚本驱动剪辑、口播视频包装、背景动画 MP4、可交付 MP4 | 读取 `references/workflow.md`，确认项目根目录、`input/source.mp4` 和脚本/转写来源 |
| `/TGW-tech-video-produce`、一口气生成、生产背景 MP4、跑完整链路 | 读取 `references/workflow.md` 和 `references/validation.md`，执行 `scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style "<style_id>"` |
| 没有逐字稿、从视频生成逐字稿、本地转写 | 读取 `references/input-contract.md`，确认 `input/source.mp4` 存在，再执行 `transcribe` 或 `produce --transcribe-if-missing` |
| `/TGW-tech-video-check`、检查科技画布视频环境 | 读取 `references/config.md`，执行 `scripts/tech_canvas_pipeline.py check --json` |
| `/TGW-tech-video-init`、初始化科技画布视频项目 | 读取 `references/input-contract.md`，执行 `scripts/tech_canvas_pipeline.py init --workspace "<项目根目录>"` |
| `/TGW-tech-video-plan`、生成剪辑方案、生成 timeline | 读取 `references/workflow.md`，执行 `scripts/tech_canvas_pipeline.py plan --workspace "<项目根目录>"` |
| `/TGW-tech-video-overview`、生成风格总览站、生成 6 种风格 | 读取 `references/style-presets.md`，执行 `scripts/tech_canvas_pipeline.py overview --workspace "<项目根目录>"` |
| `/TGW-tech-video-hyperframes`、生成本地 HTML 科技画布 | 读取 `references/hyperframes-rules.md`，把用户选择映射为 `style_id`，执行 `scripts/tech_canvas_pipeline.py hyperframes --workspace "<项目根目录>" --style "<style_id>"` |
| `/TGW-tech-video-render`、渲染背景动画 MP4 | 读取 `references/validation.md`，确认 `hyperframes/index.html` 存在，再执行 `scripts/tech_canvas_pipeline.py render --workspace "<项目根目录>"` |
| `/TGW-tech-video-validate`、验收背景动画、检查输出物 | 读取 `references/validation.md`，执行 `scripts/tech_canvas_pipeline.py validate --workspace "<项目根目录>" --require-source-video --require-production-manifest` |
| 用户要求把人像视频和背景直接合成 | 说明当前默认交付 `output/background.mp4`，合成由用户在剪映完成；除非另起合成模块，不承诺最终成片 |

如果用户没有提供项目根目录，只问一个问题：

```text
请给我这个科技画布视频项目的根目录路径。生产模式需要 input/source.mp4，并需要 input/script.md、input/script.srt、input/script.vtt、带时间戳逐字稿，或允许我用本地 Whisper 从 source.mp4 转写。
```

## 推荐项目结构

```text
tech-canvas-project/
├── input/
│   ├── source.mp4
│   ├── script.srt
│   ├── script.vtt
│   ├── script.md
│   ├── style.md
│   └── assets/
├── analysis/
│   ├── frames/
│   ├── transcript.json
│   ├── script_segments.json
│   └── timeline.json
├── overview/
│   └── index.html
├── hyperframes/
│   └── index.html
└── output/
    ├── background.mp4
    ├── render_report.json
    ├── validation_report.json
    ├── production_manifest.json
    └── validation_frames/
```

## 默认工作流

1. 确认项目根目录、`input/source.mp4`、逐字稿来源、输出比例和风格方向。
2. 检查环境：

```bash
python3 scripts/tech_canvas_pipeline.py check --json
```

3. 如果用户要一口气生产，优先执行：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style "<style_id>"
```

没有可用脚本输入但允许本地转写时执行：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style "<style_id>" --transcribe-if-missing --model medium --language zh
```

4. 如果用户要求分步复核，按以下顺序执行：

```bash
python3 scripts/tech_canvas_pipeline.py init --workspace "<项目根目录>"
python3 scripts/tech_canvas_pipeline.py transcribe --workspace "<项目根目录>" --model medium --language zh
python3 scripts/tech_canvas_pipeline.py plan --workspace "<项目根目录>"
python3 scripts/tech_canvas_pipeline.py overview --workspace "<项目根目录>"
python3 scripts/tech_canvas_pipeline.py hyperframes --workspace "<项目根目录>" --style "<style_id>"
python3 scripts/tech_canvas_pipeline.py render --workspace "<项目根目录>"
python3 scripts/tech_canvas_pipeline.py validate --workspace "<项目根目录>" --require-source-video --require-production-manifest
```

跳过 `transcribe` 的条件：用户已经提供可用的 `input/script.md`、`input/script.srt`、`input/script.vtt` 或带时间戳逐字稿。

5. 交付前检查：

- `output/background.mp4` 存在并能被 `ffprobe` 读取。
- `output/background.mp4` 时长与 `input/source.mp4` 的误差不超过 0.25 秒。
- `output/validation_report.json` 的 `passed` 为 `true`。
- `output/validation_frames/` 至少有 3 张非空抽帧，供人工检查遮挡、节奏和视觉风格。

## 风格映射

用户没有指定风格时，生产模式默认使用 `cyber-blueprint`。用户可以用序号、中文名、英文展示名或英文 id 选风格。

| 用户输入 | style_id |
|---|---|
| `1` / `第一个` / `第1个` / `赛博蓝图` / `Cyber Blueprint` | `cyber-blueprint` |
| `2` / `第二个` / `第2个` / `黑金发布会` / `Dark Launch` | `dark-launch` |
| `3` / `第三个` / `第3个` / `玻璃仪表盘` / `Glass Dashboard` | `glass-dashboard` |
| `4` / `第四个` / `第4个` / `数据雷达` / `Data Radar` | `data-radar` |
| `5` / `第五个` / `第5个` / `极简科技` / `Minimal Tech` | `minimal-tech` |
| `6` / `第六个` / `第6个` / `产品路线图` / `Product Roadmap` | `product-roadmap` |

## 回答格式

启动真实任务时，先输出：

```text
科技画布视频生产项目卡
- 项目目标：
- 项目根目录：
- 人像视频：input/source.mp4 / 缺失
- 脚本来源：input/script.md / input/script.srt / input/script.vtt / 带时间戳逐字稿 / 需要本地转写
- 是否允许本地转写：
- 输出比例：
- 风格 style_id：
- 是否要求一口气 produce：
- 不允许做的事：
- 下一步命令：
```

跑完每一步后输出：

- 已生成的文件。
- 是否达到 `output/background.mp4`。
- `validation_report.json` 是否通过。
- 仍需人工复核的点。
- 下一步命令。

## 禁止

- 不把 ASR API key 写进提示词、README、脚本、项目文件或 GitHub 仓库。
- 不默认上传用户视频到第三方服务。
- 不在没有脚本或本地转写结果的情况下假装已经完成口播转写。
- 不在没有 `input/source.mp4` 的情况下声称背景 MP4 已与人像视频同步。
- 不把背景 MP4 说成最终成片；它是给剪映叠人像用的背景动画层。
- 没有实现调研、TTS、素材生成、音乐、字幕、人像合成前，不得承诺“一键完整成片”。
- 不自动发布到小红书、抖音、视频号。
