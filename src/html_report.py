from __future__ import annotations

import json
from typing import Any, Dict

from src.html_report_part1 import PART as P1
from src.html_report_part2 import PART as P2
from src.html_report_part3 import PART as P3
from src.html_report_part4 import PART as P4

_TEMPLATE = "".join([P1, P2, P3, P4])


def render_html(report: Dict[str, Any], color_convention: str = "CN") -> str:
    data = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    up_color = "#C62828" if color_convention == "CN" else "#17803B"
    down_color = "#17803B" if color_convention == "CN" else "#C62828"
    return _TEMPLATE.replace("__DATA__", data).replace("__UP__", up_color).replace("__DOWN__", down_color)
