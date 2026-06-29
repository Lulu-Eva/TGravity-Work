#!/usr/bin/env python3
"""TGW tech canvas video production helper.

This script intentionally stays local-only. It turns an edited talking-head
video plus a transcript, or a locally transcribable audio track, into a synced
local HTML tech canvas background and a validated MP4 background layer. It does
not call cloud ASR services.
"""

from __future__ import annotations

import argparse
import base64
import colorsys
import importlib.util
import http.client
import json
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"
STYLE_PRESETS_FILE = TEMPLATE_DIR / "style-presets.json"
PROJECT_CONFIG_FILE = TEMPLATE_DIR / "project-config.json"
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
DEFAULT_FPS = 24
DEFAULT_TRANSCRIBE_MODEL = "medium"
SCRIPT_INPUTS = [
    Path("input/script.md"),
    Path("input/script.srt"),
    Path("input/script.vtt"),
]
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome",
    "chromium",
    "chromium-browser",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def require_workspace(args: argparse.Namespace) -> Path:
    if not args.workspace:
        raise SystemExit("--workspace is required for this command.")
    return Path(args.workspace).expanduser().resolve()


def find_chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return str(path)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def ffprobe_duration(path: Path) -> float | None:
    if not path.exists() or not shutil.which("ffprobe"):
        return None
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    try:
        duration = float(result.stdout.strip())
    except ValueError:
        return None
    return round(duration, 3) if duration > 0 else None


def run_checked(command: list[str], *, text: bool = True, binary: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=text and not binary)
    if result.returncode != 0:
        stderr = result.stderr if isinstance(result.stderr, str) else result.stderr.decode("utf-8", errors="replace")
        stdout = result.stdout if isinstance(result.stdout, str) else result.stdout.decode("utf-8", errors="replace")
        detail = (stderr or stdout or "").strip()
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result


def source_video_duration(workspace: Path) -> float | None:
    return ffprobe_duration(workspace / "input" / "source.mp4")


def format_srt_time(seconds: float) -> str:
    milliseconds = int(round(max(0.0, seconds) * 1000))
    hours, remainder = divmod(milliseconds, 3600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_transcript_outputs(workspace: Path, segments: list[dict], source: str, model_name: str) -> None:
    srt_lines = []
    md_lines = ["# 视频逐字稿", "", f"来源：{source}", f"转录模型：{model_name}", ""]
    for index, segment in enumerate(segments, start=1):
        start = float(segment.get("start", 0))
        end = float(segment.get("end", start + 1))
        text = re.sub(r"\s+", " ", str(segment.get("text", ""))).strip()
        if not text:
            continue
        srt_lines.extend([str(index), f"{format_srt_time(start)} --> {format_srt_time(end)}", text, ""])
        md_lines.extend([str(index), f"{format_srt_time(start)} --> {format_srt_time(end)}", text, ""])
    (workspace / "input" / "script.srt").write_text("\n".join(srt_lines).strip() + "\n", encoding="utf-8")
    (workspace / "input" / "script.md").write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")


def command_transcribe(args: argparse.Namespace) -> int:
    workspace = require_workspace(args)
    source_path = workspace / "input" / "source.mp4"
    if not source_path.exists():
        raise SystemExit("Missing input/source.mp4. Put the edited talking-head video there before transcribing.")
    if not shutil.which("ffmpeg"):
        raise SystemExit("Missing ffmpeg. Install ffmpeg before local transcription.")
    if not importlib.util.find_spec("whisper"):
        raise SystemExit("Missing Python package 'whisper'. Provide input/script.md, input/script.srt, input/script.vtt, or install openai-whisper locally.")

    import whisper  # type: ignore

    model_name = args.model
    print(f"Loading local Whisper model: {model_name}")
    model = whisper.load_model(model_name)
    result = model.transcribe(
        str(source_path),
        language=args.language,
        task="transcribe",
        fp16=False,
        verbose=False,
    )
    raw_segments = result.get("segments", [])
    segments = []
    for segment in raw_segments:
        text = re.sub(r"\s+", " ", str(segment.get("text", ""))).strip()
        if not text:
            continue
        segments.append(
            {
                "start": round(float(segment.get("start", 0)), 3),
                "end": round(float(segment.get("end", 0)), 3),
                "text": text,
            }
        )
    if not segments:
        raise SystemExit("Whisper returned no transcript segments. Check audio track in input/source.mp4.")

    write_transcript_outputs(workspace, segments, source="input/source.mp4", model_name=model_name)
    write_json(
        workspace / "analysis" / "transcript.json",
        {
            "source": "input/source.mp4",
            "model": model_name,
            "language": args.language,
            "segments": segments,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    print(f"Wrote transcript SRT: {workspace / 'input' / 'script.srt'}")
    print(f"Wrote pipeline script: {workspace / 'input' / 'script.md'}")
    print(f"Wrote transcript JSON: {workspace / 'analysis' / 'transcript.json'}")
    return 0


def parse_timecode(value: str) -> float | None:
    value = value.strip()
    match = re.match(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})(?:[.,](\d{1,3}))?$", value)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        millis = int((match.group(4) or "0").ljust(3, "0")[:3])
        return hours * 3600 + minutes * 60 + seconds + millis / 1000
    match = re.match(r"(\d+(?:\.\d+)?)\s*s", value, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def parse_timestamped_script(text: str) -> list[dict]:
    """Accept simple SRT/VTT-ish and markdown timestamp lines."""
    blocks = re.findall(
        r"(?:^|\n)(?:(?:\d+\s*\n)?(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)\s*-->\s*(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)\s*\n([\s\S]*?))(?=\n\s*\n|\Z)",
        text,
    )
    parsed = []
    for start_raw, end_raw, body in blocks:
        start = parse_timecode(start_raw)
        end = parse_timecode(end_raw)
        clean = re.sub(r"<[^>]+>", "", body).strip()
        clean = re.sub(r"\s+", " ", clean)
        if start is not None and end is not None and end > start and clean:
            parsed.append({"start": round(start, 3), "end": round(end, 3), "text": clean})
    if parsed:
        return parsed

    line_pattern = re.compile(
        r"^\s*(?:[-*]\s*)?(?:\[(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)\]|(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?))\s*(.+)$",
        flags=re.MULTILINE,
    )
    line_items = []
    for match in line_pattern.finditer(text):
        start = parse_timecode(match.group(1) or match.group(2))
        clean = match.group(3).strip()
        if start is not None and clean:
            line_items.append({"start": round(start, 3), "text": clean})
    for index, item in enumerate(line_items):
        next_start = line_items[index + 1]["start"] if index + 1 < len(line_items) else item["start"] + duration_hint(item["text"])
        if next_start > item["start"]:
            parsed.append({"start": item["start"], "end": round(next_start, 3), "text": item["text"]})
    return parsed


def scale_clips_to_duration(clips: list[dict], target_duration: float | None) -> tuple[list[dict], float]:
    current = sum(float(clip.get("duration", 0)) for clip in clips)
    if target_duration and target_duration > 0 and current > 0:
        scale = target_duration / current
        elapsed = 0.0
        scaled = []
        for clip in clips:
            item = dict(clip)
            duration = max(1.0, float(item.get("duration", 1)) * scale)
            item["duration"] = round(duration, 3)
            item["timeline_start"] = round(elapsed, 3)
            elapsed += duration
            scaled.append(item)
        if scaled:
            overflow = round(target_duration - scaled[-1]["timeline_start"], 3)
            scaled[-1]["duration"] = max(1.0, overflow)
        return scaled, round(target_duration, 3)
    return clips, round(current, 3)


def open_http_json(port: int, path: str) -> object:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("GET", path)
    response = connection.getresponse()
    payload = response.read().decode("utf-8")
    connection.close()
    if response.status >= 400:
        raise RuntimeError(f"Chrome DevTools HTTP {response.status}: {payload[:200]}")
    return json.loads(payload)


def websocket_frame(payload: str) -> bytes:
    data = payload.encode("utf-8")
    header = bytearray([0x81])
    length = len(data)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", length))
    mask = b"\x11\x22\x33\x44"
    header.extend(mask)
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
    return bytes(header) + masked


def websocket_read(sock: socket.socket) -> str:
    first = sock.recv(2)
    if len(first) < 2:
        raise RuntimeError("Unexpected empty WebSocket frame.")
    opcode = first[0] & 0x0F
    length = first[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", sock.recv(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", sock.recv(8))[0]
    if first[1] & 0x80:
        mask = sock.recv(4)
    else:
        mask = None
    chunks = []
    remaining = length
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise RuntimeError("Unexpected closed WebSocket.")
        chunks.append(chunk)
        remaining -= len(chunk)
    payload = b"".join(chunks)
    if mask:
        payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    if opcode == 8:
        raise RuntimeError("Chrome closed WebSocket connection.")
    return payload.decode("utf-8")


class ChromeCdp:
    def __init__(self, websocket_url: str):
        match = re.match(r"ws://([^:/]+):(\d+)(/.*)", websocket_url)
        if not match:
            raise RuntimeError(f"Unsupported websocket URL: {websocket_url}")
        host, port, path = match.group(1), int(match.group(2)), match.group(3)
        key = base64.b64encode(b"tgw-render-key").decode("ascii")
        self.sock = socket.create_connection((host, port), timeout=10)
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = self.sock.recv(4096)
        if b" 101 " not in response:
            raise RuntimeError(f"Chrome WebSocket handshake failed: {response[:200]!r}")
        self.next_id = 1

    def call(self, method: str, params: dict | None = None, timeout: float = 20.0) -> dict:
        message_id = self.next_id
        self.next_id += 1
        payload = json.dumps({"id": message_id, "method": method, "params": params or {}})
        self.sock.sendall(websocket_frame(payload))
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = websocket_read(self.sock)
            message = json.loads(raw)
            if message.get("id") != message_id:
                continue
            if "error" in message:
                raise RuntimeError(f"CDP {method} failed: {message['error']}")
            return message.get("result", {})
        raise RuntimeError(f"Timed out waiting for CDP {method}")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


def command_check(args: argparse.Namespace) -> int:
    result = {
        "python": sys.version.split()[0],
        "ffmpeg_available": bool(shutil.which("ffmpeg")),
        "ffprobe_available": bool(shutil.which("ffprobe")),
        "python_whisper_available": bool(importlib.util.find_spec("whisper")),
        "local_transcribe": bool(shutil.which("ffmpeg") and importlib.util.find_spec("whisper")),
        "node_available": bool(shutil.which("node")),
        "npx_available": bool(shutil.which("npx")),
        "chrome_available": bool(find_chrome()),
        "chrome_path": find_chrome(),
        "hyperframes_global_cli_available": bool(shutil.which("hyperframes")),
        "hyperframes_via_npx_checked": False,
        "cloud_asr": False,
        "local_render": bool(shutil.which("ffmpeg") and find_chrome()),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


def command_init(args: argparse.Namespace) -> int:
    workspace = require_workspace(args)
    for relative in [
        "input/assets",
        "analysis/frames",
        "overview",
        "hyperframes",
        "output",
    ]:
        (workspace / relative).mkdir(parents=True, exist_ok=True)

    config_path = workspace / "tech-canvas-project.json"
    if not config_path.exists():
        config = load_json(PROJECT_CONFIG_FILE)
        config["created_at"] = datetime.now().isoformat(timespec="seconds")
        write_json(config_path, config)

    script_path = workspace / "input" / "script.md"
    if not script_path.exists():
        script_path.write_text(
            "# 视频脚本\n\n"
            "请把提前写好的脚本，或“得到大脑”转写后清理出的文稿，粘贴到这里。\n",
            encoding="utf-8",
        )

    style_path = workspace / "input" / "style.md"
    if not style_path.exists():
        style_path.write_text(
            "# 风格要求\n\n"
            "默认使用赛博蓝图 Cyber Blueprint。你也可以写品牌色、参考视频、禁用元素。\n",
            encoding="utf-8",
        )

    print(f"Initialized tech canvas video workspace: {workspace}")
    print("Required next input: input/script.md, input/script.srt, or input/script.vtt")
    print("Recommended video input: input/source.mp4")
    return 0


def is_placeholder_script(path: Path, text: str) -> bool:
    placeholder = "请把提前写好的脚本"
    return path.name == "script.md" and (not text or placeholder in text)


def read_script_with_source(workspace: Path) -> tuple[str, str]:
    errors = []
    for relative_path in SCRIPT_INPUTS:
        script_path = workspace / relative_path
        if not script_path.exists():
            errors.append(f"{relative_path} missing")
            continue
        text = script_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            errors.append(f"{relative_path} empty")
            continue
        if is_placeholder_script(script_path, text):
            errors.append(f"{relative_path} still placeholder")
            continue
        return str(relative_path), text
    raise SystemExit(
        "Missing real script input. Provide input/script.md, input/script.srt, or input/script.vtt "
        f"before running plan. Checked: {', '.join(errors)}."
    )


def read_script(workspace: Path) -> str:
    _, text = read_script_with_source(workspace)
    return text


def has_real_script(workspace: Path) -> bool:
    try:
        read_script_with_source(workspace)
    except SystemExit:
        return False
    return True


def split_script(text: str) -> list[str]:
    structured = re.findall(r"(?:^|\n)##\s+\d+[^\n]*\n([\s\S]*?)(?=\n##\s+\d+|\Z)", text)
    if structured:
        parts = []
        for block in structured:
            match = re.search(r"文案[:：]\s*(.+)", block)
            candidate = match.group(1).strip() if match else block.strip()
            if candidate:
                parts.append(candidate)
        if parts:
            return parts

    normalized = re.sub(r"\s+", " ", text)
    normalized = re.sub(r"^#.*?(?=[\u4e00-\u9fffA-Za-z0-9])", "", normalized).strip()
    chunks = re.split(r"(?<=[。！？!?])\s*", normalized)
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    if len(chunks) <= 1 and len(normalized) > 80:
        chunks = [normalized[i : i + 70].strip() for i in range(0, len(normalized), 70)]
    return chunks or [normalized]


def infer_intent(index: int, total: int, text: str) -> str:
    if index == 0:
        return "开场钩子"
    if index == total - 1:
        return "结尾总结"
    if any(word in text for word in ["步骤", "先", "然后", "接下来", "第一", "第二"]):
        return "步骤说明"
    if any(word in text for word in ["效果", "案例", "展示", "看"]):
        return "效果展示"
    return "内容讲解"


def duration_hint(text: str) -> float:
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    ascii_words = len(re.findall(r"[A-Za-z0-9]+", text))
    seconds = max(3.0, min(8.0, chinese_chars / 7.0 + ascii_words / 2.5))
    return round(seconds, 1)


def visual_need_for(text: str, intent: str) -> str:
    if any(word in text for word in ["Codex", "code", "项目", "软件", "对话"]):
        return "Codex 界面、项目界面或软件操作画面"
    if any(word in text for word in ["效果", "风格", "模板", "总览"]):
        return "效果预览、风格总览站或科技动效画面"
    if intent == "开场钩子":
        return "强视觉开场、成片效果或人物口播"
    if intent == "步骤说明":
        return "操作步骤画面、流程节点或屏幕录制"
    return "与文案语义匹配的视频片段，待人工复核"


def compact_text(text: str, limit: int = 42) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(clean) <= limit:
        return clean
    return clean[: max(1, limit - 3)].rstrip("，。,. ") + "..."


def extract_keywords(text: str, intent: str = "", max_items: int = 4) -> list[str]:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    candidates = [
        ("HyperFrames", "HyperFrames"),
        ("hyper frame", "HyperFrames"),
        ("Codex", "Codex"),
        ("AI", "AI"),
        ("视频", "视频"),
        ("脚本", "脚本"),
        ("逐字稿", "逐字稿"),
        ("转写", "转写"),
        ("剪映", "剪映"),
        ("科技", "科技"),
        ("开源", "开源"),
        ("项目", "项目"),
        ("工具", "工具"),
        ("流程", "流程"),
        ("效率", "效率"),
        ("画布", "画布"),
    ]
    keywords = []
    for needle, label in candidates:
        if needle.lower() in clean.lower() and label not in keywords:
            keywords.append(label)
        if len(keywords) >= max_items:
            return keywords

    for token in re.findall(r"[\u4e00-\u9fff]{2,6}|[A-Za-z][A-Za-z0-9+-]{2,}", clean):
        if token in {"这个", "一个", "就是", "然后", "其实", "可以", "直接", "这里", "我们"}:
            continue
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= max_items:
            break

    if not keywords:
        keywords = [intent or "脚本", "节奏", "画布"]
    return keywords[:max_items]


def normalize_style_key(value: str) -> str:
    normalized = (value or "").strip().lower()
    normalized = re.sub(r"[\s_]+", "-", normalized)
    normalized = re.sub(r"[\"'“”‘’]", "", normalized)
    return normalized


def command_plan(args: argparse.Namespace) -> int:
    workspace = require_workspace(args)
    script_source, text = read_script_with_source(workspace)
    timed_parts = parse_timestamped_script(text)
    source_duration = source_video_duration(workspace)
    segments = []
    clips = []
    if timed_parts:
        parts = [item["text"] for item in timed_parts]
    else:
        parts = split_script(text)

    elapsed = 0.0
    for index, part in enumerate(parts, start=1):
        clean = part.strip()
        intent = infer_intent(index - 1, len(parts), clean)
        if timed_parts:
            start = float(timed_parts[index - 1]["start"])
            end = float(timed_parts[index - 1]["end"])
            duration = round(max(1.0, end - start), 3)
            elapsed = start
        else:
            duration = duration_hint(clean)
        segment_id = f"s{index:02d}"
        segments.append(
            {
                "id": segment_id,
                "text": clean,
                "intent": intent,
                "duration_hint": duration,
                "time_start": round(elapsed, 3),
                "time_end": round(elapsed + duration, 3),
                "visual_need": visual_need_for(clean, intent),
                "needs_review": True,
            }
        )
        clips.append(
            {
                "script_id": segment_id,
                "caption": compact_text(clean, 42),
                "duration": duration,
                "video_start": None,
                "video_end": None,
                "effect": "tech-card-reveal",
                "transition": "glow-line-wipe" if index > 1 else "cold-open",
                "timeline_start": round(elapsed, 3),
                "intent": intent,
                "keywords": extract_keywords(clean, intent),
                "needs_review": True,
            }
        )
        elapsed += duration

    if not timed_parts:
        clips, elapsed = scale_clips_to_duration(clips, source_duration)
        for index, clip in enumerate(clips):
            segments[index]["duration_hint"] = clip["duration"]
            segments[index]["time_start"] = clip["timeline_start"]
            segments[index]["time_end"] = round(clip["timeline_start"] + clip["duration"], 3)
    elif source_duration and elapsed < source_duration:
        elapsed = source_duration

    write_json(
        workspace / "analysis" / "script_segments.json",
            {
                "source": script_source,
                "timing_source": "timestamped_script" if timed_parts else ("input/source.mp4_scaled" if source_duration else "duration_hint"),
                "source_video_duration": source_duration,
                "segments": segments,
        },
    )
    write_json(
        workspace / "analysis" / "timeline.json",
        {
            "source": script_source,
            "timing_source": "timestamped_script" if timed_parts else ("input/source.mp4_scaled" if source_duration else "duration_hint"),
            "source_video_duration": source_duration,
            "total_duration": round(elapsed, 3),
            "clips": clips,
        },
    )
    print(f"Wrote {len(segments)} script segments.")
    print(f"Wrote draft timeline, total duration {round(elapsed, 3)}s.")
    if source_duration:
        print(f"Detected input/source.mp4 duration: {source_duration}s.")
    if timed_parts:
        print("Used timestamped transcript timing.")
    return 0


def render_overview_html(styles: list[dict], timeline: dict | None) -> str:
    total_duration = timeline.get("total_duration") if timeline else "待生成"
    clip_count = len(timeline.get("clips", [])) if timeline else 0
    cards = []
    for style in styles:
        keywords = " / ".join(style["visual_keywords"])
        motion = " / ".join(style["motion_keywords"])
        recommendation = style.get("recommendation", "备选")
        cards.append(
            f"""
      <article class="card" id="{escape(style['id'])}">
        <div class="badge">{escape(style['id'])}</div>
        <div class="recommendation">当前推荐程度：{escape(recommendation)}</div>
        <h2>{escape(style['name'])}</h2>
        <p class="best">{escape(style['best_for'])}</p>
        <div class="preview"><span></span><span></span><span></span></div>
        <p><strong>视觉</strong>{escape(keywords)}</p>
        <p><strong>动效</strong>{escape(motion)}</p>
        <pre>{escape(style['prompt'])}</pre>
      </article>
            """
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TGW Tech Canvas Overview</title>
  <style>
    :root {{
      --bg: #081016;
      --panel: #101a22;
      --panel-2: #13242e;
      --text: #eef8ff;
      --muted: #9eb6c4;
      --accent: #44d7d7;
      --gold: #d7b56d;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--text); }}
    .shell {{ max-width: 1280px; margin: 0 auto; padding: 40px 24px; }}
    header {{ display: grid; grid-template-columns: 1.4fr 0.8fr; gap: 24px; align-items: end; margin-bottom: 28px; }}
    h1 {{ font-size: 44px; margin: 0 0 12px; letter-spacing: 0; }}
    .lead {{ color: var(--muted); font-size: 18px; line-height: 1.6; margin: 0; }}
    .meta {{ background: linear-gradient(135deg, rgba(68,215,215,.16), rgba(215,181,109,.12)); border: 1px solid rgba(255,255,255,.12); padding: 18px; border-radius: 8px; }}
    .meta p {{ margin: 6px 0; color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }}
    .card {{ background: linear-gradient(180deg, var(--panel), var(--panel-2)); border: 1px solid rgba(255,255,255,.1); border-radius: 8px; padding: 18px; min-height: 360px; }}
    .badge {{ color: var(--accent); font-size: 12px; text-transform: uppercase; margin-bottom: 12px; }}
    .recommendation {{ display: inline-block; color: var(--gold); border: 1px solid rgba(215,181,109,.35); padding: 5px 8px; border-radius: 6px; font-size: 13px; margin-bottom: 12px; }}
    h2 {{ font-size: 24px; margin: 0 0 10px; }}
    .best {{ color: var(--gold); min-height: 48px; }}
    .preview {{ height: 96px; border: 1px solid rgba(68,215,215,.28); margin: 16px 0; display: flex; align-items: center; justify-content: center; gap: 14px; background-image: linear-gradient(rgba(68,215,215,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(68,215,215,.08) 1px, transparent 1px); background-size: 18px 18px; }}
    .preview span {{ display: block; width: 46px; height: 32px; border: 1px solid var(--accent); box-shadow: 0 0 18px rgba(68,215,215,.3); }}
    p {{ line-height: 1.55; color: var(--muted); }}
    strong {{ color: var(--text); display: block; margin-bottom: 4px; }}
    pre {{ white-space: pre-wrap; color: #c6dce8; background: rgba(0,0,0,.22); padding: 12px; border-radius: 6px; font-size: 12px; line-height: 1.5; }}
    @media (max-width: 900px) {{
      header, .grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 34px; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <h1>科技画布风格总览</h1>
        <p class="lead">先选风格，再生成本地 HTML 科技画布，确认后渲染并验收背景动画 MP4。</p>
      </div>
      <aside class="meta">
        <p>脚本段数：{clip_count}</p>
        <p>预计时长：{escape(str(total_duration))} 秒</p>
        <p>生成时间：{escape(datetime.now().isoformat(timespec="seconds"))}</p>
      </aside>
    </header>
    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def command_overview(args: argparse.Namespace) -> int:
    workspace = require_workspace(args)
    styles = load_json(STYLE_PRESETS_FILE)["styles"]
    timeline_path = workspace / "analysis" / "timeline.json"
    timeline = load_json(timeline_path) if timeline_path.exists() else None
    html = render_overview_html(styles, timeline)
    overview_path = workspace / "overview" / "index.html"
    overview_path.parent.mkdir(parents=True, exist_ok=True)
    overview_path.write_text(html, encoding="utf-8")
    print(f"Wrote overview: {overview_path}")
    return 0


def style_alias_map(styles: list[dict]) -> dict[str, str]:
    mapping = {}
    for index, style in enumerate(styles, start=1):
        candidates = [
            style["id"],
            str(index),
            f"{index:02d}",
            style["name"],
            *style.get("aliases", []),
        ]
        for candidate in candidates:
            normalized = normalize_style_key(str(candidate))
            if normalized:
                mapping[normalized] = style["id"]
    return mapping


def resolve_style_id(style_query: str, styles: list[dict]) -> str:
    mapping = style_alias_map(styles)
    normalized = normalize_style_key(style_query)
    if normalized in mapping:
        return mapping[normalized]

    for candidate, resolved_id in mapping.items():
        if candidate.isdigit():
            continue
        if len(candidate) >= 2 and candidate in normalized:
            return resolved_id

    # Also accept direct Chinese substrings from the display name.
    stripped = (style_query or "").strip()
    if stripped:
        for style in styles:
            if stripped == style["name"] or stripped in style["name"]:
                return style["id"]
            for alias in style.get("aliases", []):
                if stripped == str(alias):
                    return style["id"]

    numeric_match = re.search(r"(?<!\d)0?([1-6])(?!\d)", normalized)
    if numeric_match and numeric_match.group(0) in mapping:
        return mapping[numeric_match.group(0)]
    if numeric_match and numeric_match.group(1) in mapping:
        return mapping[numeric_match.group(1)]

    available = ", ".join(f"{index}/{style['name']} -> {style['id']}" for index, style in enumerate(styles, start=1))
    raise SystemExit(f"Unknown style '{style_query}'. Available styles: {available}")


def find_style(style_id: str) -> dict:
    styles = load_json(STYLE_PRESETS_FILE)["styles"]
    resolved_id = resolve_style_id(style_id, styles)
    for style in styles:
        if style["id"] == resolved_id:
            return style
    raise SystemExit(f"Resolved style '{resolved_id}' was not found in style presets.")


def load_timeline(workspace: Path) -> dict:
    timeline_path = workspace / "analysis" / "timeline.json"
    if not timeline_path.exists():
        raise SystemExit("Missing analysis/timeline.json. Run plan before hyperframes.")
    timeline = load_json(timeline_path)
    clips = timeline.get("clips", [])
    if not clips:
        raise SystemExit("analysis/timeline.json has no clips.")
    return timeline


def wait_for_chrome(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            open_http_json(port, "/json/version")
            return
        except Exception:
            time.sleep(0.15)
    raise RuntimeError("Chrome DevTools endpoint did not become ready.")


def first_page_websocket(port: int) -> str:
    targets = open_http_json(port, "/json")
    if not isinstance(targets, list):
        raise RuntimeError("Chrome /json target list returned an unexpected payload.")
    for target in targets:
        if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
            return str(target["webSocketDebuggerUrl"])
    raise RuntimeError("No Chrome page target with webSocketDebuggerUrl was found.")


def html_file_url(path: Path) -> str:
    return "file://" + quote(str(path.resolve()))


def run_ffmpeg_image_sequence(frames_dir: Path, fps: int, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%05d.jpg"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    run_checked(command)


def validate_mp4(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Missing MP4 output: {path}")
    duration = ffprobe_duration(path)
    if not duration:
        raise RuntimeError(f"Unable to read MP4 duration: {path}")
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate",
        "-of",
        "json",
        str(path),
    ]
    result = run_checked(command)
    payload = json.loads(result.stdout)
    stream = payload.get("streams", [{}])[0]
    return {
        "path": str(path),
        "duration": duration,
        "width": stream.get("width"),
        "height": stream.get("height"),
        "avg_frame_rate": stream.get("avg_frame_rate"),
    }


def ffprobe_stream_info(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Missing media file: {path}")
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,width,height,avg_frame_rate",
        "-of",
        "json",
        str(path),
    ]
    result = run_checked(command)
    payload = json.loads(result.stdout)
    duration = float(payload.get("format", {}).get("duration") or 0)
    video_stream = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"), {})
    return {
        "path": str(path),
        "duration": round(duration, 3),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "avg_frame_rate": video_stream.get("avg_frame_rate"),
    }


def timeline_total_duration(timeline: dict) -> float | None:
    try:
        duration = float(timeline.get("total_duration") or 0)
    except (TypeError, ValueError):
        return None
    return round(duration, 3) if duration > 0 else None


def extract_validation_frames(mp4_path: Path, output_dir: Path, duration: float) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_file in output_dir.glob("sample_*.jpg"):
        old_file.unlink()
    end_margin = min(0.75, max(0.3, duration * 0.1))
    sample_times = [0.0, max(0.0, duration / 2), max(0.0, duration - end_margin)]
    outputs = []
    for index, second in enumerate(sample_times, start=1):
        output_path = output_dir / f"sample_{index:02d}_{second:.2f}s.jpg"
        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{second:.3f}",
            "-i",
            str(mp4_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ]
        run_checked(command)
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"FFmpeg did not write validation frame at {second:.3f}s: {output_path}")
        outputs.append(str(output_path))
    return outputs


def jpeg_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            return None
        length = int.from_bytes(data[index : index + 2], "big")
        if length < 2 or index + length > len(data):
            return None
        if marker in {0xC0, 0xC1, 0xC2, 0xC3} and length >= 7:
            height = int.from_bytes(data[index + 3 : index + 5], "big")
            width = int.from_bytes(data[index + 5 : index + 7], "big")
            return width, height
        index += length
    return None


def frame_visual_stats(path: Path) -> dict:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Missing ffmpeg for frame visual stats.")
    dimensions = jpeg_dimensions(path)
    if not dimensions:
        raise RuntimeError(f"Unable to read JPEG dimensions: {path}")
    width, height = dimensions
    scale_width = min(96, max(16, width // 10))
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(path),
        "-vf",
        f"scale={scale_width}:-1",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    result = subprocess.run(command, check=True, capture_output=True)
    data = result.stdout
    if len(data) < 3:
        raise RuntimeError(f"No raw pixels decoded from {path}")
    pixels = [data[index : index + 3] for index in range(0, len(data) - 2, 3)]
    if not pixels:
        raise RuntimeError(f"No pixels decoded from {path}")
    luminance_values = []
    hue_buckets = set()
    bright_pixels = 0
    for red, green, blue in pixels:
        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        luminance_values.append(luminance)
        if luminance > 24:
            bright_pixels += 1
        hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        if saturation > 0.12 and value > 0.12:
            hue_buckets.add(int(hue * 24))
    mean_luminance = sum(luminance_values) / len(luminance_values)
    luminance_range = max(luminance_values) - min(luminance_values)
    return {
        "path": str(path),
        "width": width,
        "height": height,
        "sampled_pixels": len(pixels),
        "mean_luminance": round(mean_luminance, 3),
        "luminance_range": round(luminance_range, 3),
        "bright_pixel_ratio": round(bright_pixels / len(pixels), 4),
        "hue_bucket_count": len(hue_buckets),
    }


def validation_frames_nonblank(frame_outputs: list[str]) -> tuple[bool, str, list[dict]]:
    stats = []
    for frame_path in frame_outputs:
        stats.append(frame_visual_stats(Path(frame_path)))
    failures = [
        stat
        for stat in stats
        if stat["mean_luminance"] < 6
        or stat["luminance_range"] < 18
        or stat["bright_pixel_ratio"] < 0.025
    ]
    ok = bool(stats) and not failures
    detail = "; ".join(
        f"{Path(stat['path']).name}: mean={stat['mean_luminance']}, range={stat['luminance_range']}, bright={stat['bright_pixel_ratio']}"
        for stat in stats
    )
    return ok, detail, stats


def validation_item(name: str, passed: bool, detail: str, evidence: str | None = None) -> dict:
    return {"name": name, "passed": passed, "detail": detail, "evidence": evidence}


def render_html_to_mp4(
    html_path: Path,
    output_path: Path,
    width: int,
    height: int,
    fps: int,
    duration: float,
    keep_frames: bool = False,
) -> dict:
    chrome_path = find_chrome()
    if not chrome_path:
        raise SystemExit("Missing Chrome/Chromium. Install Google Chrome or Chromium before rendering MP4.")
    if not shutil.which("ffmpeg"):
        raise SystemExit("Missing ffmpeg. Install ffmpeg before rendering MP4.")

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    frames_parent = output_path.parent / "render_frames"
    if frames_parent.exists():
        shutil.rmtree(frames_parent)
    frames_parent.mkdir(parents=True, exist_ok=True)

    user_data_dir = Path(tempfile.mkdtemp(prefix="tgw-chrome-"))
    chrome_command = [
        chrome_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--hide-scrollbars",
        "about:blank",
    ]
    process = subprocess.Popen(
        chrome_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    cdp = None
    try:
        wait_for_chrome(port)
        cdp = ChromeCdp(first_page_websocket(port))
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )
        cdp.call("Page.navigate", {"url": html_file_url(html_path)})
        deadline = time.time() + 10
        while time.time() < deadline:
            result = cdp.call("Runtime.evaluate", {"expression": "document.readyState", "returnByValue": True})
            if result.get("result", {}).get("value") == "complete":
                break
            time.sleep(0.1)
        cdp.call("Runtime.evaluate", {"expression": "document.fonts && document.fonts.ready", "awaitPromise": True})

        frame_count = max(1, int(duration * fps + 0.999))
        for frame_index in range(frame_count):
            second = min(duration, frame_index / fps)
            cdp.call(
                "Runtime.evaluate",
                {
                    "expression": f"window.__tgwSetTime && window.__tgwSetTime({second:.6f})",
                    "awaitPromise": True,
                },
            )
            screenshot = cdp.call(
                "Page.captureScreenshot",
                {
                    "format": "jpeg",
                    "quality": 92,
                    "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1},
                    "captureBeyondViewport": False,
                },
                timeout=30,
            )
            image_bytes = base64.b64decode(screenshot["data"])
            (frames_parent / f"frame_{frame_index + 1:05d}.jpg").write_bytes(image_bytes)

        run_ffmpeg_image_sequence(frames_parent, fps, output_path)
    finally:
        if cdp:
            cdp.close()
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=3)
        shutil.rmtree(user_data_dir, ignore_errors=True)
        if not keep_frames:
            shutil.rmtree(frames_parent, ignore_errors=True)

    return validate_mp4(output_path)


def style_theme(style_id: str) -> dict:
    themes = {
        "cyber-blueprint": {"bg": "#07131d", "panel": "#102332", "accent": "#48e1e7", "accent2": "#7cf7c7"},
        "dark-launch": {"bg": "#080706", "panel": "#18130d", "accent": "#d7b56d", "accent2": "#fff0bd"},
        "glass-dashboard": {"bg": "#091018", "panel": "#142430", "accent": "#9edcff", "accent2": "#f7fbff"},
        "data-radar": {"bg": "#06110d", "panel": "#102018", "accent": "#5dff9d", "accent2": "#62d7ff"},
        "minimal-tech": {"bg": "#f4f7f8", "panel": "#ffffff", "accent": "#161d22", "accent2": "#54707d"},
        "product-roadmap": {"bg": "#0b0d16", "panel": "#181d2d", "accent": "#8ca5ff", "accent2": "#54f0c3"},
    }
    return themes.get(style_id, themes["cyber-blueprint"])


def render_hyperframes_html(style: dict, timeline: dict) -> str:
    clips = timeline["clips"]
    duration = float(timeline.get("total_duration") or sum(float(clip.get("duration", 4)) for clip in clips))
    theme = style_theme(style["id"])
    scenes = []
    scene_payload = []
    rail_nodes = []

    for index, clip in enumerate(clips):
        start = float(clip.get("timeline_start", 0))
        clip_duration = float(clip.get("duration", 4))
        raw_caption = str(clip.get("caption") or f"Scene {index + 1}")
        caption = escape(compact_text(raw_caption, 48))
        intent = str(clip.get("intent") or clip.get("effect") or "内容讲解")
        keywords = clip.get("keywords") or extract_keywords(raw_caption, intent)
        keyword_markup = "".join(f'<span class="keyword-chip">{escape(str(keyword))}</span>' for keyword in keywords[:4])
        transition = escape(str(clip.get("transition") or "tech-transition"))
        effect = str(clip.get("effect") or "tech-card-reveal")
        full_text = raw_caption
        density = min(99, max(18, len(full_text) * 2))
        node_left = 0 if duration <= 0 else min(96, max(0, start / duration * 100))
        scene_payload.append(
            {
                "index": index,
                "start": round(start, 3),
                "duration": round(clip_duration, 3),
                "caption": full_text,
                "intent": intent,
                "keywords": keywords[:4],
                "effect": effect,
                "transition": str(clip.get("transition") or "tech-transition"),
            }
        )
        rail_nodes.append(
            f"""
      <span class="rail-node" data-node-index="{index}" style="left: {node_left:.3f}%;">
        <b>{index + 1:02d}</b>
      </span>"""
        )
        scenes.append(
            f"""
    <section class="scene clip" data-start="{start:.3f}" data-duration="{clip_duration:.3f}" data-track-index="{index}">
      <div class="scene-frame">
        <div class="scene-kicker">BEAT {index + 1:02d} / {escape(intent)}</div>
        <h2>{caption}</h2>
        <div class="keyword-row">{keyword_markup}</div>
        <div class="scene-grid">
          <div class="scene-metric">
            <span>SYNC</span>
            <strong>{start:.1f}s - {start + clip_duration:.1f}s</strong>
          </div>
          <div class="scene-metric">
            <span>TEXT DENSITY</span>
            <strong>{density:02d}%</strong>
          </div>
          <div class="scene-metric">
            <span>SCRIPT ID</span>
            <strong>{escape(str(clip.get("script_id") or f"s{index + 1:02d}"))}</strong>
          </div>
        </div>
      </div>
      <div class="scan-line"></div>
    </section>"""
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TGW Tech Canvas Production - {escape(style['name'])}</title>
  <style>
    :root {{
      --bg: {theme['bg']};
      --panel: {theme['panel']};
      --accent: {theme['accent']};
      --accent-2: {theme['accent2']};
      --text: #f4fbff;
      --muted: rgba(244, 251, 255, 0.68);
      --progress: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #05080c; color: var(--text); }}
    #stage {{
      position: relative;
      width: 1080px;
      height: 1920px;
      overflow: hidden;
      background:
        linear-gradient(128deg, color-mix(in srgb, var(--accent) 10%, transparent), transparent 34%),
        linear-gradient(210deg, color-mix(in srgb, var(--accent-2) 8%, transparent), transparent 28%),
        linear-gradient(160deg, var(--bg), #020406 76%);
    }}
    #stage::before {{
      content: "";
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.055) 1px, transparent 1px);
      background-size: 54px 54px;
      opacity: .48;
      transform: translate3d(calc(var(--progress) * -54px), calc(var(--progress) * -88px), 0);
    }}
    #stage::after {{
      content: "";
      position: absolute;
      inset: 0;
      background:
        repeating-linear-gradient(0deg, transparent 0 38px, rgba(255,255,255,.035) 39px 40px),
        linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 16%, transparent), transparent);
      mix-blend-mode: screen;
      opacity: .34;
      transform: translateX(calc((var(--progress) - .5) * 220px));
      pointer-events: none;
    }}
    .title-bar {{
      position: absolute;
      left: 70px;
      right: 70px;
      top: 70px;
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      letter-spacing: .08em;
      font-size: 25px;
      text-transform: uppercase;
      z-index: 5;
    }}
    .title-bar strong {{
      color: var(--text);
      font-weight: 700;
    }}
    .motion-rail {{
      position: absolute;
      left: 70px;
      right: 470px;
      top: 160px;
      height: 82px;
      z-index: 6;
    }}
    .motion-rail::before {{
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      top: 38px;
      height: 2px;
      background: color-mix(in srgb, var(--accent) 24%, transparent);
    }}
    .progress-fill {{
      position: absolute;
      left: 0;
      top: 37px;
      height: 4px;
      width: calc(var(--progress) * 100%);
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      box-shadow: 0 0 26px color-mix(in srgb, var(--accent) 42%, transparent);
    }}
    .rail-node {{
      position: absolute;
      top: 22px;
      width: 34px;
      height: 34px;
      margin-left: -17px;
      border: 1px solid color-mix(in srgb, var(--accent) 50%, transparent);
      background: color-mix(in srgb, var(--panel) 82%, black);
      transform: rotate(45deg);
      opacity: .48;
    }}
    .rail-node b {{
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
      transform: rotate(-45deg);
      font-size: 13px;
      color: var(--muted);
      font-variant-numeric: tabular-nums;
    }}
    .rail-node.is-active {{
      opacity: 1;
      border-color: var(--accent-2);
      box-shadow: 0 0 24px color-mix(in srgb, var(--accent-2) 36%, transparent);
    }}
    .scene {{
      position: absolute;
      left: 70px;
      right: 470px;
      top: 280px;
      min-height: 760px;
      padding: 0;
      border: 1px solid color-mix(in srgb, var(--accent) 42%, transparent);
      background:
        linear-gradient(90deg, color-mix(in srgb, var(--accent) 13%, transparent), transparent 42%),
        linear-gradient(180deg, color-mix(in srgb, var(--panel) 88%, transparent), rgba(0,0,0,.36));
      box-shadow: 0 0 72px color-mix(in srgb, var(--accent) 17%, transparent);
      opacity: 0;
      z-index: 2;
    }}
    .scene-frame {{
      position: relative;
      min-height: 760px;
      padding: 70px 58px 52px;
      overflow: hidden;
    }}
    .scene-frame::before {{
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(90deg, transparent 0, color-mix(in srgb, var(--accent) 16%, transparent) 50%, transparent 100%),
        repeating-linear-gradient(90deg, transparent 0 96px, color-mix(in srgb, var(--accent) 8%, transparent) 96px 98px);
      opacity: .25;
      transform: skewY(-8deg);
    }}
    .scene-kicker {{
      position: relative;
      color: var(--accent);
      font-size: 26px;
      letter-spacing: .1em;
      margin-bottom: 42px;
    }}
    h2 {{
      position: relative;
      margin: 0;
      max-width: 820px;
      font-size: 76px;
      line-height: 1.08;
      letter-spacing: 0;
    }}
    .keyword-row {{
      position: relative;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 34px;
    }}
    .keyword-chip {{
      border: 1px solid color-mix(in srgb, var(--accent) 36%, transparent);
      background: color-mix(in srgb, var(--accent) 9%, transparent);
      color: var(--accent-2);
      padding: 9px 13px;
      font-size: 24px;
      line-height: 1;
      max-width: 220px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .scene-grid {{
      position: relative;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 68px;
    }}
    .scene-metric {{
      min-height: 108px;
      border: 1px solid rgba(255,255,255,.12);
      background: rgba(0,0,0,.2);
      padding: 16px;
    }}
    .scene-metric span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      letter-spacing: .1em;
      margin-bottom: 14px;
    }}
    .scene-metric strong {{
      display: block;
      color: var(--text);
      font-size: 22px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }}
    .scan-line {{
      position: absolute;
      left: -45%;
      top: 0;
      width: 40%;
      height: 100%;
      background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent-2) 30%, transparent), transparent);
      transform: skewX(-12deg);
    }}
    .data-column {{
      position: absolute;
      right: 70px;
      top: 280px;
      width: 335px;
      display: grid;
      gap: 16px;
      z-index: 5;
    }}
    .data-module {{
      border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent);
      background: rgba(0,0,0,.28);
      padding: 18px;
      min-height: 116px;
    }}
    .data-module span {{
      display: block;
      color: var(--accent);
      font-size: 15px;
      letter-spacing: .11em;
      margin-bottom: 10px;
      text-transform: uppercase;
    }}
    .data-module strong {{
      display: block;
      color: var(--text);
      font-size: 29px;
      line-height: 1.15;
      font-variant-numeric: tabular-nums;
      overflow-wrap: anywhere;
    }}
    .signal-bars {{
      display: grid;
      grid-template-columns: repeat(10, 1fr);
      gap: 5px;
      height: 58px;
      align-items: end;
    }}
    .signal-bars i {{
      display: block;
      min-height: 8px;
      background: linear-gradient(180deg, var(--accent-2), var(--accent));
      opacity: .72;
    }}
    .signal-bars i:nth-child(1) {{ height: 24%; }}
    .signal-bars i:nth-child(2) {{ height: 62%; }}
    .signal-bars i:nth-child(3) {{ height: 38%; }}
    .signal-bars i:nth-child(4) {{ height: 84%; }}
    .signal-bars i:nth-child(5) {{ height: 52%; }}
    .signal-bars i:nth-child(6) {{ height: 71%; }}
    .signal-bars i:nth-child(7) {{ height: 45%; }}
    .signal-bars i:nth-child(8) {{ height: 92%; }}
    .signal-bars i:nth-child(9) {{ height: 33%; }}
    .signal-bars i:nth-child(10) {{ height: 64%; }}
    .footer {{
      position: absolute;
      left: 70px;
      right: 470px;
      bottom: 84px;
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 24px;
      z-index: 5;
    }}
    .portrait-safe-zone {{
      position: absolute;
      right: 54px;
      bottom: 54px;
      width: 365px;
      height: 590px;
      border: 1px solid color-mix(in srgb, var(--accent) 16%, transparent);
      background:
        linear-gradient(180deg, rgba(0,0,0,.02), rgba(0,0,0,.36)),
        repeating-linear-gradient(135deg, transparent 0 18px, color-mix(in srgb, var(--accent) 6%, transparent) 18px 20px);
      box-shadow: inset 0 0 80px rgba(0,0,0,.32);
      z-index: 3;
    }}
    .hud {{
      position: absolute;
      left: 70px;
      right: 480px;
      bottom: 170px;
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 16px;
      z-index: 5;
    }}
    .hud-card {{
      border: 1px solid color-mix(in srgb, var(--accent) 26%, transparent);
      background: rgba(0,0,0,.24);
      padding: 16px;
      min-height: 88px;
    }}
    .hud-label {{
      display: block;
      color: var(--accent);
      font-size: 16px;
      letter-spacing: .1em;
      margin-bottom: 8px;
    }}
    .hud-value {{
      display: block;
      color: var(--text);
      font-size: 26px;
      line-height: 1.25;
      font-variant-numeric: tabular-nums;
    }}
  </style>
</head>
<body>
  <div id="stage" data-composition-id="tgw-tech-canvas" data-start="0" data-width="1080" data-height="1920" data-duration="{duration:.1f}">
    <div class="title-bar">
      <span><strong>TGW</strong> / {escape(style['name'])}</span>
      <span>{len(clips)} clips / {duration:.1f}s</span>
    </div>
    <div class="motion-rail" aria-hidden="true">
      <div class="progress-fill" id="progressFill"></div>
      {''.join(rail_nodes)}
    </div>
{''.join(scenes)}
    <div class="data-column">
      <div class="data-module"><span>ACTIVE INTENT</span><strong id="activeIntent">开场钩子</strong></div>
      <div class="data-module"><span>TIMEBASE</span><strong id="timebase">0.0s</strong></div>
      <div class="data-module"><span>SIGNAL</span><div class="signal-bars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
    </div>
    <div class="hud">
      <div class="hud-card"><span class="hud-label">ACTIVE BEAT</span><span class="hud-value" id="activeBeat">SCENE 01</span></div>
      <div class="hud-card"><span class="hud-label">SCRIPT SYNC</span><span class="hud-value" id="scriptSync">0.0s</span></div>
      <div class="hud-card"><span class="hud-label">CANVAS LOAD</span><span class="hud-value" id="canvasLoad">0%</span></div>
    </div>
    <div class="portrait-safe-zone" aria-hidden="true"></div>
    <div class="footer">
      <span>TGW</span>
      <span>background render layer</span>
    </div>
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    window.__tgwScenes = {json.dumps(scene_payload, ensure_ascii=False)};
    const scenes = Array.from(document.querySelectorAll(".scene.clip"));
    const railNodes = Array.from(document.querySelectorAll(".rail-node"));
    const stage = document.getElementById("stage");
    const duration = {duration:.3f};
    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
    const findActive = (seconds) => (
      window.__tgwScenes.find((item) => seconds >= item.start && seconds < item.start + item.duration)
      || window.__tgwScenes[window.__tgwScenes.length - 1]
    );
    const renderAt = (seconds) => {{
      const clamped = clamp(seconds, 0, duration);
      const progress = duration > 0 ? clamped / duration : 0;
      stage.style.setProperty("--progress", progress.toFixed(5));
      document.getElementById("progressFill").style.width = (progress * 100).toFixed(2) + "%";
      const activeScene = findActive(clamped);
      scenes.forEach((scene, index) => {{
        const meta = window.__tgwScenes[index];
        const local = clamped - meta.start;
        const active = local >= 0 && local < meta.duration;
        const near = Math.abs(local) < 0.8 || Math.abs(local - meta.duration) < 0.8;
        scene.style.opacity = active ? "1" : (near ? ".18" : "0");
        scene.style.transform = active
          ? "translate3d(" + (-10 + clamp(local / Math.max(0.1, meta.duration), 0, 1) * 10).toFixed(2) + "px, " + Math.max(-18, 34 - local * 28).toFixed(2) + "px, 0) scale(" + Math.min(1, 0.982 + local * 0.024).toFixed(4) + ")"
          : "translate3d(26px, 28px, 0) scale(.982)";
        const scanLine = scene.querySelector(".scan-line");
        if (scanLine) {{
          const progress = Math.max(0, Math.min(1, local / Math.max(0.1, meta.duration)));
          scanLine.style.transform = "translateX(" + (progress * 250).toFixed(2) + "%) skewX(-12deg)";
        }}
      }});
      railNodes.forEach((node, index) => {{
        node.classList.toggle("is-active", activeScene && index <= activeScene.index);
      }});
      if (activeScene) {{
        document.getElementById("activeBeat").textContent = "SCENE " + String(activeScene.index + 1).padStart(2, "0");
        document.getElementById("scriptSync").textContent = clamped.toFixed(1) + "s / " + duration.toFixed(1) + "s";
        document.getElementById("activeIntent").textContent = activeScene.intent || activeScene.effect || "内容讲解";
        document.getElementById("timebase").textContent = clamped.toFixed(2) + "s";
        document.getElementById("canvasLoad").textContent = Math.round(progress * 100) + "%";
      }}
    }};
    const tl = {{ seek(seconds) {{ renderAt(seconds); return this; }} }};
    window.__timelines["tgw-tech-canvas"] = tl;
    window.__tgwProduction = {{
      style: {json.dumps(style["id"], ensure_ascii=False)},
      duration: {duration:.3f},
      clips: {len(clips)}
    }};
    window.__tgwSetTime = function(seconds) {{
      const clamped = clamp(seconds, 0, duration);
      tl.seek(clamped, false);
      renderAt(clamped);
    }};
    window.__tgwSetTime(0);
  </script>
</body>
</html>
"""


def command_hyperframes(args: argparse.Namespace) -> int:
    workspace = require_workspace(args)
    timeline = load_timeline(workspace)
    style = find_style(args.style)
    html = render_hyperframes_html(style, timeline)
    output_path = workspace / "hyperframes" / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote local HTML tech canvas: {output_path}")
    print("Next: render output/background.mp4 after review.")
    return 0


def command_render(args: argparse.Namespace) -> int:
    workspace = require_workspace(args)
    html_path = workspace / "hyperframes" / "index.html"
    if not html_path.exists():
        raise SystemExit("Missing hyperframes/index.html. Run hyperframes before render.")
    timeline = load_timeline(workspace)
    timeline_duration = timeline_total_duration(timeline) or 0
    source_duration = source_video_duration(workspace)
    duration = args.duration or source_duration or timeline_duration
    duration_source = "cli_arg" if args.duration else ("input/source.mp4" if source_duration else "analysis/timeline.json")
    timeline_source_delta = None
    timeline_source_warning = None
    if source_duration and timeline_duration:
        timeline_source_delta = round(abs(float(timeline_duration) - float(source_duration)), 3)
        if timeline_source_delta > 0.25:
            timeline_source_warning = (
                "analysis/timeline.json total_duration differs from input/source.mp4. "
                "Run plan again after fixing transcript timestamps, or pass an explicit --duration only for deliberate overrides."
            )
    if not duration or duration <= 0:
        raise SystemExit("Unable to determine render duration. Provide --duration or run plan with input/source.mp4.")
    output_path = Path(args.output).expanduser().resolve() if args.output else workspace / "output" / "background.mp4"
    report = render_html_to_mp4(
        html_path=html_path,
        output_path=output_path,
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration=float(duration),
        keep_frames=args.keep_frames,
    )
    report.update(
        {
            "source_html": str(html_path),
            "source_video_duration": source_duration,
            "timeline_duration": timeline_duration,
            "timeline_source_delta": timeline_source_delta,
            "timeline_source_warning": timeline_source_warning,
            "render_duration_source": duration_source,
            "render_width": args.width,
            "render_height": args.height,
            "render_fps": args.fps,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    write_json(workspace / "output" / "render_report.json", report)
    print(f"Wrote background MP4: {output_path}")
    print(f"Wrote render report: {workspace / 'output' / 'render_report.json'}")
    if timeline_source_warning:
        print(f"Warning: {timeline_source_warning} delta={timeline_source_delta:.3f}s")
    return 0


def command_produce(args: argparse.Namespace) -> int:
    workspace = require_workspace(args)
    require_source_video = not args.allow_missing_source_video
    source_path = workspace / "input" / "source.mp4"
    if require_source_video and not source_path.exists():
        raise SystemExit("Missing input/source.mp4. Production mode requires the edited talking-head video to lock duration sync.")

    command_init(argparse.Namespace(workspace=str(workspace)))

    transcribed_locally = False
    if not has_real_script(workspace):
        if not args.transcribe_if_missing:
            raise SystemExit(
                "Missing real input/script.md, input/script.srt, or input/script.vtt. Add a transcript, or rerun produce with --transcribe-if-missing "
                "to create a local Whisper draft from input/source.mp4."
            )
        command_transcribe(
            argparse.Namespace(
                workspace=str(workspace),
                model=args.model,
                language=args.language,
            )
        )
        transcribed_locally = True

    if not has_real_script(workspace):
        raise SystemExit("script input is still missing or placeholder text after transcription.")

    command_plan(argparse.Namespace(workspace=str(workspace)))
    command_overview(argparse.Namespace(workspace=str(workspace)))
    command_hyperframes(argparse.Namespace(workspace=str(workspace), style=args.style))
    command_render(
        argparse.Namespace(
            workspace=str(workspace),
            output=None,
            duration=args.duration,
            fps=args.fps,
            width=args.width,
            height=args.height,
            keep_frames=args.keep_frames,
        )
    )
    style_id = resolve_style_id(args.style, load_json(STYLE_PRESETS_FILE)["styles"])
    manifest_path = workspace / "output" / "production_manifest.json"
    manifest = {
        "project_type": "tgw-tech-canvas-video-production",
        "workspace": str(workspace),
        "style": style_id,
        "source_video": str(source_path) if source_path.exists() else None,
        "transcribed_locally": transcribed_locally,
        "outputs": {
            "overview": str(workspace / "overview" / "index.html"),
            "html_canvas": str(workspace / "hyperframes" / "index.html"),
            "background_mp4": str(workspace / "output" / "background.mp4"),
            "render_report": str(workspace / "output" / "render_report.json"),
            "validation_report": str(workspace / "output" / "validation_report.json"),
            "validation_frames": str(workspace / "output" / "validation_frames"),
        },
        "validation_passed": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_json(manifest_path, manifest)
    validation_code = command_validate(
        argparse.Namespace(
            workspace=str(workspace),
            width=args.width,
            height=args.height,
            duration_tolerance=args.duration_tolerance,
            require_source_video=require_source_video,
            require_production_manifest=True,
        )
    )

    validation_report_path = workspace / "output" / "validation_report.json"
    validation_report = load_json(validation_report_path) if validation_report_path.exists() else {}
    manifest["validation_passed"] = bool(validation_report.get("passed")) and validation_code == 0
    manifest["validated_at"] = datetime.now().isoformat(timespec="seconds")
    write_json(manifest_path, manifest)
    print(f"Wrote production manifest: {manifest_path}")
    print(f"Production MP4 ready: {manifest['validation_passed']}")
    return validation_code


def command_validate(args: argparse.Namespace) -> int:
    workspace = require_workspace(args)
    items = []

    script_paths = [(workspace / relative_path, str(relative_path)) for relative_path in SCRIPT_INPUTS]
    transcript_path = workspace / "analysis" / "transcript.json"
    segments_path = workspace / "analysis" / "script_segments.json"
    timeline_path = workspace / "analysis" / "timeline.json"
    overview_path = workspace / "overview" / "index.html"
    html_path = workspace / "hyperframes" / "index.html"
    background_path = workspace / "output" / "background.mp4"
    render_report_path = workspace / "output" / "render_report.json"
    production_manifest_path = workspace / "output" / "production_manifest.json"

    script_source = None
    script_text = ""
    script_errors = []
    for script_path, relative_path in script_paths:
        if not script_path.exists():
            script_errors.append(f"{relative_path} missing")
            continue
        text = script_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            script_errors.append(f"{relative_path} empty")
            continue
        if is_placeholder_script(script_path, text):
            script_errors.append(f"{relative_path} still placeholder")
            continue
        script_source = relative_path
        script_text = text
        break
    items.append(
        validation_item(
            "script input exists",
            bool(script_source),
            script_source or "; ".join(script_errors),
            str((workspace / script_source) if script_source else (workspace / "input")),
        )
    )
    if script_source and script_source.endswith((".srt", ".vtt")):
        items.append(validation_item(f"{script_source} has timecodes", "-->" in script_text, "caption file contains --> timecode markers", str(workspace / script_source)))
    if transcript_path.exists():
        try:
            transcript = load_json(transcript_path)
            transcript_segments = transcript.get("segments", [])
            items.append(validation_item("analysis/transcript.json has segments", bool(transcript_segments), f"{len(transcript_segments)} segments", str(transcript_path)))
        except Exception as error:
            items.append(validation_item("analysis/transcript.json parseable", False, str(error), str(transcript_path)))

    try:
        segments_payload = load_json(segments_path)
        segments = segments_payload.get("segments", [])
        empty_segments = [segment.get("id", "?") for segment in segments if not str(segment.get("text", "")).strip()]
        items.append(validation_item("script segments exist", bool(segments), f"{len(segments)} segments", str(segments_path)))
        items.append(validation_item("script segments have text", not empty_segments, f"empty={empty_segments}", str(segments_path)))
    except Exception as error:
        segments = []
        items.append(validation_item("analysis/script_segments.json parseable", False, str(error), str(segments_path)))

    try:
        timeline = load_json(timeline_path)
        clips = timeline.get("clips", [])
        script_ids = {segment.get("id") for segment in segments}
        missing_links = [clip.get("script_id") for clip in clips if clip.get("script_id") not in script_ids]
        items.append(validation_item("timeline clips exist", bool(clips), f"{len(clips)} clips", str(timeline_path)))
        items.append(validation_item("timeline clips link to script_id", not missing_links, f"missing={missing_links}", str(timeline_path)))
    except Exception as error:
        timeline = {}
        items.append(validation_item("analysis/timeline.json parseable", False, str(error), str(timeline_path)))

    source_path = workspace / "input" / "source.mp4"
    source_info = None
    source_error = None
    if source_path.exists():
        try:
            source_info = ffprobe_stream_info(source_path)
        except Exception as error:
            source_error = str(error)
    if args.require_source_video:
        items.append(validation_item("input/source.mp4 exists", source_path.exists(), str(source_path), str(source_path)))
        if source_path.exists():
            detail = json.dumps(source_info, ensure_ascii=False) if source_info else str(source_error)
            items.append(validation_item("input/source.mp4 readable", bool(source_info), detail, str(source_path)))
    timeline_duration = timeline_total_duration(timeline) if timeline else None
    if source_info and timeline_duration:
        delta = abs(float(timeline_duration) - float(source_info["duration"]))
        items.append(
            validation_item(
                "timeline duration matches source",
                delta <= args.duration_tolerance,
                f"timeline={timeline_duration:.3f}s source={float(source_info['duration']):.3f}s delta={delta:.3f}s tolerance={args.duration_tolerance}s",
                str(timeline_path),
            )
        )
    elif source_info and timeline:
        items.append(validation_item("timeline duration matches source", False, "analysis/timeline.json has no positive total_duration", str(timeline_path)))

    if overview_path.exists():
        overview_text = overview_path.read_text(encoding="utf-8", errors="ignore")
        overview_ok = all(token in overview_text for token in ["科技画布风格总览", "cyber-blueprint", "dark-launch", "当前推荐程度"])
        items.append(validation_item("overview HTML has required markers", overview_ok, "style overview markers", str(overview_path)))
    else:
        items.append(validation_item("overview/index.html exists", False, str(overview_path), str(overview_path)))

    if html_path.exists():
        html_text = html_path.read_text(encoding="utf-8", errors="ignore")
        markers = [
            "data-composition-id",
            "window.__timelines",
            "window.__tgwSetTime",
            "scene clip",
            "portrait-safe-zone",
            "motion-rail",
            "data-column",
            "keyword-chip",
            "canvasLoad",
        ]
        missing_markers = [marker for marker in markers if marker not in html_text]
        items.append(validation_item("background HTML has required markers", not missing_markers, f"missing={missing_markers}", str(html_path)))
        items.append(validation_item("background HTML has no cloud ASR key", "ASR API" not in html_text and "TENCENT" not in html_text.upper(), "no obvious cloud ASR key markers", str(html_path)))
    else:
        items.append(validation_item("hyperframes/index.html exists", False, str(html_path), str(html_path)))

    background_info = None
    if background_path.exists():
        try:
            background_info = ffprobe_stream_info(background_path)
            items.append(validation_item("background MP4 readable", True, json.dumps(background_info, ensure_ascii=False), str(background_path)))
            expected_width = int(args.width)
            expected_height = int(args.height)
            resolution_ok = background_info.get("width") == expected_width and background_info.get("height") == expected_height
            items.append(validation_item("background MP4 resolution", resolution_ok, f"{background_info.get('width')}x{background_info.get('height')} expected {expected_width}x{expected_height}", str(background_path)))
            if source_info:
                delta = abs(float(background_info["duration"]) - float(source_info["duration"]))
                items.append(validation_item("background duration matches source", delta <= args.duration_tolerance, f"delta={delta:.3f}s tolerance={args.duration_tolerance}s", str(background_path)))
        except Exception as error:
            items.append(validation_item("background MP4 readable", False, str(error), str(background_path)))
    else:
        items.append(validation_item("output/background.mp4 exists", False, str(background_path), str(background_path)))

    if render_report_path.exists():
        try:
            report = load_json(render_report_path)
            required_keys = ["path", "duration", "width", "height", "avg_frame_rate", "source_html", "created_at"]
            missing_keys = [key for key in required_keys if key not in report]
            items.append(validation_item("render report has required keys", not missing_keys, f"missing={missing_keys}", str(render_report_path)))
        except Exception as error:
            items.append(validation_item("render report parseable", False, str(error), str(render_report_path)))
    else:
        items.append(validation_item("output/render_report.json exists", False, str(render_report_path), str(render_report_path)))

    if production_manifest_path.exists():
        try:
            manifest = load_json(production_manifest_path)
            outputs = manifest.get("outputs", {})
            required_output_keys = ["html_canvas", "background_mp4", "render_report", "validation_report", "validation_frames"]
            missing_output_keys = [key for key in required_output_keys if key not in outputs]
            items.append(validation_item("production manifest has output paths", not missing_output_keys, f"missing={missing_output_keys}", str(production_manifest_path)))
        except Exception as error:
            items.append(validation_item("production manifest parseable", False, str(error), str(production_manifest_path)))
    elif args.require_production_manifest:
        items.append(validation_item("output/production_manifest.json exists", False, str(production_manifest_path), str(production_manifest_path)))

    frame_outputs = []
    frame_stats = []
    if background_info:
        try:
            frame_outputs = extract_validation_frames(
                background_path,
                workspace / "output" / "validation_frames",
                float(background_info["duration"]),
            )
            items.append(validation_item("validation frames extracted", bool(frame_outputs), f"{len(frame_outputs)} frames", str(workspace / "output" / "validation_frames")))
            frames_ok, frames_detail, frame_stats = validation_frames_nonblank(frame_outputs)
            items.append(validation_item("validation frames are nonblank", frames_ok, frames_detail, str(workspace / "output" / "validation_frames")))
        except Exception as error:
            items.append(validation_item("validation frames extracted", False, str(error), str(workspace / "output" / "validation_frames")))

    passed = all(item["passed"] for item in items)
    validation_report = {
        "passed": passed,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "source_video": source_info,
        "background_video": background_info,
        "validation_frames": frame_outputs,
        "validation_frame_stats": frame_stats,
        "items": items,
    }
    output_path = workspace / "output" / "validation_report.json"
    write_json(output_path, validation_report)
    print(f"Wrote validation report: {output_path}")
    print(f"Validation passed: {passed}")
    return 0 if passed else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TGW tech canvas video production helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Check local dependencies")
    check_parser.add_argument("--json", action="store_true", help="Print JSON")
    check_parser.set_defaults(func=command_check)

    for name, help_text, func in [
        ("init", "Initialize workspace", command_init),
        ("transcribe", "Transcribe input/source.mp4 to input/script.md and input/script.srt using local Whisper", command_transcribe),
        ("plan", "Create script segments and draft timeline", command_plan),
        ("overview", "Create style overview HTML", command_overview),
    ]:
        subparser = subparsers.add_parser(name, help=help_text)
        subparser.add_argument("--workspace", required=True, help="Project workspace path")
        if name == "transcribe":
            subparser.add_argument("--model", default=DEFAULT_TRANSCRIBE_MODEL, help=f"Local Whisper model name. Default: {DEFAULT_TRANSCRIBE_MODEL}")
            subparser.add_argument("--language", default="zh", help="Transcription language. Default: zh")
        subparser.set_defaults(func=func)

    hyperframes_parser = subparsers.add_parser("hyperframes", help="Create local HTML tech canvas")
    hyperframes_parser.add_argument("--workspace", required=True, help="Project workspace path")
    hyperframes_parser.add_argument("--style", required=True, help="Style id, number, Chinese name, or English display name")
    hyperframes_parser.set_defaults(func=command_hyperframes)

    render_parser = subparsers.add_parser("render", help="Render hyperframes/index.html to output/background.mp4")
    render_parser.add_argument("--workspace", required=True, help="Project workspace path")
    render_parser.add_argument("--output", help="Output MP4 path. Defaults to output/background.mp4")
    render_parser.add_argument("--duration", type=float, help="Render duration in seconds. Defaults to input/source.mp4 duration or timeline duration")
    render_parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help=f"Frames per second. Default: {DEFAULT_FPS}")
    render_parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help=f"Render width. Default: {DEFAULT_WIDTH}")
    render_parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help=f"Render height. Default: {DEFAULT_HEIGHT}")
    render_parser.add_argument("--keep-frames", action="store_true", help="Keep intermediate JPEG frames in output/render_frames")
    render_parser.set_defaults(func=command_render)

    produce_parser = subparsers.add_parser("produce", help="Run production pipeline through validated output/background.mp4")
    produce_parser.add_argument("--workspace", required=True, help="Project workspace path")
    produce_parser.add_argument("--style", default="cyber-blueprint", help="Style id, number, Chinese name, or English display name. Default: cyber-blueprint")
    produce_parser.add_argument("--transcribe-if-missing", action="store_true", help="Use local Whisper if no script input exists")
    produce_parser.add_argument("--model", default=DEFAULT_TRANSCRIBE_MODEL, help=f"Local Whisper model name when transcribing. Default: {DEFAULT_TRANSCRIBE_MODEL}")
    produce_parser.add_argument("--language", default="zh", help="Transcription language when transcribing. Default: zh")
    produce_parser.add_argument("--duration", type=float, help="Render duration override. Defaults to input/source.mp4 duration")
    produce_parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help=f"Frames per second. Default: {DEFAULT_FPS}")
    produce_parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help=f"Render width. Default: {DEFAULT_WIDTH}")
    produce_parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help=f"Render height. Default: {DEFAULT_HEIGHT}")
    produce_parser.add_argument("--duration-tolerance", type=float, default=0.25, help="Allowed source/background duration delta in seconds")
    produce_parser.add_argument("--allow-missing-source-video", action="store_true", help="Allow production without input/source.mp4. This disables source-video sync validation.")
    produce_parser.add_argument("--keep-frames", action="store_true", help="Keep intermediate JPEG frames in output/render_frames")
    produce_parser.set_defaults(func=command_produce)

    validate_parser = subparsers.add_parser("validate", help="Validate project artifacts and rendered background MP4")
    validate_parser.add_argument("--workspace", required=True, help="Project workspace path")
    validate_parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help=f"Expected video width. Default: {DEFAULT_WIDTH}")
    validate_parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help=f"Expected video height. Default: {DEFAULT_HEIGHT}")
    validate_parser.add_argument("--duration-tolerance", type=float, default=0.25, help="Allowed timeline/source and source/background duration delta in seconds")
    validate_parser.add_argument("--require-source-video", action="store_true", help="Fail validation if input/source.mp4 is missing or unreadable")
    validate_parser.add_argument("--require-production-manifest", action="store_true", help="Fail validation if output/production_manifest.json is missing")
    validate_parser.set_defaults(func=command_validate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
