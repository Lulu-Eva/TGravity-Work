# 完整成片需求边界

## 本 Skill 的生产范围

本 Skill 只负责科技画布背景动画 MP4：

```text
input/source.mp4
+ input/script.md / input/script.srt / input/script.vtt / 本地转写音轨
-> analysis/script_segments.json
-> analysis/timeline.json
-> overview/index.html
-> hyperframes/index.html
-> output/background.mp4
-> output/validation_report.json
-> output/production_manifest.json
```

`output/background.mp4` 是给剪映叠人像使用的背景动画层，不是含人像、字幕、音乐和发布包装的最终成片。

## 用户要求完整成片时

如果用户要求以下能力，不要承诺本 Skill 已支持：

- 从主题自动调研到成片。
- 自动写完整拍摄脚本。
- 自动生成 B-roll 素材。
- 自动生成配音、音乐或音效。
- 自动生成最终字幕。
- 自动把人像视频和背景合成最终成片。
- 自动发布到小红书、抖音、视频号或其他平台。

先把需求收敛为背景动画层：

```text
当前 Skill 只交付科技画布背景动画 MP4：input/source.mp4 + 脚本或逐字稿 -> timeline -> 本地 HTML 画布 -> output/background.mp4 -> validation_report。最终人像合成、字幕、音乐和发布需要另起完整成片流程。
```

## 可接受的输入

生产模式优先要求：

```text
input/source.mp4
input/script.md / input/script.srt / input/script.vtt
```

缺少脚本时，只有用户明确允许本地转写，才运行：

```bash
python3 scripts/tech_canvas_pipeline.py produce --workspace "<项目根目录>" --style "<style_id>" --transcribe-if-missing --model medium --language zh
```

缺少 `input/source.mp4` 时，只能做草案或要求补视频，不能声称已与人像视频同步。

## 交付闸门

只有同时满足以下条件，才可以说背景动画 MP4 已完成机器验收：

- `output/background.mp4` 存在。
- `output/background.mp4` 能被 `ffprobe` 读取。
- `output/background.mp4` 时长与 `input/source.mp4` 误差不超过 0.25 秒。
- `output/validation_report.json` 的 `passed` 为 `true`。
- `output/production_manifest.json` 存在。
- `output/validation_frames/` 至少有 3 张非空抽帧。

## 必须提示人工复核

- 转写错字、漏字或错分段。
- 画布节奏是否贴合口播气口。
- 人像叠加后是否遮挡关键文字。
- 科技风格是否适合品牌调性。
- 背景动画是否抢主体。
- 视频、逐字稿、截图中是否有隐私、肖像或版权风险。
