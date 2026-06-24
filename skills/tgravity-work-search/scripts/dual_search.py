#!/usr/bin/env python3
"""TGravity Work Search: Perplexity + Tavily dual-engine search."""

from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import stat
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Any


CONFIG_DIR = Path(os.environ.get("TGRAVITY_WORK_SEARCH_HOME", Path.home() / ".config" / "tgravity-work-search"))
CONFIG_FILE = CONFIG_DIR / "config.json"
VERSION = "0.1.0"
REQUESTS_INSTALL_HINT = "missing dependency: requests. Install with: python3 -m pip install --user requests"


def load_requests(engine: str) -> tuple[Any | None, dict[str, Any] | None]:
    warnings.filterwarnings(
        "ignore",
        message=r"urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
    )
    try:
        import requests

        return requests, None
    except ImportError:
        return None, fail(engine, REQUESTS_INSTALL_HINT, "dependency")


def load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Config file is not valid JSON: {CONFIG_FILE}\n{exc}") from exc


def resolve_key(name: str) -> tuple[str | None, str]:
    env_value = os.environ.get(name, "").strip()
    if env_value:
        return env_value, f"env:{name}"

    data = load_config()
    file_value = str(data.get(name) or "").strip()
    if file_value:
        return file_value, str(CONFIG_FILE)

    return None, "missing"


def key_status() -> dict[str, dict[str, Any]]:
    status: dict[str, dict[str, Any]] = {}
    for name in ("PERPLEXITY_API_KEY", "TAVILY_API_KEY"):
        value, source = resolve_key(name)
        status[name] = {"present": bool(value), "source": source}
    return status


def save_keys(keys: dict[str, str]) -> None:
    existing = load_config()
    payload = {**existing}
    for name, value in keys.items():
        value = value.strip()
        if not value:
            continue
        if len(value) < 20:
            raise SystemExit(f"{name} looks too short; nothing saved.")
        payload[name] = value

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, stat.S_IRWXU)
    tmp_file = CONFIG_FILE.with_suffix(".json.tmp")
    tmp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp_file, stat.S_IRUSR | stat.S_IWUSR)
    tmp_file.replace(CONFIG_FILE)
    os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)


def status() -> int:
    current = key_status()
    for name in ("PERPLEXITY_API_KEY", "TAVILY_API_KEY"):
        item = current[name]
        state = "present" if item["present"] else "missing"
        print(f"{name}={state}")
        if item["present"]:
            print(f"{name}_source={item['source']}")
    print(f"config_path={CONFIG_FILE}")

    present_count = sum(1 for item in current.values() if item["present"])
    if present_count == 2:
        print("status=configured")
        return 0
    if present_count == 1:
        print("status=partial")
        return 0
    print("status=missing")
    return 1


def init_config() -> int:
    current = key_status()
    keys_to_save: dict[str, str] = {}

    for name in ("PERPLEXITY_API_KEY", "TAVILY_API_KEY"):
        env_value = os.environ.get(name, "").strip()
        if env_value:
            answer = input(f"Found {name} in environment. Save it to local config? [y/N] ").strip().lower()
            if answer == "y":
                keys_to_save[name] = env_value
            continue
        if current[name]["present"]:
            continue
        keys_to_save[name] = getpass.getpass(f"Paste {name}: ").strip()

    if not keys_to_save:
        print("No new keys saved.")
        return status()

    save_keys(keys_to_save)
    print(f"Saved API keys to {CONFIG_FILE}")
    print("Keys were not printed and must not be committed to Git.")
    return status()


def init_from_stdin() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"stdin is not valid JSON: {exc}") from exc

    aliases = {
        "PERPLEXITY_API_KEY": ("PERPLEXITY_API_KEY", "perplexity_api_key", "perplexity", "pplx"),
        "TAVILY_API_KEY": ("TAVILY_API_KEY", "tavily_api_key", "tavily"),
    }
    keys_to_save: dict[str, str] = {}
    for name, keys in aliases.items():
        value = ""
        for key in keys:
            value = str(payload.get(key) or "").strip()
            if value:
                break
        if value:
            keys_to_save[name] = value

    if not keys_to_save:
        raise SystemExit("stdin JSON did not contain PERPLEXITY_API_KEY or TAVILY_API_KEY")

    save_keys(keys_to_save)
    print(f"Saved API keys to {CONFIG_FILE}")
    print("Keys were not printed and must not be committed to Git.")
    return status()


def choose_model(query: str, explicit: str | None) -> str:
    if explicit:
        return explicit

    q = query.lower()
    if any(token in q for token in ["深度研究", "完整报告", "deep research"]):
        return "sonar-deep-research"
    if any(token in q for token in ["为什么", "比较", "分析", "vs", "compare", "analysis", "why"]):
        return "sonar-reasoning-pro"
    if any(token in q for token in ["最新", "是什么", "有没有", "latest", "what is", "is there"]):
        return "sonar"
    return "sonar-pro"


def choose_recency(query: str, explicit: str) -> str:
    if explicit != "auto":
        return explicit

    q = query.lower()
    if any(token in q for token in ["今天", "刚刚", "最新", "today", "latest", "recent", "breaking"]):
        return "day"
    if any(token in q for token in ["本周", "这周", "week", "weekly"]):
        return "week"
    return "month"


def normalize_perplexity_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""

    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part)
    return str(content)


def classify_http_failure(engine: str, status_code: int, body: str) -> dict[str, str]:
    lower = body.lower()
    if status_code in (401, 403):
        return {"type": "auth", "message": f"{engine} API key 无效、过期或权限不足"}
    if status_code == 402 or any(token in lower for token in ["quota", "credit", "billing", "payment", "insufficient balance"]):
        return {"type": "billing", "message": f"{engine} 可能没有余额、积分或账单额度"}
    if status_code == 429:
        return {"type": "rate_limit", "message": f"{engine} 触发限流或额度限制"}
    if 500 <= status_code < 600:
        return {"type": "provider", "message": f"{engine} 服务端错误"}
    return {"type": "unknown", "message": "搜索失败"}


def classify_exception(engine: str, exc: Exception) -> dict[str, str]:
    text = repr(exc).lower()
    if "timeout" in text or "timed out" in text:
        return {"type": "timeout", "message": f"{engine} 网络超时"}
    if "connection" in text or "network" in text or "name resolution" in text:
        return {"type": "network", "message": f"{engine} 网络连接失败"}
    return {"type": "unknown", "message": "搜索失败"}


def fail(engine: str, error: str, failure_type: str = "unknown", status_code: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"engine": engine, "ok": False, "error": error, "failure_type": failure_type}
    if status_code is not None:
        result["status_code"] = status_code
    return result


def perplexity_search(query: str, model: str, recency: str, timeout: int) -> dict[str, Any]:
    api_key, source = resolve_key("PERPLEXITY_API_KEY")
    if not api_key:
        return fail("perplexity", "missing PERPLEXITY_API_KEY", "missing_key")

    requests, dependency_failure = load_requests("perplexity")
    if dependency_failure:
        return dependency_failure

    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"tgravity-work-search/{VERSION}",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": query}],
                "web_search_options": {"search_recency_filter": recency},
            },
            timeout=timeout,
        )
    except Exception as exc:
        info = classify_exception("Perplexity", exc)
        return fail("perplexity", info["message"], info["type"])

    if resp.status_code != 200:
        info = classify_http_failure("Perplexity", resp.status_code, resp.text[:1000])
        return fail("perplexity", info["message"], info["type"], resp.status_code)

    data = resp.json()
    return {
        "engine": "perplexity",
        "ok": True,
        "model": model,
        "recency": recency,
        "key_source": source,
        "content": normalize_perplexity_content(data),
    }


def tavily_search(query: str, search_depth: str, max_results: int, timeout: int) -> dict[str, Any]:
    api_key, source = resolve_key("TAVILY_API_KEY")
    if not api_key:
        return fail("tavily", "missing TAVILY_API_KEY", "missing_key")

    requests, dependency_failure = load_requests("tavily")
    if dependency_failure:
        return dependency_failure

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json", "User-Agent": f"tgravity-work-search/{VERSION}"},
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_raw_content": False,
                "include_answer": True,
            },
            timeout=timeout,
        )
    except Exception as exc:
        info = classify_exception("Tavily", exc)
        return fail("tavily", info["message"], info["type"])

    if resp.status_code != 200:
        info = classify_http_failure("Tavily", resp.status_code, resp.text[:1000])
        return fail("tavily", info["message"], info["type"], resp.status_code)

    data = resp.json()
    return {
        "engine": "tavily",
        "ok": True,
        "key_source": source,
        "answer": data.get("answer", ""),
        "results": data.get("results", []),
    }


def tavily_markdown(result: dict[str, Any]) -> str:
    lines = []
    answer = (result.get("answer") or "").strip()
    if answer:
        lines.append(answer)
        lines.append("")

    hits = result.get("results") or []
    if hits:
        lines.append("来源：")
        for item in hits:
            title = item.get("title") or item.get("url") or "Untitled"
            url = item.get("url") or ""
            snippet = (item.get("content") or "").strip()
            lines.append(f"- {title}")
            if url:
                lines.append(f"  {url}")
            if snippet:
                lines.append(f"  {snippet[:220]}")
    return "\n".join(lines).strip()


def engine_failure_line(result: dict[str, Any]) -> str:
    if result.get("ok"):
        return ""
    engine = "Perplexity" if result.get("engine") == "perplexity" else "Tavily"
    failure_type = result.get("failure_type") or "unknown"
    error = result.get("error") or "搜索失败"
    if failure_type == "unknown":
        return f"- {engine}: 搜索失败"
    return f"- {engine}: {error}"


def synthesize_conclusion(perplexity: dict[str, Any], tavily: dict[str, Any]) -> str:
    if perplexity.get("ok") and tavily.get("ok"):
        return "Perplexity 适合直接读结论，Tavily 适合回看来源；两边一起看时，先抓判断，再核链接。"
    if perplexity.get("ok"):
        return "Tavily 未成功返回；本次已自动使用 Perplexity 结果继续。"
    if tavily.get("ok"):
        return "Perplexity 未成功返回；本次已自动使用 Tavily 结果继续。"
    return "两个搜索引擎都没有成功返回，本次搜索技能失效。"


def to_markdown(query: str, perplexity: dict[str, Any], tavily: dict[str, Any]) -> str:
    parts = []
    parts.append(f"# 搜索主题\n\n{query}")
    parts.append("")

    failures = [line for line in [engine_failure_line(perplexity), engine_failure_line(tavily)] if line]
    if failures:
        parts.append("## 搜索状态")
        parts.extend(failures)
        parts.append("")

    parts.append("## Perplexity 搜索结果（综合推理）")
    if perplexity.get("ok"):
        parts.append(f"[模型：{perplexity.get('model', 'unknown')}]")
        parts.append("")
        parts.append((perplexity.get("content") or "").strip() or "(空结果)")
    else:
        parts.append("未返回可用结果。")

    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## Tavily 搜索结果（结构化来源）")
    if tavily.get("ok"):
        parts.append(tavily_markdown(tavily) or "(空结果)")
    else:
        parts.append("未返回可用结果。")

    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## 综合结论")
    parts.append("")
    parts.append(synthesize_conclusion(perplexity, tavily))
    return "\n".join(parts).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TGravity Work Search through Perplexity + Tavily.")
    parser.add_argument("--init", action="store_true", help="Prompt for Perplexity and Tavily API keys and save them locally.")
    parser.add_argument("--init-stdin", action="store_true", help="Read API keys from stdin JSON and save them locally without printing them.")
    parser.add_argument("--status", action="store_true", help="Check whether Perplexity and Tavily API keys are configured.")
    parser.add_argument("--query", help="Search query.")
    parser.add_argument("--model", default="", help="Perplexity model override.")
    parser.add_argument("--recency", default="auto", help="Perplexity recency filter: auto/day/week/month/year.")
    parser.add_argument("--search-depth", default="advanced", choices=("basic", "advanced"), help="Tavily search depth.")
    parser.add_argument("--max-results", type=int, default=5, help="Tavily max results.")
    parser.add_argument("--timeout", type=int, default=45, help="Per-request timeout seconds.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format.")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved config and exit.")
    args = parser.parse_args()

    if args.init:
        return init_config()
    if args.init_stdin:
        return init_from_stdin()
    if args.status:
        return status()
    if not args.query:
        parser.error("--query is required unless using --init or --status")
    if args.max_results < 1 or args.max_results > 20:
        parser.error("--max-results must be between 1 and 20")

    model = choose_model(args.query, args.model or None)
    recency = choose_recency(args.query, args.recency)

    if args.dry_run:
        current = key_status()
        payload = {
            "query": args.query,
            "model": model,
            "recency": recency,
            "search_depth": args.search_depth,
            "max_results": args.max_results,
            "has_perplexity_key": current["PERPLEXITY_API_KEY"]["present"],
            "has_tavily_key": current["TAVILY_API_KEY"]["present"],
            "config_path": str(CONFIG_FILE),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    with ThreadPoolExecutor(max_workers=2) as pool:
        perplexity_future = pool.submit(perplexity_search, args.query, model, recency, args.timeout)
        tavily_future = pool.submit(tavily_search, args.query, args.search_depth, args.max_results, args.timeout)
        perplexity = perplexity_future.result()
        tavily = tavily_future.result()

    merged = {
        "query": args.query,
        "perplexity": perplexity,
        "tavily": tavily,
        "ok": bool(perplexity.get("ok") or tavily.get("ok")),
    }

    if args.format == "json":
        print(json.dumps(merged, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(args.query, perplexity, tavily), end="")

    return 0 if merged["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
