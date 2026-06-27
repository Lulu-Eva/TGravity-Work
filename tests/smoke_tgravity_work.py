#!/usr/bin/env python3
"""Semantic smoke tests for the TGravity Work skill package."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
ROUTER_SKILL = ROOT / "skills" / "tgravity-work" / "SKILL.md"
ONBOARDING_SKILL = ROOT / "skills" / "tgravity-work-onboarding" / "SKILL.md"
GOAL_SKILL = ROOT / "skills" / "tgravity-work-goal" / "SKILL.md"
ASSET_CARDS_SKILL = ROOT / "skills" / "tgravity-work-asset-cards" / "SKILL.md"
MCN_ROUTER_SKILL = ROOT / "skills" / "tgravity-work-mcn" / "SKILL.md"
PROMPT_OPTIMIZER_SKILL = ROOT / "skills" / "tgravity-work-prompt-optimizer" / "SKILL.md"
PROMPT_ARCHITECT_SKILL = ROOT / "skills" / "tgravity-work-prompt-architect" / "SKILL.md"
PIPELINE = ROOT / "skills" / "tgravity-work-tech-canvas-video" / "scripts" / "tech_canvas_pipeline.py"
VIDEO_PIPELINE = ROOT / "skills" / "tgravity-work-video-indexer" / "scripts" / "video_pipeline.py"
SEARCH_SCRIPT = ROOT / "skills" / "tgravity-work-search" / "scripts" / "dual_search.py"
INVOICE_SCRIPT = ROOT / "skills" / "tgravity-work-invoice-reimbursement" / "scripts" / "invoice_reimbursement.py"
VALIDATE_ASSET_CARDS = ROOT / "skills" / "tgravity-work-asset-export" / "scripts" / "validate_asset_cards.py"
EXPORT_ASSETS = ROOT / "skills" / "tgravity-work-asset-export" / "scripts" / "export_assets.py"
MCN_INDEX = ROOT / "skills" / "tgravity-work-mcn-index" / "scripts" / "mcn_index.py"
MCN_RENDER_SHARED = ROOT / "shared" / "mcn" / "render_mcn_asset.py"
MCN_SYNC_SHARED = ROOT / "shared" / "mcn" / "sync_shared_resources.py"
MCN_RENDER = ROOT / "skills" / "tgravity-work-mcn-creator-profile" / "scripts" / "render_mcn_asset.py"
ASSET_CARD_FIXTURES = ROOT / "tests" / "fixtures" / "asset-cards"
MCN_FIXTURES = ROOT / "tests" / "fixtures" / "mcn-assets"


def yaml_frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SystemExit(f"missing YAML frontmatter: {path.relative_to(ROOT)}")
    return parts[1]


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        print("FAILED:", " ".join(command))
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)
    return result


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise SystemExit(f"cannot load module: {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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


def assert_mcn_skill_contract() -> None:
    router_text = ROUTER_SKILL.read_text(encoding="utf-8")
    mcn_text = MCN_ROUTER_SKILL.read_text(encoding="utf-8")
    contract_text = (ROOT / "shared" / "mcn" / "asset-contract.md").read_text(encoding="utf-8")
    required_router = [
        "tgravity-work-mcn",
        "达人档案",
        "品牌档案",
        "逆向brief",
        "合作记录",
        "MCN关系索引",
    ]
    missing_router = [item for item in required_router if item not in router_text and item not in mcn_text]
    if missing_router:
        raise SystemExit(f"MCN router contract missing: {missing_router}")
    router_frontmatter = yaml_frontmatter(ROUTER_SKILL)
    mcn_frontmatter = yaml_frontmatter(MCN_ROUTER_SKILL)
    main_router_forbidden = [
        "目标提示词",
        "提示词优化",
        "提示词架构",
        "开工前检查",
        "TGravity日报",
        "导出TGravity资产",
        "达人档案",
        "品牌档案",
        "逆向brief",
        "合作记录",
        "品牌达人互链",
        "MCN关系索引",
        "搜索技能",
        "视频分析技能",
        "科技画布",
        "发票报销",
        "大项目行动前审视",
        "项目文件夹整理",
        "生成 AGENTS.md",
    ]
    leaked_main_triggers = [item for item in main_router_forbidden if item in router_frontmatter]
    if leaked_main_triggers:
        raise SystemExit(f"main router frontmatter still duplicates child triggers: {leaked_main_triggers}")
    mcn_router_forbidden = [
        "达人档案",
        "品牌档案",
        "品牌方档案",
        "逆向brief",
        "商单brief",
        "合作记录",
        "合作历史",
        "品牌达人互链",
        "达人品牌互链",
        "MCN关系索引",
        "重建MCN索引",
    ]
    leaked_mcn_triggers = [item for item in mcn_router_forbidden if item in mcn_frontmatter]
    if leaked_mcn_triggers:
        raise SystemExit(f"MCN router frontmatter still duplicates leaf triggers: {leaked_mcn_triggers}")
    required_contract = [
        "mcn_creator_profile",
        "mcn_brand_profile",
        "mcn_reverse_brief",
        "mcn_collaboration",
        "YAML frontmatter is the source of truth",
        "A creator-brand cooperation is not a sentence",
        "Executed creator-brand cooperation is sourced only from `mcn_collaboration` records",
        "`合作过` is a generated reading label only",
        "not source data",
        "asset skeleton",
        "CRT-YYYYMMDD-001",
        "relationships:",
    ]
    missing_contract = [item for item in required_contract if item not in contract_text]
    if missing_contract:
        raise SystemExit(f"MCN shared contract missing: {missing_contract}")
    mcn_skill_dirs = [
        ROOT / "skills" / "tgravity-work-mcn-creator-profile",
        ROOT / "skills" / "tgravity-work-mcn-brand-profile",
        ROOT / "skills" / "tgravity-work-mcn-brief-builder",
        ROOT / "skills" / "tgravity-work-mcn-collaboration",
        ROOT / "skills" / "tgravity-work-mcn-index",
    ]
    missing_local_contract = [
        str(path.relative_to(ROOT))
        for path in mcn_skill_dirs
        if not (path / "references" / "asset-contract.md").exists()
    ]
    if missing_local_contract:
        raise SystemExit(f"MCN child skill is not self-contained: {missing_local_contract}")
    shared_contract = (ROOT / "shared" / "mcn" / "asset-contract.md").read_text(encoding="utf-8")
    drifted_contracts = [
        str((path / "references" / "asset-contract.md").relative_to(ROOT))
        for path in mcn_skill_dirs
        if (path / "references" / "asset-contract.md").read_text(encoding="utf-8") != shared_contract
    ]
    if drifted_contracts:
        raise SystemExit(f"MCN child skill contract drifted from shared source: {drifted_contracts}")
    render_skill_dirs = [
        ROOT / "skills" / "tgravity-work-mcn-creator-profile",
        ROOT / "skills" / "tgravity-work-mcn-brand-profile",
        ROOT / "skills" / "tgravity-work-mcn-brief-builder",
        ROOT / "skills" / "tgravity-work-mcn-collaboration",
    ]
    missing_render_scripts = [
        str(path.relative_to(ROOT))
        for path in render_skill_dirs
        if not (path / "scripts" / "render_mcn_asset.py").exists()
    ]
    if missing_render_scripts:
        raise SystemExit(f"MCN child skill missing deterministic render script: {missing_render_scripts}")
    shared_render = MCN_RENDER_SHARED.read_text(encoding="utf-8")
    drifted_render_scripts = [
        str((path / "scripts" / "render_mcn_asset.py").relative_to(ROOT))
        for path in render_skill_dirs
        if (path / "scripts" / "render_mcn_asset.py").read_text(encoding="utf-8") != shared_render
    ]
    if drifted_render_scripts:
        raise SystemExit(f"MCN child render script drifted from shared source: {drifted_render_scripts}")
    result = run([sys.executable, str(MCN_SYNC_SHARED), "--check"])
    if "checked=9" not in result.stdout or "updated_count=0" not in result.stdout:
        raise SystemExit(f"MCN shared sync check returned unexpected output:\n{result.stdout}")
    print("OK MCN skill contract")


def assert_onboarding_contract() -> None:
    text = ONBOARDING_SKILL.read_text(encoding="utf-8")
    required = [
        "tgravity-work-mcn",
        "tgravity-work-mcn-creator-profile",
        "tgravity-work-mcn-brand-profile",
        "tgravity-work-mcn-brief-builder",
        "tgravity-work-mcn-collaboration",
        "tgravity-work-mcn-index",
        "MCN 资产：达人、品牌、Brief、合作记录和互链",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"onboarding MCN contract missing: {missing}")
    print("OK onboarding contract")


def copy_mcn_fixture(workspace: Path) -> Path:
    mcn_root = workspace / "tgravity-work-data" / "mcn"
    mcn_root.mkdir(parents=True, exist_ok=True)
    for dirname in ("creators", "brands", "briefs", "collaborations"):
        shutil.copytree(MCN_FIXTURES / dirname, mcn_root / dirname)
    return mcn_root


def assert_mcn_index_smoke() -> None:
    with tempfile.TemporaryDirectory(prefix="tgravity-mcn-smoke-") as tmp:
        workspace = Path(tmp)
        mcn_root = copy_mcn_fixture(workspace)
        source_files = sorted(mcn_root.glob("*/*.md"))
        before = {path.relative_to(mcn_root).as_posix(): path.read_text(encoding="utf-8") for path in source_files}
        result = run([sys.executable, str(MCN_INDEX), "--root", str(workspace), "--fill-links"])
        expected = [
            "asset_count=4",
            "relation_count=4",
            "collaboration_count=1",
            "brand_creator_rows=1",
            "duplicate_ids=0",
            "missing_targets=0",
            "required_problems=0",
            "changed_link_files=3",
            "fill_links_dry_run=False",
            "fill_links_backup=True",
        ]
        missing = [item for item in expected if item not in result.stdout]
        if missing:
            raise SystemExit(f"MCN index smoke missing output: {missing}\n{result.stdout}")
        backup_root_line = next((line for line in result.stdout.splitlines() if line.startswith("backup_root=")), "")
        backup_root = Path(backup_root_line.split("=", 1)[1])
        if not backup_root.exists():
            raise SystemExit(f"MCN fill-links did not create a backup root:\n{result.stdout}")
        expected_backups = [
            "creators/CRT-20260627-001_测试达人.md",
            "brands/BRD-20260627-001_测试品牌.md",
            "collaborations/COL-20260627-001_测试品牌-测试达人-测试项目.md",
        ]
        for rel in expected_backups:
            backup = backup_root / rel
            if not backup.exists():
                raise SystemExit(f"MCN fill-links backup missing: {rel}")
            if backup.read_text(encoding="utf-8") != before[rel]:
                raise SystemExit(f"MCN fill-links backup does not preserve original content: {rel}")
        index_root = workspace / "tgravity-work-data" / "mcn" / "indexes"
        required_files = [
            "关系索引.csv",
            "关系总览.md",
            "品牌-达人矩阵.csv",
            "达人合作历史.csv",
            "悬空关系检查.md",
        ]
        for name in required_files:
            if not (index_root / name).exists():
                raise SystemExit(f"MCN index file missing: {name}")
        matrix = (index_root / "品牌-达人矩阵.csv").read_text(encoding="utf-8")
        if "BRD-20260627-001" not in matrix or "CRT-20260627-001" not in matrix:
            raise SystemExit("MCN brand-creator matrix missing fixture IDs")
        brand_file = workspace / "tgravity-work-data" / "mcn" / "brands" / "BRD-20260627-001_测试品牌.md"
        creator_file = workspace / "tgravity-work-data" / "mcn" / "creators" / "CRT-20260627-001_测试达人.md"
        brand_text = brand_file.read_text(encoding="utf-8")
        creator_text = creator_file.read_text(encoding="utf-8")
        if (
            "## 合作过的达人" not in brand_text
            or "[[CRT-20260627-001_测试达人]]" not in brand_text
            or "[[COL-20260627-001_测试品牌-测试达人-测试项目]]" not in brand_text
        ):
            raise SystemExit("MCN fill-links did not add brand -> creator collaboration backlink")
        if (
            "## 合作过的品牌" not in creator_text
            or "[[BRD-20260627-001_测试品牌]]" not in creator_text
            or "[[COL-20260627-001_测试品牌-测试达人-测试项目]]" not in creator_text
        ):
            raise SystemExit("MCN fill-links did not add creator -> brand collaboration backlink")
        if "[[BRF-20260627-001_测试品牌-测试产品-投放需求]]" not in creator_text:
            raise SystemExit("MCN fill-links did not add creator related brief link inside the 关联资产 section")
        second = run([sys.executable, str(MCN_INDEX), "--root", str(workspace), "--fill-links"])
        if "changed_link_files=0" not in second.stdout or "backup_root=" not in second.stdout:
            raise SystemExit(f"MCN fill-links is not idempotent on second run:\n{second.stdout}")
    print("OK MCN index smoke")


def assert_mcn_index_dry_run_smoke() -> None:
    with tempfile.TemporaryDirectory(prefix="tgravity-mcn-dry-run-") as tmp:
        workspace = Path(tmp)
        mcn_root = copy_mcn_fixture(workspace)
        tracked_files = sorted(mcn_root.glob("*/*.md"))
        before = {path.relative_to(mcn_root).as_posix(): path.read_text(encoding="utf-8") for path in tracked_files}
        result = run([sys.executable, str(MCN_INDEX), "--root", str(workspace), "--fill-links", "--dry-run"])
        expected = [
            "changed_link_files=3",
            "fill_links_dry_run=True",
            "fill_links_backup=True",
            "backup_root=",
        ]
        missing = [item for item in expected if item not in result.stdout]
        if missing:
            raise SystemExit(f"MCN dry-run smoke missing output: {missing}\n{result.stdout}")
        for path in tracked_files:
            rel = path.relative_to(mcn_root).as_posix()
            if path.read_text(encoding="utf-8") != before[rel]:
                raise SystemExit(f"MCN dry-run modified source Markdown: {rel}")
        if (mcn_root / ".backups").exists():
            raise SystemExit("MCN dry-run should not create source Markdown backups")
        index_root = mcn_root / "indexes"
        if not (index_root / "关系索引.csv").exists():
            raise SystemExit("MCN dry-run should still rebuild index files")
    print("OK MCN index dry-run smoke")


def assert_mcn_invalid_asset_smoke() -> None:
    with tempfile.TemporaryDirectory(prefix="tgravity-mcn-invalid-") as tmp:
        workspace = Path(tmp)
        mcn_root = copy_mcn_fixture(workspace)
        broken = mcn_root / "creators" / "broken_creator.md"
        broken.write_text(
            "---\n"
            "tgravity_asset: true\n"
            "asset_type: mcn_creator_profile\n"
            "title: Broken Creator\n"
            "---\n"
            "\n"
            "# Broken Creator\n",
            encoding="utf-8",
        )
        result = run([sys.executable, str(MCN_INDEX), "--root", str(workspace)])
        if "required_problems=1" not in result.stdout:
            raise SystemExit(f"MCN invalid asset was not reported:\n{result.stdout}")
        problems = (mcn_root / "indexes" / "悬空关系检查.md").read_text(encoding="utf-8")
        if "broken_creator.md: missing asset_id" not in problems:
            raise SystemExit("MCN invalid asset report missing broken_creator.md")
    print("OK MCN invalid asset smoke")


def assert_mcn_generated_only_relationship_smoke() -> None:
    with tempfile.TemporaryDirectory(prefix="tgravity-mcn-generated-only-") as tmp:
        workspace = Path(tmp)
        mcn_root = copy_mcn_fixture(workspace)
        creator = mcn_root / "creators" / "CRT-20260627-001_测试达人.md"
        text = creator.read_text(encoding="utf-8")
        text = text.replace(
            "relationships:\n"
            "  - type: 适配\n",
            "relationships:\n"
            "  - type: 合作过\n"
            "    target: BRD-20260627-001\n"
            "    evidence: bad_test\n"
            "    note: should be generated-only\n"
            "  - type: 适配\n",
        )
        creator.write_text(text, encoding="utf-8")
        result = run([sys.executable, str(MCN_INDEX), "--root", str(workspace)])
        if "required_problems=1" not in result.stdout:
            raise SystemExit(f"MCN generated-only relationship was not reported:\n{result.stdout}")
        problems = (mcn_root / "indexes" / "悬空关系检查.md").read_text(encoding="utf-8")
        if "relationship type 合作过 is generated-only" not in problems:
            raise SystemExit("MCN generated-only relationship report missing 合作过 problem")
    print("OK MCN generated-only relationship smoke")


def assert_mcn_render_smoke() -> None:
    with tempfile.TemporaryDirectory(prefix="tgravity-mcn-render-") as tmp:
        workspace = Path(tmp)
        output_dir = workspace / "tgravity-work-data" / "mcn" / "creators"
        command = [
            sys.executable,
            str(MCN_RENDER),
            "--template",
            str(ROOT / "skills" / "tgravity-work-mcn-creator-profile" / "assets" / "templates" / "mcn-creator-profile.md"),
            "--output-dir",
            str(output_dir),
            "--asset-id",
            "CRT-20260627-099",
            "--title",
            "测试: 达人/一号",
            "--owner",
            "测试维护人",
            "--source",
            "用户口述",
            "--date",
            "2026-06-27",
        ]
        result = run(command)
        if "created=" not in result.stdout:
            raise SystemExit(f"MCN render script did not report created path:\n{result.stdout}")
        files = list(output_dir.glob("CRT-20260627-099_*.md"))
        if len(files) != 1:
            raise SystemExit(f"MCN render script created unexpected files: {files}")
        text = files[0].read_text(encoding="utf-8")
        required = [
            "asset_id: CRT-20260627-099",
            'title: "测试: 达人/一号"',
            'name: "测试: 达人/一号"',
            "owner: 测试维护人",
            "source: 用户口述",
            "created_at: 2026-06-27",
            "# 测试: 达人/一号",
        ]
        missing = [item for item in required if item not in text]
        if missing:
            raise SystemExit(f"MCN render output missing expected fields: {missing}")
        duplicate = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if duplicate.returncode == 0 or "refusing to overwrite existing file" not in (duplicate.stdout + duplicate.stderr):
            raise SystemExit("MCN render script did not refuse duplicate output")
        bad_target = subprocess.run(
            [
                sys.executable,
                str(MCN_RENDER),
                "--template",
                str(ROOT / "skills" / "tgravity-work-mcn-creator-profile" / "assets" / "templates" / "mcn-creator-profile.md"),
                "--output-dir",
                str(ROOT / "skills" / "tgravity-work-mcn-creator-profile" / "tgravity-work-data" / "mcn" / "creators"),
                "--asset-id",
                "CRT-20260627-100",
                "--title",
                "禁止写入Skill包",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if bad_target.returncode == 0 or "output-dir points inside the skill package" not in (bad_target.stdout + bad_target.stderr):
            raise SystemExit("MCN render script did not refuse output inside the skill package")
    print("OK MCN render smoke")


def assert_mcn_export_smoke() -> None:
    with tempfile.TemporaryDirectory(prefix="tgravity-mcn-export-") as tmp:
        workspace = Path(tmp)
        mcn_root = copy_mcn_fixture(workspace)
        output = workspace / "exports"
        result = run([sys.executable, str(EXPORT_ASSETS), "--source", str(mcn_root), "--output", str(output)])
        if "asset_count=4" not in result.stdout:
            raise SystemExit(f"MCN export did not export expected assets:\n{result.stdout}")
        export_dir_line = next(line for line in result.stdout.splitlines() if line.startswith("export_dir="))
        export_dir = Path(export_dir_line.split("=", 1)[1])
        for rel in [
            "mcn/creators/CRT-20260627-001_测试达人.md",
            "mcn/brands/BRD-20260627-001_测试品牌.md",
            "mcn/briefs/BRF-20260627-001_测试品牌-测试产品-投放需求.md",
            "mcn/collaborations/COL-20260627-001_测试品牌-测试达人-测试项目.md",
        ]:
            if not (export_dir / rel).exists():
                raise SystemExit(f"MCN exported file missing: {rel}")
    print("OK MCN export smoke")


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


def assert_script_failure_handling() -> None:
    search = load_module(SEARCH_SCRIPT, "tgravity_search_smoke")
    data, failure = search.response_json("Perplexity", SimpleNamespace(status_code=200, json=lambda: (_ for _ in ()).throw(ValueError("html"))))
    if data is not None or not failure or failure.get("failure_type") != "invalid_json":
        raise SystemExit(f"search invalid JSON was not classified correctly: {failure}")

    video = load_module(VIDEO_PIPELINE, "tgravity_video_smoke")
    code, _, err = video.run_capture([sys.executable, "-c", "import time; time.sleep(2)"], timeout=1)
    if code != 124 or "timeout after 1s" not in err:
        raise SystemExit(f"video run_capture timeout did not return per-file failure: code={code}, err={err}")

    invoice = load_module(INVOICE_SCRIPT, "tgravity_invoice_smoke")
    with tempfile.TemporaryDirectory(prefix="tgravity-invoice-failure-") as tmp:
        pdf = Path(tmp) / "broken.pdf"
        pdf.write_bytes(b"%PDF broken")

        def broken_extract(_: str) -> str:
            raise ValueError("broken pdf")

        try:
            invoice.parse_pdf(pdf, broken_extract, "测试公司")
        except RuntimeError as exc:
            if "PDF 文本抽取失败" not in str(exc):
                raise SystemExit(f"invoice parse_pdf wrapped the wrong error: {exc}")
        else:
            raise SystemExit("invoice parse_pdf did not surface extraction failure")
    print("OK script failure handling")


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
        html = (workspace / "hyperframes" / "index.html").read_text(encoding="utf-8")
        forbidden_network_markers = ["https://", "http://", "cdn.jsdelivr", "gsap.min.js"]
        leaked = [marker for marker in forbidden_network_markers if marker in html]
        if leaked:
            raise SystemExit(f"tech canvas HTML contains external network dependency: {leaked}")
        manifest = json.loads((workspace / "output" / "production_manifest.json").read_text(encoding="utf-8"))
        if "html_canvas" not in manifest.get("outputs", {}):
            raise SystemExit("production manifest missing html_canvas output")
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
    assert_mcn_skill_contract()
    assert_onboarding_contract()
    assert_mcn_index_smoke()
    assert_mcn_index_dry_run_smoke()
    assert_mcn_invalid_asset_smoke()
    assert_mcn_generated_only_relationship_smoke()
    assert_mcn_render_smoke()
    assert_mcn_export_smoke()
    assert_srt_plan_smoke()
    assert_script_failure_handling()
    if args.full or not args.quick:
        assert_produce_validate_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
