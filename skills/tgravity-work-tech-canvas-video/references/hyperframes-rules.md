# 本地 HTML 科技画布规则

## 进入条件

只有同时满足以下条件，才生成 `hyperframes/index.html`：

- `analysis/script_segments.json` 存在。
- `analysis/timeline.json` 存在。
- 用户已选择一个风格，并已映射为 canonical `style_id`。
- 用户允许生成本地 HTML 科技画布，或正在执行 `produce` 生产命令。

## 输出

```text
hyperframes/index.html
```

第一版必须是单文件 HTML，所有 CSS 和时间轴 JS 内联，不引用 CDN 或任何外部网络资源。它是 MP4 渲染源，不是最终交付物本身。生成命令：

```bash
python3 scripts/tech_canvas_pipeline.py hyperframes --workspace "<项目根目录>" --style "<style_id>"
```

`--style` 支持序号、中文名、英文展示名和 canonical `style_id`。模型仍应先做映射：

| 用户输入 | style_id |
|---|---|
| `1` / `第一个` / `第1个` / `赛博蓝图` / `Cyber Blueprint` | `cyber-blueprint` |
| `2` / `第二个` / `第2个` / `黑金发布会` / `Dark Launch` | `dark-launch` |
| `3` / `第三个` / `第3个` / `玻璃仪表盘` / `Glass Dashboard` | `glass-dashboard` |
| `4` / `第四个` / `第4个` / `数据雷达` / `Data Radar` | `data-radar` |
| `5` / `第五个` / `第5个` / `极简科技` / `Minimal Tech` | `minimal-tech` |
| `6` / `第六个` / `第6个` / `产品路线图` / `Product Roadmap` | `product-roadmap` |

## 结构要求

- 根元素使用 `<div id="stage">`。
- 必须带 `data-composition-id`、`data-start`、`data-width`、`data-height`、`data-duration`。
- 每个场景使用 `.scene.clip`。
- 每个场景都有 `data-start`、`data-duration`、`data-track-index`。
- 必须包含 `.motion-rail`、`.data-column`、`.keyword-chip` 和 HUD 元素，避免生成只有单张文字卡的弱包装画面。
- 必须暴露 `window.__tgravitySetTime(seconds)`，由 Chrome + FFmpeg 渲染器逐帧驱动。
- 注册到 `window.__timelines["<composition-id>"]`。
- 必须包含 `.portrait-safe-zone`，默认给右下角人像视频留出安全区。

## 稳定策略

- 优先套模板，不临场发明复杂结构。
- 每个 scene 的主动画控制在 2-4 个元素，背景网格、进度轨和 HUD 可以按 `window.__tgravitySetTime(seconds)` 做全局时间驱动。
- 字幕和标题必须适合 9:16 手机观看。
- 主信息区默认避开右下人像安全区；人像区只保留低对比纹理，不放关键文字。
- 先生成 `hyperframes/index.html`，人工复核后再渲染 `output/background.mp4`。
- 未实际运行 `npx hyperframes lint` 前，不称为“已验证 HyperFrames 工程”。

## 生产边界

默认渲染命令不调用 `npx hyperframes render`。本 Skill 用本机 Chrome + FFmpeg 渲染背景 MP4：

```bash
python3 scripts/tech_canvas_pipeline.py render --workspace "<项目根目录>"
```

输出：

```text
output/background.mp4
output/render_report.json
```

这不是最终人像合成成片。生产交付必须继续执行：

```bash
python3 scripts/tech_canvas_pipeline.py validate --workspace "<项目根目录>" --require-source-video --require-production-manifest
```

或者直接执行：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style "<style_id>"
```

如果用户明确要求验证真实 HyperFrames CLI 兼容性，人工可在 `hyperframes/` 目录里自行尝试：

```bash
npx hyperframes lint
npx hyperframes preview
```

只有 `lint` 实际通过后，才能说“已通过 HyperFrames CLI lint”。如果本机没有 Node.js 22+、FFmpeg 或 HyperFrames，如实说明缺失项。
