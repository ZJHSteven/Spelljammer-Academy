"""
编码与文件读写工具（教学向）：

- 统一采用 UTF-8；若未来需要容错，可在此扩展编码回退逻辑；
- 独立封装 I/O，便于单元测试与复用；
- 禁止在业务脚本中散落 try/except 与 open 调用，保持主流程整洁。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_text(path: str | Path, encoding: str = "utf-8") -> str:
    p = Path(path)
    return p.read_text(encoding=encoding)


def write_text(path: str | Path, content: str, encoding: str = "utf-8") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)


def write_json(path: str | Path, data: Any, ensure_ascii: bool = False, indent: int = 2) -> None:
    from .logging import logger

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
    p.write_text(text, encoding="utf-8")
    logger.info(f"已写出 JSON：{p}")

