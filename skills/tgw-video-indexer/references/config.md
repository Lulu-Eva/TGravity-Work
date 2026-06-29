# Video Indexer Config

## 本机依赖

基础能力：

- Python 3。
- `ffprobe`：读取视频元数据。
- `ffmpeg`：生成关键帧和 contact sheet。

可选能力：

- `pandas` + `openpyxl`：导出多 sheet Excel。
- `Pillow`：把关键帧合成 contact sheet。
- `openai-whisper` 或本机其他 Whisper 命令：低置信 ASR 补充。

检查命令：

```bash
python3 scripts/video_pipeline.py check --json
```

如果缺少 `ffmpeg` / `ffprobe`，视频元数据和关键帧流程会受限。不要把依赖缺失误判为“视频无法分析”。

## 配置文件位置

项目配置保存在运行项目里：

```text
视频素材工作区/tgw-video-project.json
```

本 Skill 不需要 API Key。默认不使用云端转写服务。

如果以后接入云端视觉模型或云端 ASR，必须另设本机私密配置，不得写进 GitHub 仓库。

## 默认目录

| 项 | 默认值 |
|---|---|
| 项目根目录 | 用户明确给出的目录 |
| 视频目录 | `视频原始素材/` |
| 逐字稿目录 | `线下工作坊逐字稿/`，找不到再尝试 `逐字稿/`、`transcripts/` |
| 输出目录 | `视频素材工作区/` |
| 缩略图目录 | `视频素材工作区/thumbs_raw/` |
| contact sheet | `视频素材工作区/contact_sheets/` |

## 初始化

```bash
python3 scripts/video_pipeline.py init --workspace "<项目根目录>"
```

`--workspace` 是真实项目命令的硬要求。不要在不知道项目根目录时用当前目录代替。

可指定目录：

```bash
python3 scripts/video_pipeline.py init \
  --workspace "<项目根目录>" \
  --video-dir "<视频目录>" \
  --transcript-dir "<逐字稿目录>" \
  --out-dir "<输出目录>"
```

路径可以是相对项目根目录，也可以是绝对路径。输出目录必须在用户明确授权的项目范围内。

## 新电脑配置

新电脑第一次用时，按顺序做：

1. 安装 TGW Skills。
2. 检查 `ffmpeg`：

```bash
ffmpeg -version
ffprobe -version
```

3. 如果没有 `ffmpeg`，在 macOS 上通常用 Homebrew 安装：

```bash
brew install ffmpeg
```

4. 如需 Excel：

```bash
python3 -m pip install --user pandas openpyxl
```

5. 如需 contact sheet：

```bash
python3 -m pip install --user pillow
```

6. 如需本机 Whisper：

```bash
python3 -m pip install --user openai-whisper
```

不要在没有用户同意时自动安装依赖。

## 隐私边界

默认本机处理：

- 视频扫描。
- 元数据提取。
- 逐字稿解析。
- contact sheet。
- Excel/CSV 导出。

需要明确确认后才能做：

- 上传视频到第三方云端。
- 使用云端 ASR。
- 使用云端视觉理解。
- 处理含身份证、合同、私聊、客户隐私、儿童影像的素材。
