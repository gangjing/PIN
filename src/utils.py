from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]


def load_env(path: str = ".env") -> None:
    env_path = ROOT / path
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def now_iso() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def timestamp_for_file() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d_%H%M")


def ensure_dirs() -> None:
    for name in ["reports", "output", "logs", "docs", "docs/reports"]:
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def setup_logging() -> Path:
    ensure_dirs()
    log_path = ROOT / "logs" / f"market_watch_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )
    return log_path


def parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value == "":
        return ""
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_config(path: str) -> Dict[str, Any]:
    cfg_path = ROOT / path
    try:
        import yaml  # type: ignore

        with cfg_path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        return load_simple_yaml(cfg_path)


def load_simple_yaml(path: Path) -> Dict[str, Any]:
    """Tiny YAML subset parser for the bundled config when PyYAML is absent."""
    root: Dict[str, Any] = {}
    stack = [(-1, root)]
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, value = raw.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            node: Dict[str, Any] = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            parent[key] = parse_scalar(value)
    return root


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def pct(value: Any) -> str:
    if value is None:
        return "数据不足"
    try:
        return f"{float(value):+.2f}%"
    except Exception:
        return "数据不足"


def money(value: Any) -> str:
    if value is None:
        return "数据不足"
    try:
        return f"{float(value):.2f}"
    except Exception:
        return "数据不足"
