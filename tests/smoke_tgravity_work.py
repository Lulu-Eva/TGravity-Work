#!/usr/bin/env python3
"""Semantic smoke tests for the TGravity Work skill package."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOAL_SKILL = ROOT / "skills" / "tgravity-work-goal" / "SKILL.md"
PIPELINE = ROOT / "skills" / "tgravity-work-tech-canvas-video" / "scripts" / "tech_canvas_pipeline.py"


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        print("FAILED:", " ".join(command))
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)
    return result


def assert_goal_skill_contract() -> None:
    text = GOAL_SKILL.read_text(encoding="utf-8")
    required = [
        "输入分类闸门",
        "Agent 可交付性检查",
        "低清晰度规则",
        "目标提示词结构",
        "不输出完整执行计划",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"goal skill contract missing: {missing}")
    print("OK goal skill contract")


def write_srt(workspace: Path) -> None:
    input_dir = workspace / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "script.srt").write_text(
        "1\n"
        "00:00:00,000 --> 00:00:01,000\n"
        "Open the system map.\n\n"
        "2\n"
        "00:00:01,000 --> 00:00:02,000\n"
        "Show the delivery path.\n",
        encoding="utf-8",
    )


def make_source_video(workspace: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg missing; cannot run full produce smoke")
    input_dir = workspace / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=180x320:rate=6:duration=2",
            "-pix_fmt",
            "yuv420p",
            str(input_dir / "source.mp4"),
        ]
    )


def assert_srt_plan_smoke() -> None:
    with tempfile.TemporaryDirectory(prefix="tgravity-srt-smoke-") as tmp:
        workspace = Path(tmp)
        write_srt(workspace)
        run([sys.executable, str(PIPELINE), "plan", "--workspace", str(workspace)])
        segments = json.loads((workspace / "analysis" / "script_segments.json").read_text(encoding="utf-8"))
        timeline = json.loads((workspace / "analysis" / "timeline.json").read_text(encoding="utf-8"))
        assert segments["source"] == "input/script.srt"
        assert timeline["source"] == "input/script.srt"
        assert timeline["timing_source"] == "timestamped_script"
        assert len(timeline["clips"]) == 2
    print("OK SRT plan smoke")


def local_render_available() -> bool:
    result = run([sys.executable, str(PIPELINE), "check", "--json"])
    payload = json.loads(result.stdout)
    return bool(payload.get("local_render"))


def assert_produce_validate_smoke() -> None:
    if not local_render_available():
        print("SKIP full produce smoke: local_render=false")
        return
    with tempfile.TemporaryDirectory(prefix="tgravity-produce-smoke-") as tmp:
        workspace = Path(tmp)
        write_srt(workspace)
        make_source_video(workspace)
        run(
            [
                sys.executable,
                str(PIPELINE),
                "produce",
                "--workspace",
                str(workspace),
                "--style",
                "minimal-tech",
                "--width",
                "180",
                "--height",
                "320",
                "--fps",
                "6",
                "--duration-tolerance",
                "0.5",
            ]
        )
        report = json.loads((workspace / "output" / "validation_report.json").read_text(encoding="utf-8"))
        if report.get("passed") is not True:
            failed = [item for item in report.get("items", []) if not item.get("passed")]
            raise SystemExit(f"produce validation failed: {failed}")
    print("OK produce/validate smoke")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TGravity Work semantic smoke tests")
    parser.add_argument("--quick", action="store_true", help="Run contract and SRT planning tests only")
    parser.add_argument("--full", action="store_true", help="Also run a tiny produce -> validate smoke test")
    args = parser.parse_args()

    assert_goal_skill_contract()
    assert_srt_plan_smoke()
    if args.full or not args.quick:
        assert_produce_validate_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
