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
ROUTER_SKILL = ROOT / "skills" / "tgravity-work" / "SKILL.md"
GOAL_SKILL = ROOT / "skills" / "tgravity-work-goal" / "SKILL.md"
ASSET_CARDS_SKILL = ROOT / "skills" / "tgravity-work-asset-cards" / "SKILL.md"
PROMPT_OPTIMIZER_SKILL = ROOT / "skills" / "tgravity-work-prompt-optimizer" / "SKILL.md"
PROMPT_ARCHITECT_SKILL = ROOT / "skills" / "tgravity-work-prompt-architect" / "SKILL.md"
PIPELINE = ROOT / "skills" / "tgravity-work-tech-canvas-video" / "scripts" / "tech_canvas_pipeline.py"
VALIDATE_ASSET_CARDS = ROOT / "skills" / "tgravity-work-asset-export" / "scripts" / "validate_asset_cards.py"
ASSET_CARD_FIXTURES = ROOT / "tests" / "fixtures" / "asset-cards"


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


def assert_router_hitl_contract() -> None:
    router_text = ROUTER_SKILL.read_text(encoding="utf-8")
    asset_text = ASSET_CARDS_SKILL.read_text(encoding="utf-8")
    asset_frontmatter = asset_text.split("---", 2)[1]
    forbidden = [
        "决策请求、需要璐璐判断 | `tgravity-work-asset-cards`",
        "or 需要璐璐判断",
    ]
    leaked = [item for item in forbidden if item in router_text or item in asset_frontmatter]
    if leaked:
        raise SystemExit(f"HITL marker is still an asset-card trigger: {leaked}")
    required = [
        "不能单独决定路由",
        "生成决策请求卡",
        "只在当前任务里标记为需要人工判断",
    ]
    missing = [item for item in required if item not in router_text and item not in asset_text]
    if missing:
        raise SystemExit(f"HITL routing contract missing: {missing}")
    print("OK router HITL contract")


def assert_prompt_architect_contract() -> None:
    text = PROMPT_ARCHITECT_SKILL.read_text(encoding="utf-8")
    required = [
        "模式闸门",
        "审核模式",
        "生成模式",
        "置信度闸门",
        "判断标准",
        "架构诊断报告",
        "工作流主干",
        "建议保留的设计",
        "最多输出 5 个漏洞",
        "优化后的提示词框架",
        "不输出不可执行建议",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"prompt architect skill contract missing: {missing}")
    forbidden = ["".join(parts) for parts in [
        ("d", "bs"),
        ("D", "BS"),
        ("dont", "besilent"),
        ("Open", "Montage"),
        ("open", "montage"),
    ]]
    leaked = [item for item in forbidden if item in text]
    if leaked:
        raise SystemExit(f"prompt architect skill contains external reference: {leaked}")
    print("OK prompt architect skill contract")


def assert_prompt_optimizer_contract() -> None:
    text = PROMPT_OPTIMIZER_SKILL.read_text(encoding="utf-8")
    required = [
        "输入闸门",
        "Phase 1：质疑需求",
        "Phase 2：删减",
        "Phase 3：简化",
        "Phase 4：加速",
        "Phase 5：模板化",
        "Phase 6：精简报告",
        "不新增原提示词没有的能力",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"prompt optimizer skill contract missing: {missing}")
    forbidden = ["".join(parts) for parts in [
        ("d", "bs"),
        ("D", "BS"),
        ("dont", "besilent"),
        ("Open", "Montage"),
        ("open", "montage"),
        ("特", "斯拉"),
        ("马", "斯克"),
    ]]
    leaked = [item for item in forbidden if item in text]
    if leaked:
        raise SystemExit(f"prompt optimizer skill contains external reference: {leaked}")
    print("OK prompt optimizer skill contract")


def assert_asset_card_fixture_validation() -> None:
    result = run([sys.executable, str(VALIDATE_ASSET_CARDS), "--source", str(ASSET_CARD_FIXTURES)])
    if "checked=1" not in result.stdout or "with_missing_fields=0" not in result.stdout:
        raise SystemExit(f"asset card fixture validation did not scan the expected fixture:\n{result.stdout}")
    print("OK asset card fixture validation")


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
    assert_router_hitl_contract()
    assert_prompt_optimizer_contract()
    assert_prompt_architect_contract()
    assert_asset_card_fixture_validation()
    assert_srt_plan_smoke()
    if args.full or not args.quick:
        assert_produce_validate_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
