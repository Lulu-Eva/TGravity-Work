#!/usr/bin/env python3
"""TGravity Work Search: local Perplexity Search API helper."""

from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import os
from pathlib import Path
import stat
import sys
import urllib.error
import urllib.request


CONFIG_DIR = Path(os.environ.get("TGRAVITY_WORK_SEARCH_HOME", Path.home() / ".config" / "tgravity-work-search"))
CONFIG_FILE = CONFIG_DIR / "config.json"
SEARCH_ENDPOINT = "https://api.perplexity.ai/search"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Config file is not valid JSON: {CONFIG_FILE}\n{exc}") from exc


def resolve_api_key() -> tuple[str | None, str]:
    env_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if env_key:
        return env_key, "env:PERPLEXITY_API_KEY"

    data = load_config()
    file_key = str(data.get("PERPLEXITY_API_KEY") or data.get("api_key") or "").strip()
    if file_key:
        return file_key, str(CONFIG_FILE)

    return None, "missing"


def save_api_key(api_key: str) -> None:
    api_key = api_key.strip()
    if not api_key:
        raise SystemExit("Empty API key; nothing saved.")
    if len(api_key) < 20:
        raise SystemExit("API key looks too short; nothing saved.")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, stat.S_IRWXU)

    payload = {
        "PERPLEXITY_API_KEY": api_key,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    tmp_file = CONFIG_FILE.with_suffix(".json.tmp")
    tmp_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp_file, stat.S_IRUSR | stat.S_IWUSR)
    tmp_file.replace(CONFIG_FILE)
    os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)


def status() -> int:
    key, source = resolve_api_key()
    if not key:
        print("status=missing")
        print(f"config_path={CONFIG_FILE}")
        print("hint=run: python3 scripts/perplexity_search.py --init")
        return 1

    print("status=configured")
    print(f"source={source}")
    print("key=present")
    return 0


def init_config() -> int:
    env_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if env_key:
        print("Found PERPLEXITY_API_KEY in environment.")
        answer = input("Save it to local TGravity Work Search config? [y/N] ").strip().lower()
        if answer != "y":
            print("Skipped saving. Environment variable will still work for this shell.")
            return 0
        api_key = env_key
    else:
        api_key = getpass.getpass("Paste Perplexity API Key: ").strip()

    save_api_key(api_key)
    print(f"Saved Perplexity API key to {CONFIG_FILE}")
    print("The key was not printed and should not be committed to Git.")
    return 0


def call_search(args: argparse.Namespace) -> dict:
    api_key, source = resolve_api_key()
    if not api_key:
        raise SystemExit(
            "Missing Perplexity API key.\n"
            f"Config path: {CONFIG_FILE}\n"
            "Initialize with: python3 scripts/perplexity_search.py --init"
        )

    payload = {
        "query": args.query,
        "max_results": args.max_results,
    }
    if args.country:
        payload["country"] = args.country
    if args.context_size:
        payload["search_context_size"] = args.context_size
    if args.language:
        payload["search_language_filter"] = args.language
    domain_filters = []
    for domain in args.domain or []:
        domain_filters.append(domain)
    for domain in args.exclude_domain or []:
        domain_filters.append(f"-{domain.lstrip('-')}")
    if domain_filters:
        payload["search_domain_filter"] = domain_filters
    if args.recency:
        payload["search_recency_filter"] = args.recency
    if args.published_after:
        payload["search_after_date_filter"] = args.published_after
    if args.published_before:
        payload["search_before_date_filter"] = args.published_before
    if args.updated_after:
        payload["last_updated_after_filter"] = args.updated_after
    if args.updated_before:
        payload["last_updated_before_filter"] = args.updated_before

    request = urllib.request.Request(
        SEARCH_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "tgravity-work-search/0.1.6",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in (401, 403):
            raise SystemExit(f"Perplexity API authorization failed ({exc.code}). Check or rotate the API key.") from exc
        if exc.code == 429:
            raise SystemExit("Perplexity API rate limit or quota hit (429). Stop retrying and check quota.") from exc
        raise SystemExit(f"Perplexity API HTTP error {exc.code}:\n{body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Network error while calling Perplexity API: {exc}") from exc
    except TimeoutError as exc:
        raise SystemExit(f"Perplexity API request timed out after {args.timeout}s.") from exc

    data["_tgravity"] = {
        "query": args.query,
        "max_results": args.max_results,
        "endpoint": SEARCH_ENDPOINT,
        "key_source": source,
        "filters": {k: v for k, v in payload.items() if k not in {"query", "max_results"}},
        "searched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    return data


def render_markdown(data: dict) -> str:
    meta = data.get("_tgravity", {})
    results = data.get("results") or []
    lines = [
        "# TGravity Work Search Results",
        "",
        f"- Query: {meta.get('query', '')}",
        f"- Searched at: {meta.get('searched_at', '')}",
        f"- Result count: {len(results)}",
        "",
    ]
    filters = meta.get("filters") or {}
    if filters:
        lines.insert(4, f"- Filters: `{json.dumps(filters, ensure_ascii=False)}`")

    if not results:
        lines.append("No results returned.")
        return "\n".join(lines) + "\n"

    for idx, item in enumerate(results, 1):
        title = item.get("title") or "Untitled"
        url = item.get("url") or ""
        snippet = item.get("snippet") or ""
        date = item.get("date") or item.get("last_updated") or ""
        lines.append(f"## {idx}. {title}")
        if url:
            lines.append(f"- URL: {url}")
        if date:
            lines.append(f"- Date: {date}")
        if snippet:
            lines.append(f"- Snippet: {snippet}")
        lines.append("")
    return "\n".join(lines)


def write_output(text: str, output: str | None) -> None:
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"wrote={output_path}")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TGravity Work Search through Perplexity Search API.")
    parser.add_argument("--init", action="store_true", help="Prompt for Perplexity API key and save it locally.")
    parser.add_argument("--status", action="store_true", help="Check whether a Perplexity API key is configured.")
    parser.add_argument("--query", help="Search query.")
    parser.add_argument("--max-results", type=int, default=8, help="Maximum search results to request.")
    parser.add_argument("--recency", choices=("hour", "day", "week", "month", "year"), help="Publication recency filter.")
    parser.add_argument("--domain", action="append", help="Limit results to a domain; repeatable.")
    parser.add_argument("--exclude-domain", action="append", help="Exclude a domain; repeatable.")
    parser.add_argument("--language", action="append", help="ISO 639-1 language code; repeatable.")
    parser.add_argument("--country", help="ISO 3166-1 alpha-2 country code.")
    parser.add_argument("--context-size", choices=("low", "medium", "high"), help="How much page content to extract.")
    parser.add_argument("--published-after", help="Return results published after date, MM/DD/YYYY.")
    parser.add_argument("--published-before", help="Return results published before date, MM/DD/YYYY.")
    parser.add_argument("--updated-after", help="Return results updated after date, MM/DD/YYYY.")
    parser.add_argument("--updated-before", help="Return results updated before date, MM/DD/YYYY.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format.")
    parser.add_argument("--output", help="Optional output file path.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    args = parser.parse_args(argv)

    if args.init:
        return init_config()
    if args.status:
        return status()
    if not args.query:
        parser.error("--query is required unless using --init or --status")
    if args.max_results < 1 or args.max_results > 20:
        parser.error("--max-results must be between 1 and 20")

    data = call_search(args)
    if args.format == "json":
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    else:
        text = render_markdown(data)
    write_output(text, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
