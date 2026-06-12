from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="本地轻量定时运行器")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--interval", type=int, default=30, help="检查间隔秒")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    fired = set()
    while True:
        now = datetime.now().strftime("%H:%M")
        for market, meta in (config.get("markets") or {}).items():
            if not meta.get("enabled", True):
                continue
            for session, run_at in (meta.get("sessions") or {}).items():
                key = f"{datetime.now().date()}-{market}-{session}"
                if now == run_at and key not in fired:
                    mode = "pre_close" if "pre_close" in session else "afternoon" if "afternoon" in session or "mid" in session else "morning"
                    subprocess.run([sys.executable, str(Path(__file__).with_name("main.py")), "--market", market, "--mode", mode, "--html", "--json"], check=False)
                    fired.add(key)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
