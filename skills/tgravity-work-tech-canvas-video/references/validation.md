# 验收规则

## 必检文件

生产模式必须检查：

```text
input/source.mp4
input/script.md / input/script.srt / input/script.vtt
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

如果走本地转写路径，还要检查：

```text
input/script.srt
analysis/transcript.json
```

## 机器验收标准

- `input/source.mp4` 存在，且能被 `ffprobe` 读取。
- `input/script.md`、`input/script.srt` 或 `input/script.vtt` 至少有一个存在，且不是初始化占位文本。
- 如果使用 `input/script.srt` 或 `input/script.vtt`，必须含有 `-->` 时间码。
- 如果由本地转写生成，`input/script.srt` 必须含有 `-->` 时间码。
- 如果由本地转写生成，`analysis/transcript.json` 必须含有非空 `segments`。
- 本地 Whisper 转写结果必须人工复核；`base` 模型输出只能视为草稿。
- `analysis/script_segments.json` 有非空段落。
- `analysis/timeline.json` 中每个 clip 都能追溯到一个 `script_id`。
- `analysis/timeline.json` 的 `total_duration` 必须与 `input/source.mp4` 时长接近；误差超过 0.25 秒视为不同步，验收失败。
- `overview/index.html` 能本地打开，并包含 `科技画布风格总览`、`cyber-blueprint`、`dark-launch` 和 `当前推荐程度`。
- `hyperframes/index.html` 不包含云端 ASR key。
- `hyperframes/index.html` 带 `data-composition-id`、`data-width`、`data-height`、`data-duration`。
- `hyperframes/index.html` 带 `window.__timelines`、`window.__tgravitySetTime`、`.scene.clip`、`.motion-rail`、`.data-column`、`.keyword-chip` 和 `.portrait-safe-zone`。
- `output/background.mp4` 能被 `ffprobe` 读取。
- `output/background.mp4` 分辨率默认是 1080x1920，或等于用户明确传入的渲染尺寸。
- `output/background.mp4` 时长必须与 `input/source.mp4` 接近；误差超过 0.25 秒视为不同步，验收失败。
- `output/render_report.json` 记录输出路径、时长、分辨率、fps、源 HTML 和生成时间。
- `output/validation_report.json` 的 `passed` 必须为 `true`。
- `output/production_manifest.json` 必须存在，并指向背景 MP4、本地 HTML 文件、渲染报告和验收报告。
- `output/validation_frames/` 至少包含 3 张抽帧图。
- 抽帧必须通过非空画面检查：不能是黑屏、空白帧或几乎没有亮度变化的画面。
- 项目文件都在用户项目目录内。

## 验收命令

从本 Skill 根目录执行，并把 `WORKSPACE` 改成用户项目根目录：

```bash
export WORKSPACE="<项目根目录>"
test -f "$WORKSPACE/input/source.mp4"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$WORKSPACE/input/source.mp4"
rg "科技画布风格总览|cyber-blueprint|dark-launch|当前推荐程度" "$WORKSPACE/overview/index.html"
rg "data-composition-id|window.__timelines|window.__tgravitySetTime|scene clip|portrait-safe-zone|motion-rail|data-column|keyword-chip|canvasLoad" "$WORKSPACE/hyperframes/index.html"
test -f "$WORKSPACE/input/script.md" || test -f "$WORKSPACE/input/script.srt" || test -f "$WORKSPACE/input/script.vtt"
test ! -f "$WORKSPACE/input/script.srt" || rg "-->" "$WORKSPACE/input/script.srt"
test ! -f "$WORKSPACE/input/script.vtt" || rg "-->" "$WORKSPACE/input/script.vtt"
test ! -f "$WORKSPACE/analysis/transcript.json" || rg '"segments"' "$WORKSPACE/analysis/transcript.json"
test -f "$WORKSPACE/output/background.mp4"
test -f "$WORKSPACE/output/render_report.json"
test -f "$WORKSPACE/output/production_manifest.json"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$WORKSPACE/output/background.mp4"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,avg_frame_rate -of json "$WORKSPACE/output/background.mp4"
python3 scripts/tech_canvas_pipeline.py validate --workspace "$WORKSPACE" --require-source-video --require-production-manifest
test -f "$WORKSPACE/output/validation_report.json"
python3 - <<'PY'
import json
import os
from pathlib import Path
workspace = Path(os.environ["WORKSPACE"])
report = json.loads((workspace / "output" / "validation_report.json").read_text(encoding="utf-8"))
assert report["passed"] is True
items = {item["name"]: item["passed"] for item in report["items"]}
assert items.get("input/source.mp4 exists") is True
assert items.get("input/source.mp4 readable") is True
assert items.get("timeline duration matches source") is True
assert items.get("background duration matches source") is True
assert items.get("validation frames are nonblank") is True
PY
find "$WORKSPACE/output/validation_frames" -name 'sample_*.jpg' | wc -l
```

如果要声称“已通过 HyperFrames CLI lint”，必须另行实际执行：

```bash
cd hyperframes && npx hyperframes lint
```

没有实际执行前，只能称为本地 HTML 画布草案。

## 人工复核

以下内容必须提示用户复核：

- 转写是否有错别字、漏字或错分段。
- 画布节奏是否贴合口播气口。
- 人像视频叠到左下或右下后，是否遮挡关键文字。
- 科技风格是否适合品牌调性。
- 背景动画是否过抢，是否影响口播主体。
- 视频、逐字稿、截图中是否有隐私、肖像、版权风险。
