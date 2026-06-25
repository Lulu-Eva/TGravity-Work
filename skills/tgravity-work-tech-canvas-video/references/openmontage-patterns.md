# OpenMontage 参考模式

> 核验日期：2026-06-25。
> 来源：Perplexity + TGravity Work Search 双引擎搜索，并用 OpenMontage 官方 GitHub README、AGENT_GUIDE、PROJECT_CONTEXT、PROMPT_GALLERY 和 `pipeline_defs/` 目录交叉核验。

## 结论

OpenMontage 和本 Skill 不是同一类工具。

- OpenMontage：端到端、pipeline-driven、agentic video production system。目标是从想法/参考视频到调研、方案、脚本、分镜、素材、配音、字幕、音乐、合成、质检和最终 MP4。
- 本 Skill：科技画布背景动画 MP4 生产器。目标是从已剪好气口的 `input/source.mp4` 和 `input/script.md` / `input/script.srt` / `input/script.vtt` 或本地转写音轨，到 `analysis/script_segments.json`、`analysis/timeline.json`、`hyperframes/index.html`、`output/background.mp4`、`output/validation_report.json` 和 `output/production_manifest.json`。

不得把 OpenMontage 的能力迁移成承诺。只能借鉴它的架构思想。

## 两段短视频文案分别在说什么

### 1. OpenMontage 文案

核心意思：

- 让 AI coding assistant 充当视频制片系统的调度者。
- 不是只生成一个零散视频片段，而是按 pipeline 推进。
- 典型链路是：调研 -> 方案 -> 脚本 -> 分镜/scene plan -> assets -> edit -> compose -> review。
- 它有多条视频类型管线，例如 animated explainer、screen demo、clip factory、podcast repurpose、documentary montage、hybrid、localization dub 等。
- 它会根据工具可用性选择 TTS、图像/视频生成、素材检索、Remotion、HyperFrames、FFmpeg 等路径。

这段文案的营销夸张点：

- “一键跑通”依赖环境、API key、素材来源、模型权限、成本和人工审批。
- “完整成片”不是所有管线都同等稳定，部分官方文档标注 beta。
- 不能据此推断本 Skill 已经具备 TTS、音乐、word-level 字幕、人像合成或全流程成片能力。

### 2. Codex + HyperFrames 文案

核心意思：

- 把原始录音或文字稿交给 Codex，让 Codex 先拆镜头、匹配画面、安排字幕重点和节奏。
- HyperFrames 负责 HTML/CSS/GSAP 风格的科技动效画布，适合 kinetic typography、产品发布、开发者工具、网页转视频、科技包装。
- 创作者的工作重心从“手剪所有素材”转为“整理脚本、明确镜头意图、复核节奏和画面匹配”。

这段更接近本 Skill 当前能力。本 Skill 当前可生成 HTML/GSAP 科技画布，并用 Chrome + FFmpeg 渲染、验收背景动画 MP4；但它不是最终人像合成成片。

## OpenMontage 可借鉴的架构点

### 1. Pipeline-first

任何视频请求先分类成 pipeline，而不是直接生成内容。

本 Skill 的固定 pipeline：

```text
input/script.md / input/script.srt / input/script.vtt
-> analysis/script_segments.json
-> analysis/timeline.json
-> overview/index.html
-> 用户选 style_id
-> hyperframes/index.html
-> output/background.mp4
-> output/validation_report.json
-> output/production_manifest.json
```

如果用户要求 OpenMontage 式全流程，先说明本 Skill 只有这个背景动画 pipeline。

### 2. Stage director

每个阶段先读对应 reference，再执行脚本：

- 输入和缺脚本：`references/input-contract.md`
- 工作流：`references/workflow.md`
- 风格：`references/style-presets.md`
- HyperFrames 背景动画：`references/hyperframes-rules.md`
- 验收：`references/validation.md`

不得跳过 reference 直接凭模型经验写输出。

### 3. Capability-first

OpenMontage 会先检查工具能力，再承诺交付。

本 Skill 的能力检查：

```bash
python3 scripts/tech_canvas_pipeline.py check --json
```

检查结果只说明本机环境；只有 `local_render: true` 才代表具备本地 HTML -> MP4 渲染能力。

### 4. Human approval gate

OpenMontage 的关键阶段有 checkpoint 和人工批准。本 Skill 的硬闸门是：

```text
overview/index.html -> 用户选风格 -> hyperframes/index.html -> output/background.mp4
```

用户未选风格前，不生成 `hyperframes/index.html`。

### 5. Artifacts are canonical

本 Skill 不应该只在聊天里给建议。关键中间件必须落盘：

```text
analysis/script_segments.json
analysis/timeline.json
overview/index.html
hyperframes/index.html
output/background.mp4
output/render_report.json
output/validation_report.json
output/production_manifest.json
```

## 本 Skill 不能继承的 OpenMontage 能力

当前不得承诺：

- 自动联网调研并生成事实型脚本。
- 自动生成 TTS 配音。
- 自动生成或检索 B-roll 素材。
- 自动生成背景音乐。
- 自动生成 word-level 字幕。
- 自动把人像视频合成进最终 MP4。
- 自动运行 Remotion / HyperFrames render。
- 自动从参考视频分析 transcript、pacing、scenes、keyframes。

如果用户要求这些，输出：

```text
这个需求属于 OpenMontage 式端到端视频生产。本 Skill 只负责科技画布背景动画层：input/source.mp4 + input/script.md / input/script.srt / input/script.vtt 或本地转写音轨 -> timeline -> overview -> hyperframes/index.html -> output/background.mp4 -> validation_report。要做完整人像合成成片，需要另起全流程视频生产管线，补齐调研、素材、TTS、音乐、字幕、人像合成和质检模块。
```

## 对本 Skill 的改进方向

可以后续新增，但必须作为新版本：

1. `proposal` 阶段：基于脚本生成 2-3 个视频概念和成本/能力说明。
2. `scene_plan` 阶段：把 `timeline.json` 升级成更严格的 scene artifact。
3. `asset_manifest` 阶段：接入 `tgravity-work-video-indexer` 的素材索引和人工素材选择。
4. `composite` 阶段：把用户人像视频叠到背景 MP4 的安全区并输出完整成片。
5. `review` 阶段：加入截图采样、HTML 结构检查、字幕遮挡检查、品牌调性检查。

这些不是当前能力。
