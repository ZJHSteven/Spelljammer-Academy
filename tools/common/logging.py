"""
统一日志与错误输出模块（教学向）：

- 目的：将日志与主流程解耦，便于统一控制台输出与未来接入文件/JSON 日志。
- 设计：提供最小的 info/warn/error 接口；必要时可扩展为结构化日志。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO


@dataclass
class Logger:
    """极简日志器。

    说明（为什么要自己写一个而不是直接 print）：
    - 将打印与业务逻辑解耦，便于今后替换为 `logging`、写文件等；
    - 统一前缀，用户更容易区分信息等级；
    - 在脚本失败时，error 会输出到 stderr，并以非零码退出（由调用方决定是否退出）。
    """

    out: TextIO = sys.stdout
    err: TextIO = sys.stderr

    def info(self, msg: str) -> None:
        self.out.write(f"[INFO] {msg}\n")

    def warn(self, msg: str) -> None:
        self.out.write(f"[WARN] {msg}\n")

    def error(self, msg: str) -> None:
        self.err.write(f"[ERROR] {msg}\n")


logger = Logger()

