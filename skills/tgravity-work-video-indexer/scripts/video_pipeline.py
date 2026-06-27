#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_VIDEO_DIR = "视频原始素材"
DEFAULT_TRANSCRIPT_DIRS = ["线下工作坊逐字稿", "逐字稿", "transcripts"]
DEFAULT_OUT_DIR = "视频素材工作区"
CONFIG_NAME = "tgravity-video-project.json"
VIDEO_EXTENSIONS = [".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm"]

INVENTORY_COLUMNS = [
    "material_id",
    "filename",
    "path",
    "relative_path",
    "clip_no",
    "shoot_start",
    "shoot_end",
    "duration_sec",
    "duration_tc",
    "width",
    "height",
    "resolution",
    "video_codec",
    "audio_codec",
    "fps",
    "size_bytes",
    "time_source",
    "metadata_status",
]

UTTERANCE_COLUMNS = [
    "source_file",
    "recording_title",
    "recording_start",
    "relative_start",
    "relative_end",
    "absolute_start",
    "absolute_end",
    "speaker",
    "text",
    "format",
    "confidence",
]

CHAPTER_COLUMNS = [
    "source_file",
    "recording_title",
    "chapter_start",
    "chapter_end",
    "absolute_start",
    "absolute_end",
    "title",
    "summary",
    "format",
]

ALIGNED_COLUMNS = ["文件名", "素材编号", "素材内时间码", "绝对时间", "来源逐字稿", "说话人", "原文"]

MATERIAL_COLUMNS = [
    "素材编号",
    "文件名",
    "路径",
    "拍摄开始",
    "拍摄结束",
    "时长",
    "分辨率",
    "素材类型",
    "可用性",
    "音频来源/置信度",
    "主要话题",
    "具体内容",
    "建议切片时间码",
    "金句/亮点",
    "画面备注",
    "声音/转写备注",
    "剪辑建议",
]

WHISPER_COLUMNS = [
    "素材编号",
    "文件名",
    "素材内开始",
    "素材内结束",
    "绝对开始",
    "绝对结束",
    "来源",
    "文本",
    "avg_logprob",
    "no_speech_prob",
]

REVIEW_COLUMNS = [
    "素材编号",
    "素材类型",
    "可用性",
    "主要话题",
    "具体内容",
    "建议切片时间码",
    "金句/亮点",
    "画面备注",
    "剪辑建议",
    "置信度",
    "备注",
]

REVIEW_OVERRIDE_FIELDS = [
    "素材类型",
    "可用性",
    "主要话题",
    "具体内容",
    "建议切片时间码",
    "金句/亮点",
    "画面备注",
    "剪辑建议",
]

REQUIRED_MATERIAL_FIELDS = [
    "素材编号",
    "文件名",
    "路径",
    "时长",
    "素材类型",
    "可用性",
    "音频来源/置信度",
    "主要话题",
    "具体内容",
    "建议切片时间码",
    "画面备注",
    "剪辑建议",
]


def eprint(*parts: Any) -> None:
    print(*parts, file=sys.stderr)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def format_tc(seconds: Any) -> str:
    try:
        total = int(round(float(seconds)))
    except (TypeError, ValueError):
        total = 0
    total = max(total, 0)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_timecode(value: str) -> Optional[float]:
    if not value:
        return None
    text = value.strip().replace(",", ".")
    match = re.match(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?$", text)
    if not match:
        return None
    h = int(match.group(1) or 0)
    m = int(match.group(2))
    s = int(match.group(3))
    ms = match.group(4) or "0"
    return h * 3600 + m * 60 + s + int(ms.ljust(3, "0")[:3]) / 1000


def format_dt(value: Optional[dt.datetime]) -> str:
    if not value:
        return ""
    return value.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime_value(value: Any, timezone: str = "Asia/Shanghai") -> Optional[dt.datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = (
        text.replace("年", "-")
        .replace("月", "-")
        .replace("日", " ")
        .replace("：", ":")
        .strip()
    )
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for candidate in [text, text.replace("/", "-"), text.replace("T", " ")]:
        try:
            parsed = dt.datetime.fromisoformat(candidate)
            if parsed.tzinfo is not None:
                try:
                    from zoneinfo import ZoneInfo

                    parsed = parsed.astimezone(ZoneInfo(timezone))
                except Exception:
                    parsed = parsed.astimezone()
                return parsed.replace(tzinfo=None, microsecond=0)
            return parsed.replace(microsecond=0)
        except ValueError:
            pass
    patterns = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y%m%d%H%M%S",
        "%Y%m%d_%H%M%S",
    ]
    for pattern in patterns:
        try:
            return dt.datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def resolve_path(workspace: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return workspace / path


def path_to_string(path: Path) -> str:
    return str(path.expanduser().resolve())


def relative_to(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def default_config(workspace: Path) -> Dict[str, Any]:
    transcript_dir = DEFAULT_TRANSCRIPT_DIRS[0]
    for name in DEFAULT_TRANSCRIPT_DIRS:
        if (workspace / name).exists():
            transcript_dir = name
            break
    return {
        "workspace": str(workspace),
        "video_dir": DEFAULT_VIDEO_DIR,
        "transcript_dir": transcript_dir,
        "out_dir": DEFAULT_OUT_DIR,
        "output_excel": "视频素材切片表.xlsx",
        "timezone": "Asia/Shanghai",
        "video_extensions": VIDEO_EXTENSIONS,
        "frame_interval_seconds": 60,
        "contact_sheet_columns": 4,
        "contact_sheet_width": 320,
        "allow_cloud_upload": False,
        "allow_local_asr": False,
    }


def load_project(args: argparse.Namespace) -> Dict[str, Any]:
    workspace_value = getattr(args, "workspace", None)
    if not workspace_value:
        raise SystemExit("missing --workspace: video project commands must explicitly name the project root directory")
    workspace = Path(workspace_value).expanduser().resolve()
    out_dir_arg = getattr(args, "out_dir", None) or DEFAULT_OUT_DIR
    config_path_arg = getattr(args, "config", None)
    config_path = Path(config_path_arg).expanduser() if config_path_arg else resolve_path(workspace, out_dir_arg) / CONFIG_NAME

    config = default_config(workspace)
    config.update(read_json(config_path))
    config["workspace"] = str(workspace)

    for key in ["video_dir", "transcript_dir", "out_dir", "output_excel", "timezone"]:
        value = getattr(args, key, None)
        if value:
            config[key] = value

    if getattr(args, "video_extensions", None):
        config["video_extensions"] = [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in args.video_extensions.split(",")]

    out_dir = resolve_path(workspace, config.get("out_dir", DEFAULT_OUT_DIR))
    config["_config_path"] = str(config_path)
    config["_workspace_path"] = workspace
    config["_video_path"] = resolve_path(workspace, config.get("video_dir", DEFAULT_VIDEO_DIR))
    config["_transcript_path"] = resolve_path(workspace, config.get("transcript_dir", DEFAULT_TRANSCRIPT_DIRS[0]))
    config["_out_path"] = out_dir
    config["_thumbs_path"] = out_dir / "thumbs_raw"
    config["_sheets_path"] = out_dir / "contact_sheets"
    config["_excel_path"] = out_dir / config.get("output_excel", "视频素材切片表.xlsx")
    return config


def save_project_config(config: Dict[str, Any]) -> Path:
    out_dir: Path = config["_out_path"]
    data = {key: value for key, value in config.items() if not key.startswith("_")}
    data["workspace"] = str(config["_workspace_path"])
    path = out_dir / CONFIG_NAME
    write_json(path, data)
    return path


def read_text(path: Path) -> str:
    for encoding in ["utf-8", "utf-8-sig", "gb18030"]:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def run_capture(cmd: List[str], timeout: int = 120) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        timeout_message = f"timeout after {timeout}s: {' '.join(cmd)}"
        return 124, stdout, (stderr + "\n" + timeout_message).strip()
    return proc.returncode, proc.stdout, proc.stderr


def ffprobe_json(path: Path) -> Tuple[Optional[Dict[str, Any]], str]:
    if not command_exists("ffprobe"):
        return None, "ffprobe_missing"
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        code, out, err = run_capture(cmd)
    except Exception as exc:
        return None, f"ffprobe_error:{exc}"
    if code != 0:
        return None, (err or out or "ffprobe_failed").strip()
    try:
        return json.loads(out), ""
    except json.JSONDecodeError:
        return None, "ffprobe_invalid_json"


def parse_fraction(value: str) -> str:
    if not value or value == "0/0":
        return ""
    if "/" not in value:
        return value
    try:
        num, den = value.split("/", 1)
        den_f = float(den)
        if den_f == 0:
            return ""
        fps = float(num) / den_f
        return f"{fps:.2f}".rstrip("0").rstrip(".")
    except ValueError:
        return ""


def parse_filename_time(path: Path) -> Tuple[Optional[dt.datetime], str, str]:
    name = path.name
    dji = re.search(r"DJI[_-](\d{8})(\d{6})(?:[_-](\d+))?", name, re.I)
    if dji:
        parsed = parse_datetime_value(dji.group(1) + dji.group(2))
        return parsed, "dji_filename", dji.group(3) or ""
    compact = re.search(r"(?<!\d)((?:19|20)\d{6})[_-]?(\d{6})(?!\d)", name)
    if compact:
        parsed = parse_datetime_value(compact.group(1) + compact.group(2))
        return parsed, "filename_datetime", ""
    human = re.search(
        r"((?:19|20)\d{2})[-_.](\d{1,2})[-_.](\d{1,2})[ T_-](\d{1,2})[-_.:](\d{2})[-_.:](\d{2})",
        name,
    )
    if human:
        parsed = parse_datetime_value(
            f"{human.group(1)}-{int(human.group(2)):02d}-{int(human.group(3)):02d} "
            f"{int(human.group(4)):02d}:{human.group(5)}:{human.group(6)}"
        )
        return parsed, "filename_datetime", ""
    return None, "", ""


def video_metadata(path: Path, timezone: str) -> Dict[str, Any]:
    data, error = ffprobe_json(path)
    start, time_source, clip_no = parse_filename_time(path)
    row: Dict[str, Any] = {
        "duration_sec": "",
        "duration_tc": "",
        "width": "",
        "height": "",
        "resolution": "",
        "video_codec": "",
        "audio_codec": "",
        "fps": "",
        "size_bytes": path.stat().st_size if path.exists() else "",
        "shoot_start": "",
        "shoot_end": "",
        "clip_no": clip_no,
        "time_source": time_source,
        "metadata_status": "ok",
    }
    if data is None:
        row["metadata_status"] = error
        if not start:
            start = dt.datetime.fromtimestamp(path.stat().st_mtime)
            row["time_source"] = "file_mtime"
        row["shoot_start"] = format_dt(start)
        return row

    streams = data.get("streams", [])
    format_data = data.get("format", {})
    duration = format_data.get("duration")
    try:
        duration_f = float(duration)
    except (TypeError, ValueError):
        duration_f = 0.0
    row["duration_sec"] = f"{duration_f:.3f}" if duration_f else ""
    row["duration_tc"] = format_tc(duration_f)

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    width = video_stream.get("width") or ""
    height = video_stream.get("height") or ""
    row["width"] = width
    row["height"] = height
    row["resolution"] = f"{width}x{height}" if width and height else ""
    row["video_codec"] = video_stream.get("codec_name", "")
    row["audio_codec"] = audio_stream.get("codec_name", "")
    row["fps"] = parse_fraction(video_stream.get("r_frame_rate", ""))

    if not start:
        tags = {}
        tags.update(format_data.get("tags") or {})
        tags.update(video_stream.get("tags") or {})
        for key in ["creation_time", "com.apple.quicktime.creationdate"]:
            if key in tags:
                start = parse_datetime_value(tags[key], timezone=timezone)
                if start:
                    time_source = f"metadata:{key}"
                    break
    if not start:
        start = dt.datetime.fromtimestamp(path.stat().st_mtime)
        time_source = "file_mtime"

    end = start + dt.timedelta(seconds=duration_f) if start and duration_f else None
    row["shoot_start"] = format_dt(start)
    row["shoot_end"] = format_dt(end)
    row["time_source"] = time_source
    return row


def find_videos(video_dir: Path, extensions: List[str]) -> List[Path]:
    if not video_dir.exists():
        return []
    exts = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}
    return sorted(path for path in video_dir.rglob("*") if path.is_file() and path.suffix.lower() in exts)


def cmd_check(args: argparse.Namespace) -> int:
    result = {
        "python": sys.version.split()[0],
        "tools": {
            "ffmpeg": command_exists("ffmpeg"),
            "ffprobe": command_exists("ffprobe"),
        },
        "python_modules": {},
        "status": "ok",
        "notes": [],
    }
    for module in ["pandas", "openpyxl", "PIL", "whisper"]:
        try:
            __import__(module)
            result["python_modules"][module] = True
        except Exception:
            result["python_modules"][module] = False
    if not result["tools"]["ffprobe"]:
        result["status"] = "degraded"
        result["notes"].append("missing ffprobe: cannot reliably read video metadata")
    if not result["tools"]["ffmpeg"]:
        result["status"] = "degraded"
        result["notes"].append("missing ffmpeg: cannot extract frames or run common media operations")
    if not result["python_modules"]["pandas"] or not result["python_modules"]["openpyxl"]:
        result["notes"].append("missing pandas/openpyxl: Excel export will fall back to CSV")
    if not result["python_modules"]["PIL"]:
        result["notes"].append("missing Pillow: raw thumbnails can be extracted, contact sheets may be skipped")

    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result["tools"].items():
            print(f"{key}: {'ok' if value else 'missing'}")
        for key, value in result["python_modules"].items():
            print(f"{key}: {'ok' if value else 'missing'}")
        print(f"status: {result['status']}")
    return 0


def ensure_review_template(path: Path) -> None:
    if not path.exists():
        write_csv(path, [], REVIEW_COLUMNS)


def cmd_init(args: argparse.Namespace) -> int:
    config = load_project(args)
    out_dir: Path = config["_out_path"]
    out_dir.mkdir(parents=True, exist_ok=True)
    config["_thumbs_path"].mkdir(parents=True, exist_ok=True)
    config["_sheets_path"].mkdir(parents=True, exist_ok=True)
    ensure_review_template(out_dir / "visual-review-notes.csv")
    config_path = save_project_config(config)
    print(f"initialized: {config_path}")
    print(f"video_dir: {config['_video_path']}")
    print(f"transcript_dir: {config['_transcript_path']}")
    print(f"out_dir: {out_dir}")
    return 0


def generate_inventory(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    workspace: Path = config["_workspace_path"]
    video_dir: Path = config["_video_path"]
    timezone = config.get("timezone", "Asia/Shanghai")
    videos = find_videos(video_dir, config.get("video_extensions", VIDEO_EXTENSIONS))
    rows: List[Dict[str, Any]] = []
    for index, video in enumerate(videos, start=1):
        row = video_metadata(video, timezone=timezone)
        row.update(
            {
                "material_id": f"V{index:04d}",
                "filename": video.name,
                "path": path_to_string(video),
                "relative_path": relative_to(video, workspace),
            }
        )
        rows.append(row)
    return rows


def cmd_inventory(args: argparse.Namespace) -> int:
    config = load_project(args)
    config["_out_path"].mkdir(parents=True, exist_ok=True)
    rows = generate_inventory(config)
    out = config["_out_path"] / "video_inventory.csv"
    write_csv(out, rows, INVENTORY_COLUMNS)
    print(f"videos: {len(rows)}")
    print(f"inventory: {out}")
    if not rows:
        eprint(f"warning: no videos found in {config['_video_path']}")
    return 0


def parse_recording_time(text: str) -> Tuple[Optional[dt.datetime], Optional[dt.datetime]]:
    pattern = re.compile(
        r"(?:录音时间|记录时间|开始时间|会议时间)\s*[：:]\s*"
        r"([12]\d{3}[-/年]\d{1,2}[-/月]\d{1,2}(?:日)?\s+\d{1,2}[：:]\d{2}(?:[：:]\d{2})?)"
        r"(?:\s*(?:~|～|-|至|到)\s*"
        r"([12]\d{3}[-/年]\d{1,2}[-/月]\d{1,2}(?:日)?\s+\d{1,2}[：:]\d{2}(?:[：:]\d{2})?))?",
        re.M,
    )
    match = pattern.search(text)
    if not match:
        return None, None
    return parse_datetime_value(match.group(1)), parse_datetime_value(match.group(2))


def parse_markdown_transcript(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    text = read_text(path)
    recording_start, recording_end = parse_recording_time(text)
    title = path.stem
    title_match = re.search(r"^\s*#\s+(.+?)\s*$", text, re.M)
    if title_match:
        title = title_match.group(1).strip()

    chapter_matches: List[Tuple[float, str]] = []
    for match in re.finditer(r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]\([^)]+\)\s*\*\*(.+?)\*\*", text):
        seconds = parse_timecode(match.group(1))
        if seconds is not None:
            chapter_matches.append((seconds, match.group(2).strip()))
    for match in re.finditer(r"^\s*#{1,4}\s*\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+?)\s*$", text, re.M):
        seconds = parse_timecode(match.group(1))
        if seconds is not None:
            chapter_matches.append((seconds, match.group(2).strip()))
    chapter_matches = sorted(set(chapter_matches), key=lambda item: item[0])

    chapters: List[Dict[str, Any]] = []
    for idx, (start_sec, chapter_title) in enumerate(chapter_matches):
        end_sec = chapter_matches[idx + 1][0] if idx + 1 < len(chapter_matches) else None
        if end_sec is None and recording_start and recording_end:
            end_sec = max((recording_end - recording_start).total_seconds(), start_sec)
        abs_start = recording_start + dt.timedelta(seconds=start_sec) if recording_start else None
        abs_end = recording_start + dt.timedelta(seconds=end_sec) if recording_start and end_sec is not None else None
        chapters.append(
            {
                "source_file": path.name,
                "recording_title": title,
                "chapter_start": format_tc(start_sec),
                "chapter_end": format_tc(end_sec) if end_sec is not None else "",
                "absolute_start": format_dt(abs_start),
                "absolute_end": format_dt(abs_end),
                "title": chapter_title,
                "summary": "",
                "format": "markdown",
            }
        )

    utterances: List[Dict[str, Any]] = []
    utterance_pattern = re.compile(
        r"^\s*(?:[-*]\s*)?(?P<speaker>(?:说话人|Speaker|发言人|主持人|嘉宾)[^[]*?)\s*"
        r"\[(?P<tc>\d{1,2}:\d{2}(?::\d{2})?)\]\s*(?P<text>.+?)\s*$",
        re.M | re.I,
    )
    matches = list(utterance_pattern.finditer(text))
    for idx, match in enumerate(matches):
        start_sec = parse_timecode(match.group("tc"))
        if start_sec is None:
            continue
        next_start = None
        if idx + 1 < len(matches):
            next_start = parse_timecode(matches[idx + 1].group("tc"))
        abs_start = recording_start + dt.timedelta(seconds=start_sec) if recording_start else None
        abs_end = recording_start + dt.timedelta(seconds=next_start) if recording_start and next_start is not None else None
        utterances.append(
            {
                "source_file": path.name,
                "recording_title": title,
                "recording_start": format_dt(recording_start),
                "relative_start": format_tc(start_sec),
                "relative_end": format_tc(next_start) if next_start is not None else "",
                "absolute_start": format_dt(abs_start),
                "absolute_end": format_dt(abs_end),
                "speaker": match.group("speaker").strip(),
                "text": match.group("text").strip(),
                "format": "markdown",
                "confidence": "high" if recording_start else "medium",
            }
        )
    return utterances, chapters


def parse_srt_time(value: str) -> Optional[float]:
    start = value.split("-->", 1)[0].strip()
    return parse_timecode(start)


def parse_srt_transcript(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    text = read_text(path)
    recording_start, _, _ = parse_filename_time(path)
    rows: List[Dict[str, Any]] = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = [line.strip("\ufeff") for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        if "-->" in lines[0]:
            time_line = lines[0]
            content_lines = lines[1:]
        elif len(lines) >= 3 and "-->" in lines[1]:
            time_line = lines[1]
            content_lines = lines[2:]
        else:
            continue
        left, _, right = time_line.partition("-->")
        start_sec = parse_timecode(left.strip())
        end_sec = parse_timecode(right.strip())
        if start_sec is None:
            continue
        abs_start = recording_start + dt.timedelta(seconds=start_sec) if recording_start else None
        abs_end = recording_start + dt.timedelta(seconds=end_sec) if recording_start and end_sec is not None else None
        rows.append(
            {
                "source_file": path.name,
                "recording_title": path.stem,
                "recording_start": format_dt(recording_start),
                "relative_start": format_tc(start_sec),
                "relative_end": format_tc(end_sec) if end_sec is not None else "",
                "absolute_start": format_dt(abs_start),
                "absolute_end": format_dt(abs_end),
                "speaker": "",
                "text": " ".join(content_lines).strip(),
                "format": "srt",
                "confidence": "medium" if recording_start else "low",
            }
        )
    return rows, []


def parse_whisper_json(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    data = read_json(path)
    recording_start, _, _ = parse_filename_time(path)
    utterances: List[Dict[str, Any]] = []
    whisper_rows: List[Dict[str, Any]] = []
    for segment in data.get("segments", []):
        start_sec = segment.get("start")
        end_sec = segment.get("end")
        text = str(segment.get("text", "")).strip()
        if start_sec is None or not text:
            continue
        abs_start = recording_start + dt.timedelta(seconds=float(start_sec)) if recording_start else None
        abs_end = recording_start + dt.timedelta(seconds=float(end_sec)) if recording_start and end_sec is not None else None
        utterances.append(
            {
                "source_file": path.name,
                "recording_title": path.stem,
                "recording_start": format_dt(recording_start),
                "relative_start": format_tc(start_sec),
                "relative_end": format_tc(end_sec) if end_sec is not None else "",
                "absolute_start": format_dt(abs_start),
                "absolute_end": format_dt(abs_end),
                "speaker": "",
                "text": text,
                "format": "whisper_json",
                "confidence": "low",
            }
        )
        whisper_rows.append(
            {
                "素材编号": "",
                "文件名": path.name,
                "素材内开始": format_tc(start_sec),
                "素材内结束": format_tc(end_sec) if end_sec is not None else "",
                "绝对开始": format_dt(abs_start),
                "绝对结束": format_dt(abs_end),
                "来源": path.name,
                "文本": text,
                "avg_logprob": segment.get("avg_logprob", ""),
                "no_speech_prob": segment.get("no_speech_prob", ""),
            }
        )
    return utterances, [], whisper_rows


def parse_transcripts(transcript_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    utterances: List[Dict[str, Any]] = []
    chapters: List[Dict[str, Any]] = []
    whisper_rows: List[Dict[str, Any]] = []
    if not transcript_dir.exists():
        return utterances, chapters, whisper_rows
    files = sorted(path for path in transcript_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".markdown", ".srt", ".json"})
    for path in files:
        try:
            if path.suffix.lower() in {".md", ".markdown"}:
                u, c = parse_markdown_transcript(path)
                utterances.extend(u)
                chapters.extend(c)
            elif path.suffix.lower() == ".srt":
                u, c = parse_srt_transcript(path)
                utterances.extend(u)
                chapters.extend(c)
            elif path.suffix.lower() == ".json":
                u, c, w = parse_whisper_json(path)
                utterances.extend(u)
                chapters.extend(c)
                whisper_rows.extend(w)
        except Exception as exc:
            eprint(f"warning: failed to parse transcript {path}: {exc}")
    return utterances, chapters, whisper_rows


def cmd_transcripts(args: argparse.Namespace) -> int:
    config = load_project(args)
    out_dir: Path = config["_out_path"]
    out_dir.mkdir(parents=True, exist_ok=True)
    utterances, chapters, whisper_rows = parse_transcripts(config["_transcript_path"])
    write_csv(out_dir / "transcript_utterances.csv", utterances, UTTERANCE_COLUMNS)
    write_csv(out_dir / "transcript_chapters.csv", chapters, CHAPTER_COLUMNS)
    write_csv(out_dir / "whisper_segments.csv", whisper_rows, WHISPER_COLUMNS)
    print(f"utterances: {len(utterances)}")
    print(f"chapters: {len(chapters)}")
    print(f"whisper_segments: {len(whisper_rows)}")
    if not config["_transcript_path"].exists():
        eprint(f"warning: transcript dir not found: {config['_transcript_path']}")
    return 0


def seconds_between(start: dt.datetime, value: dt.datetime) -> float:
    return (value - start).total_seconds()


def choose_quote(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return "待人工复核"
    candidates = [row.get("原文", "").strip() for row in rows if len(row.get("原文", "").strip()) >= 18]
    if not candidates:
        candidates = [row.get("原文", "").strip() for row in rows if row.get("原文", "").strip()]
    if not candidates:
        return "待人工复核"
    keywords = ["关键", "真正", "所以", "不是", "而是", "必须", "重要", "问题", "机会", "增长"]
    scored = sorted(candidates, key=lambda text: (sum(1 for key in keywords if key in text), len(text)), reverse=True)
    return scored[0][:140]


def summarize_text(rows: List[Dict[str, str]], max_chars: int = 320) -> str:
    text = " ".join(row.get("原文", "").strip() for row in rows if row.get("原文", "").strip())
    if not text:
        return "未命中可按绝对时间对齐的逐字稿，待人工复核。"
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def chapter_topics_for_video(video_start: dt.datetime, video_end: dt.datetime, chapters: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for chapter in chapters:
        start = parse_datetime_value(chapter.get("absolute_start"))
        end = parse_datetime_value(chapter.get("absolute_end")) or start
        if not start:
            continue
        if end and end < video_start:
            continue
        if start > video_end:
            continue
        rel_start = max(0.0, seconds_between(video_start, start))
        rel_end = max(rel_start + 1.0, seconds_between(video_start, end or start))
        rel_end = min(rel_end, seconds_between(video_start, video_end))
        hits.append(
            {
                "title": chapter.get("title", "").strip(),
                "start": rel_start,
                "end": rel_end,
                "source": chapter.get("source_file", ""),
            }
        )
    return hits


def load_review_overrides(path: Path) -> Dict[str, Dict[str, str]]:
    rows = read_csv_rows(path)
    result: Dict[str, Dict[str, str]] = {}
    for row in rows:
        material_id = row.get("素材编号", "").strip()
        if material_id:
            result[material_id] = row
    return result


def generate_alignment(config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    out_dir: Path = config["_out_path"]
    inventory_path = out_dir / "video_inventory.csv"
    utter_path = out_dir / "transcript_utterances.csv"
    chapter_path = out_dir / "transcript_chapters.csv"

    inventory = read_csv_rows(inventory_path)
    utterances = read_csv_rows(utter_path)
    chapters = read_csv_rows(chapter_path)
    review = load_review_overrides(out_dir / "visual-review-notes.csv")

    aligned: List[Dict[str, Any]] = []
    material_rows: List[Dict[str, Any]] = []
    absolute_utterances = [(parse_datetime_value(row.get("absolute_start")), row) for row in utterances if parse_datetime_value(row.get("absolute_start"))]

    for video in inventory:
        material_id = video.get("material_id", "")
        video_start = parse_datetime_value(video.get("shoot_start"))
        video_end = parse_datetime_value(video.get("shoot_end"))
        duration = float(video.get("duration_sec") or 0)
        video_rows: List[Dict[str, str]] = []
        if video_start and video_end:
            for abs_start, utter in absolute_utterances:
                if not abs_start:
                    continue
                if video_start <= abs_start <= video_end:
                    rel = seconds_between(video_start, abs_start)
                    aligned_row = {
                        "文件名": video.get("filename", ""),
                        "素材编号": material_id,
                        "素材内时间码": format_tc(rel),
                        "绝对时间": format_dt(abs_start),
                        "来源逐字稿": utter.get("source_file", ""),
                        "说话人": utter.get("speaker", ""),
                        "原文": utter.get("text", ""),
                    }
                    aligned.append(aligned_row)
                    video_rows.append(aligned_row)

        chapter_hits = chapter_topics_for_video(video_start, video_end, chapters) if video_start and video_end else []
        topic_titles = []
        for hit in chapter_hits:
            title = hit.get("title", "")
            if title and title not in topic_titles:
                topic_titles.append(title)
        if topic_titles:
            topic = " / ".join(topic_titles[:3])
        elif video_rows:
            topic = "有逐字稿片段，主题待人工复核"
        else:
            topic = "待人工复核"

        if chapter_hits:
            ranges = [f"{format_tc(hit['start'])}-{format_tc(hit['end'])}" for hit in chapter_hits[:4]]
            slice_tc = "；".join(ranges)
        elif duration:
            slice_tc = f"00:00:00-{format_tc(min(duration, 30))} | 待人工复核"
        else:
            slice_tc = "待人工复核"

        audio_note = (
            f"现成逐字稿按绝对时间对齐 / 高置信；命中 {len(video_rows)} 条"
            if video_rows
            else "未对齐逐字稿 / 待 ASR 或人工复核"
        )
        material = {
            "素材编号": material_id,
            "文件名": video.get("filename", ""),
            "路径": video.get("path", ""),
            "拍摄开始": video.get("shoot_start", ""),
            "拍摄结束": video.get("shoot_end", ""),
            "时长": video.get("duration_tc", ""),
            "分辨率": video.get("resolution", ""),
            "素材类型": "待人工复核",
            "可用性": "待复核",
            "音频来源/置信度": audio_note,
            "主要话题": topic,
            "具体内容": summarize_text(video_rows),
            "建议切片时间码": slice_tc,
            "金句/亮点": choose_quote(video_rows),
            "画面备注": "待查看 contact sheet 或原片。",
            "声音/转写备注": audio_note,
            "剪辑建议": "按候选时间码初筛；画面、授权和表达风险需人工复核。" if video_rows else "先看关键帧；必要时补本机 ASR 或人工听写。",
        }
        overrides = review.get(material_id, {})
        for field in REVIEW_OVERRIDE_FIELDS:
            value = (overrides.get(field) or "").strip()
            if value:
                material[field] = value
        if overrides.get("备注", "").strip():
            material["声音/转写备注"] = f"{material['声音/转写备注']}；人工备注：{overrides['备注'].strip()}"
        material_rows.append(material)

    return aligned, material_rows


def cmd_align(args: argparse.Namespace) -> int:
    config = load_project(args)
    out_dir: Path = config["_out_path"]
    if not (out_dir / "video_inventory.csv").exists():
        generate = generate_inventory(config)
        write_csv(out_dir / "video_inventory.csv", generate, INVENTORY_COLUMNS)
    if not (out_dir / "transcript_utterances.csv").exists():
        utterances, chapters, whisper_rows = parse_transcripts(config["_transcript_path"])
        write_csv(out_dir / "transcript_utterances.csv", utterances, UTTERANCE_COLUMNS)
        write_csv(out_dir / "transcript_chapters.csv", chapters, CHAPTER_COLUMNS)
        write_csv(out_dir / "whisper_segments.csv", whisper_rows, WHISPER_COLUMNS)
    ensure_review_template(out_dir / "visual-review-notes.csv")
    aligned, material_rows = generate_alignment(config)
    write_csv(out_dir / "aligned_transcript_segments.csv", aligned, ALIGNED_COLUMNS)
    write_csv(out_dir / "video_material_draft.csv", material_rows, MATERIAL_COLUMNS)
    print(f"aligned_segments: {len(aligned)}")
    print(f"material_rows: {len(material_rows)}")
    print(f"draft: {out_dir / 'video_material_draft.csv'}")
    return 0


def extract_frame(video: Path, out_path: Path, second: float) -> bool:
    if not command_exists("ffmpeg"):
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{max(second, 0):.2f}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-q:v",
        "3",
        "-y",
        str(out_path),
    ]
    try:
        code, _, _ = run_capture(cmd, timeout=60)
    except Exception:
        return False
    return code == 0 and out_path.exists()


def make_contact_sheet(images: List[Path], out_path: Path, label_prefix: str, columns: int, width: int) -> bool:
    if not images:
        return False
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False
    thumbs = []
    label_h = 28
    for idx, image_path in enumerate(images, start=1):
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            continue
        ratio = width / image.width
        height = max(1, int(image.height * ratio))
        image = image.resize((width, height))
        canvas = Image.new("RGB", (width, height + label_h), "white")
        canvas.paste(image, (0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((8, height + 6), f"{label_prefix} #{idx}", fill=(0, 0, 0))
        thumbs.append(canvas)
    if not thumbs:
        return False
    columns = max(1, columns)
    rows = (len(thumbs) + columns - 1) // columns
    cell_w = width
    cell_h = max(img.height for img in thumbs)
    sheet = Image.new("RGB", (cell_w * columns, cell_h * rows), "white")
    for idx, thumb in enumerate(thumbs):
        x = (idx % columns) * cell_w
        y = (idx // columns) * cell_h
        sheet.paste(thumb, (x, y))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=88)
    return True


def cmd_frames(args: argparse.Namespace) -> int:
    config = load_project(args)
    inventory = read_csv_rows(config["_out_path"] / "video_inventory.csv")
    if not inventory:
        inventory = generate_inventory(config)
        write_csv(config["_out_path"] / "video_inventory.csv", inventory, INVENTORY_COLUMNS)
    interval = int(getattr(args, "frame_interval", None) or config.get("frame_interval_seconds", 60))
    max_frames = int(getattr(args, "max_frames", 12))
    columns = int(config.get("contact_sheet_columns", 4))
    width = int(config.get("contact_sheet_width", 320))

    index_rows: List[Dict[str, Any]] = []
    sheets = 0
    thumbs = 0
    if not command_exists("ffmpeg"):
        eprint("warning: ffmpeg missing; skip frame extraction")
        write_csv(config["_sheets_path"] / "index.csv", index_rows, ["素材编号", "文件名", "contact_sheet", "thumbs"])
        return 0

    for video in inventory:
        material_id = video.get("material_id", "")
        video_path = Path(video.get("path", ""))
        duration = float(video.get("duration_sec") or 0)
        if not video_path.exists():
            continue
        if duration <= 0:
            frame_times = [0]
        else:
            frame_times = [min(1.0, max(0.0, duration / 2))]
            current = interval
            while current < duration and len(frame_times) < max_frames:
                frame_times.append(float(current))
                current += interval
            if duration > 5 and len(frame_times) < max_frames:
                frame_times.append(max(duration - 2, 0))
        raw_paths = []
        for idx, second in enumerate(sorted(set(frame_times)), start=1):
            thumb_path = config["_thumbs_path"] / f"{material_id}_{idx:03d}_{format_tc(second).replace(':', '-')}.jpg"
            if extract_frame(video_path, thumb_path, second):
                raw_paths.append(thumb_path)
                thumbs += 1
        sheet_path = config["_sheets_path"] / f"{material_id}_contact.jpg"
        made_sheet = make_contact_sheet(raw_paths, sheet_path, material_id, columns=columns, width=width)
        if made_sheet:
            sheets += 1
        index_rows.append(
            {
                "素材编号": material_id,
                "文件名": video.get("filename", ""),
                "contact_sheet": str(sheet_path if made_sheet else ""),
                "thumbs": ";".join(str(p) for p in raw_paths),
            }
        )
    write_csv(config["_sheets_path"] / "index.csv", index_rows, ["素材编号", "文件名", "contact_sheet", "thumbs"])
    print(f"thumbs: {thumbs}")
    print(f"contact_sheets: {sheets}")
    print(f"contact_sheet_dir: {config['_sheets_path']}")
    return 0


def cmd_transcribe(args: argparse.Namespace) -> int:
    config = load_project(args)
    whisper_cmd = shutil.which("whisper")
    if not whisper_cmd:
        eprint("whisper command not found. Install openai-whisper or run with --skip-transcribe.")
        return 2
    inventory = read_csv_rows(config["_out_path"] / "video_inventory.csv")
    aligned = read_csv_rows(config["_out_path"] / "aligned_transcript_segments.csv")
    covered = {row.get("素材编号") for row in aligned if row.get("素材编号")}
    whisper_dir = config["_out_path"] / "whisper"
    whisper_dir.mkdir(parents=True, exist_ok=True)
    model = getattr(args, "model", "base")
    ran = 0
    for video in inventory:
        if getattr(args, "only_missing", True) and video.get("material_id") in covered:
            continue
        path = Path(video.get("path", ""))
        if not path.exists():
            continue
        cmd = [whisper_cmd, str(path), "--model", model, "--output_dir", str(whisper_dir), "--output_format", "json"]
        eprint("running:", " ".join(cmd[:2]), "...", "--model", model)
        code, _, err = run_capture(cmd, timeout=int(getattr(args, "timeout", 3600)))
        if code != 0:
            eprint(f"warning: whisper failed for {path.name}: {err.strip()}")
        else:
            ran += 1
    print(f"transcribed: {ran}")
    print(f"whisper_dir: {whisper_dir}")
    return 0


def chapters_for_excel(path: Path) -> List[Dict[str, Any]]:
    rows = read_csv_rows(path)
    result = []
    for row in rows:
        result.append(
            {
                "来源逐字稿": row.get("source_file", ""),
                "录音标题": row.get("recording_title", ""),
                "章节开始": row.get("chapter_start", ""),
                "章节结束": row.get("chapter_end", ""),
                "绝对开始": row.get("absolute_start", ""),
                "绝对结束": row.get("absolute_end", ""),
                "章节标题": row.get("title", ""),
                "章节摘要": row.get("summary", ""),
            }
        )
    return result


def cmd_export(args: argparse.Namespace) -> int:
    config = load_project(args)
    out_dir: Path = config["_out_path"]
    if not (out_dir / "video_material_draft.csv").exists():
        aligned, material_rows = generate_alignment(config)
        write_csv(out_dir / "aligned_transcript_segments.csv", aligned, ALIGNED_COLUMNS)
        write_csv(out_dir / "video_material_draft.csv", material_rows, MATERIAL_COLUMNS)

    material = read_csv_rows(out_dir / "video_material_draft.csv")
    aligned = read_csv_rows(out_dir / "aligned_transcript_segments.csv")
    whisper = read_csv_rows(out_dir / "whisper_segments.csv")
    chapters = chapters_for_excel(out_dir / "transcript_chapters.csv")
    notes = [
        {"项目": "生成时间", "值": format_dt(dt.datetime.now())},
        {"项目": "项目根目录", "值": str(config["_workspace_path"])},
        {"项目": "视频目录", "值": str(config["_video_path"])},
        {"项目": "逐字稿目录", "值": str(config["_transcript_path"])},
        {"项目": "说明", "值": "本表为可复核素材索引草稿，最终剪辑判断需人工确认。"},
    ]

    excel_path: Path = config["_excel_path"]
    try:
        import pandas as pd
    except Exception:
        eprint("warning: pandas/openpyxl missing; Excel export skipped. CSV files are available.")
        print(f"csv: {out_dir / 'video_material_draft.csv'}")
        return 0

    excel_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame(material, columns=MATERIAL_COLUMNS).to_excel(writer, index=False, sheet_name="素材总表")
        pd.DataFrame(aligned, columns=ALIGNED_COLUMNS).to_excel(writer, index=False, sheet_name="逐字稿片段")
        pd.DataFrame(whisper, columns=WHISPER_COLUMNS).to_excel(writer, index=False, sheet_name="Whisper补充片段")
        pd.DataFrame(chapters).to_excel(writer, index=False, sheet_name="逐字稿章节")
        pd.DataFrame(notes).to_excel(writer, index=False, sheet_name="说明")
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            for column_cells in sheet.columns:
                values = [str(cell.value or "") for cell in column_cells[:80]]
                width = min(max([len(v) for v in values] + [10]) + 2, 48)
                sheet.column_dimensions[column_cells[0].column_letter].width = width
    print(f"excel: {excel_path}")
    print(f"material_rows: {len(material)}")
    return 0


def parse_suggested_ranges(value: str) -> List[Tuple[float, float]]:
    ranges: List[Tuple[float, float]] = []
    for match in re.finditer(r"(\d{1,2}:\d{2}:\d{2})\s*(?:-|~|到)\s*(\d{1,2}:\d{2}:\d{2})", value or ""):
        start = parse_timecode(match.group(1))
        end = parse_timecode(match.group(2))
        if start is not None and end is not None:
            ranges.append((start, end))
    return ranges


def cmd_validate(args: argparse.Namespace) -> int:
    config = load_project(args)
    out_dir: Path = config["_out_path"]
    inventory = read_csv_rows(out_dir / "video_inventory.csv")
    material = read_csv_rows(out_dir / "video_material_draft.csv")
    aligned = read_csv_rows(out_dir / "aligned_transcript_segments.csv")
    errors: List[str] = []
    warnings: List[str] = []

    if not inventory:
        errors.append("missing or empty video_inventory.csv")
    if not material:
        errors.append("missing or empty video_material_draft.csv")

    inventory_ids = {row.get("material_id") for row in inventory if row.get("material_id")}
    material_ids = {row.get("素材编号") for row in material if row.get("素材编号")}
    missing = sorted(inventory_ids - material_ids)
    extra = sorted(material_ids - inventory_ids)
    if missing:
        errors.append(f"material table missing videos: {', '.join(missing[:10])}")
    if extra:
        warnings.append(f"material table has ids not in inventory: {', '.join(extra[:10])}")

    duration_by_id = {row.get("material_id"): float(row.get("duration_sec") or 0) for row in inventory}
    for row in material:
        mid = row.get("素材编号", "")
        for field in REQUIRED_MATERIAL_FIELDS:
            if not str(row.get(field, "")).strip():
                errors.append(f"{mid or row.get('文件名', '')}: required field empty: {field}")
        ranges = parse_suggested_ranges(row.get("建议切片时间码", ""))
        if not ranges and "待" not in row.get("建议切片时间码", ""):
            warnings.append(f"{mid}: no parseable suggested time range")
        duration = duration_by_id.get(mid, 0)
        for start, end in ranges:
            if end < start:
                errors.append(f"{mid}: suggested range ends before start: {format_tc(start)}-{format_tc(end)}")
            if duration and end > duration + 1:
                errors.append(f"{mid}: suggested range exceeds duration: {format_tc(start)}-{format_tc(end)} > {format_tc(duration)}")
        path = row.get("路径", "")
        if path and not Path(path).exists():
            warnings.append(f"{mid}: source path does not exist on this computer: {path}")

    result = {
        "视频总数": len(inventory),
        "表格记录数": len(material),
        "已对齐逐字稿片段": len(aligned),
        "需要人工复核": sum(1 for row in material if "待" in "".join(str(row.get(key, "")) for key in ["素材类型", "可用性", "主要话题", "画面备注"])),
        "error": errors,
        "warning": warnings,
        "输出文件": str(config["_excel_path"] if config["_excel_path"].exists() else out_dir / "video_material_draft.csv"),
    }
    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("视频素材表验收结果")
        for key in ["视频总数", "表格记录数", "已对齐逐字稿片段", "需要人工复核", "输出文件"]:
            print(f"- {key}: {result[key]}")
        print(f"- error: {len(errors)}")
        for item in errors[:20]:
            print(f"  - {item}")
        print(f"- warning: {len(warnings)}")
        for item in warnings[:20]:
            print(f"  - {item}")
    return 1 if errors else 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_project(args)
    cmd_init(args)
    rows = generate_inventory(config)
    write_csv(config["_out_path"] / "video_inventory.csv", rows, INVENTORY_COLUMNS)
    utterances, chapters, whisper_rows = parse_transcripts(config["_transcript_path"])
    write_csv(config["_out_path"] / "transcript_utterances.csv", utterances, UTTERANCE_COLUMNS)
    write_csv(config["_out_path"] / "transcript_chapters.csv", chapters, CHAPTER_COLUMNS)
    write_csv(config["_out_path"] / "whisper_segments.csv", whisper_rows, WHISPER_COLUMNS)
    aligned, material_rows = generate_alignment(config)
    write_csv(config["_out_path"] / "aligned_transcript_segments.csv", aligned, ALIGNED_COLUMNS)
    write_csv(config["_out_path"] / "video_material_draft.csv", material_rows, MATERIAL_COLUMNS)
    if not getattr(args, "skip_frames", False):
        cmd_frames(args)
    if getattr(args, "with_transcribe", False) and not getattr(args, "skip_transcribe", False):
        transcribe_result = cmd_transcribe(args)
        if transcribe_result != 0:
            eprint("warning: transcribe skipped or failed; draft table still generated")
    else:
        eprint("transcribe skipped by default; rerun with --with-transcribe if local ASR is explicitly allowed")
    cmd_export(args)
    print("run_summary:")
    print(f"- videos: {len(rows)}")
    print(f"- utterances: {len(utterances)}")
    print(f"- aligned_segments: {len(aligned)}")
    print(f"- material_rows: {len(material_rows)}")
    print(f"- out_dir: {config['_out_path']}")
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", required=True, help="项目根目录；真实项目命令必须显式提供，不能默认当前目录")
    parser.add_argument("--video-dir", help="视频目录，相对 workspace 或绝对路径")
    parser.add_argument("--transcript-dir", help="逐字稿目录，相对 workspace 或绝对路径")
    parser.add_argument("--out-dir", help="输出目录，相对 workspace 或绝对路径")
    parser.add_argument("--output-excel", help="导出的 Excel 文件名")
    parser.add_argument("--config", help="项目配置文件路径")
    parser.add_argument("--timezone", help="元数据时间转换时区，默认 Asia/Shanghai")
    parser.add_argument("--video-extensions", help="视频后缀逗号分隔，例如 .mp4,.mov")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TGravity Work video material indexer")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="检查本机依赖")
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=cmd_check)

    for name, help_text, func in [
        ("init", "初始化项目配置", cmd_init),
        ("inventory", "扫描视频并生成清单", cmd_inventory),
        ("transcripts", "解析逐字稿", cmd_transcripts),
        ("align", "对齐逐字稿并生成草稿表", cmd_align),
        ("export", "导出 Excel/CSV", cmd_export),
    ]:
        p = sub.add_parser(name, help=help_text)
        add_common(p)
        p.set_defaults(func=func)

    frames = sub.add_parser("frames", help="生成关键帧和 contact sheet")
    add_common(frames)
    frames.add_argument("--frame-interval", type=int, default=None)
    frames.add_argument("--max-frames", type=int, default=12)
    frames.set_defaults(func=cmd_frames)

    transcribe = sub.add_parser("transcribe", help="可选本机 Whisper 转写")
    add_common(transcribe)
    transcribe.add_argument("--model", default="base")
    transcribe.add_argument("--timeout", type=int, default=3600)
    transcribe.add_argument("--only-missing", action="store_true", default=True)
    transcribe.set_defaults(func=cmd_transcribe)

    validate = sub.add_parser("validate", help="验收输出表格")
    add_common(validate)
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=cmd_validate)

    run = sub.add_parser("run", help="执行标准草稿流程")
    add_common(run)
    run.add_argument("--skip-frames", action="store_true")
    run.add_argument("--skip-transcribe", action="store_true")
    run.add_argument("--with-transcribe", action="store_true", help="明确允许本机 Whisper 转写时才启用")
    run.add_argument("--frame-interval", type=int, default=None)
    run.add_argument("--max-frames", type=int, default=12)
    run.add_argument("--model", default="base")
    run.add_argument("--timeout", type=int, default=3600)
    run.set_defaults(func=cmd_run)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        eprint("interrupted")
        return 130
    except subprocess.TimeoutExpired as exc:
        eprint(f"timeout: {exc}")
        return 124


if __name__ == "__main__":
    raise SystemExit(main())
