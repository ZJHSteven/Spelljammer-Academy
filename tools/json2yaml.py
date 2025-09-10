#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON → YAML 转换脚本（零依赖，教学向）

设计目标（与仓库协作规范一致）：
- 完全保留 JSON 结构与字段（键名、层级、顺序）；
- 输出标准 YAML，字符串与需歧义规避的键名一律加双引号；
- 统一错误与日志接口，编码自动回退（UTF-8 → GB18030 → 安全替换）。

用法：
  python tools/json2yaml.py <input.json> [-o <output.yaml>]

示例：
  python tools/json2yaml.py "jason人物卡/dnd-character.json" -o "jason人物卡/dnd-character.yaml"

说明：
- 本脚本不依赖 PyYAML，内置最小 YAML 序列化器，适用于 JSON→YAML 单向转换；
- 若后续需要 YAML→JSON 互转与注释保留，请考虑引入专用库（需评估依赖与编码）。
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from typing import Any


# =====================
# 统一日志与异常封装
# =====================

def log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def log_warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def log_error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)


def die(msg: str, code: int = 1) -> None:
    log_error(msg)
    sys.exit(code)


# =====================
# 编码友好读取 JSON
# =====================

def load_json_with_fallback(path: str) -> Any:
    """优先按 UTF-8 读取；失败时自动回退 GB18030；再失败则启用替换字符。

    - 原因：历史文件可能混用 UTF-8 / GBK（Windows），直接读取会出现乱码。
    - 返回：Python 对象（dict/list/...）。
    """
    encodings = ["utf-8", "gb18030"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError as e:
            last_err = e
        except json.JSONDecodeError as e:
            die(f"JSON 语法错误：{e}")

    # 最后保底：以 UTF-8+replace 读取，尽量不崩溃（会替换非法字节）。
    log_warn(f"采用安全替换读取（可能存在个别字符乱码）：{path}")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception as e:  # pragma: no cover
        die(f"无法读取 JSON：{e if last_err is None else last_err}")


# =====================
# 最小 YAML 序列化器
# =====================

def _needs_quoting_key(s: str) -> bool:
    """判断映射键是否需要加引号。
    - 以数字开头、包含空白、特殊符号（: # - { } [ ] , & * ! | > ' " % @ `）等情况统一加引号。
    - 简化规则：只允许未引号键匹配 ^[A-Za-z_][A-Za-z0-9_-]*$
    """
    import re

    return re.match(r"^[A-Za-z_][A-Za-z0-9_-]*$", s) is None


def _yaml_quote(s: str) -> str:
    """双引号转义输出，确保 YAML 安全与可读。
    - 统一用双引号，转义 \ 和 "，将换行替换为 \n；
    - 如需多行文本的块缩进（| / >），可在后续迭代中引入，现阶段以稳妥为先。
    """
    s = s.replace("\\", "\\\\").replace("\"", "\\\"")
    s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", r"\n")
    return f'"{s}"'


def _format_scalar(value: Any) -> str:
    """按 YAML 标准格式化标量：
    - 字符串：双引号包裹
    - 布尔：小写 true/false
    - None：null
    - 数字：原样
    """
    if isinstance(value, str):
        return _yaml_quote(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    # int/float 直接转字符串
    return str(value)


def dump_yaml(obj: Any, indent: int = 0) -> str:
    """将任意 JSON 兼容对象（dict/list/scalar）序列化为 YAML。
    - 使用 2 空格缩进；
    - 映射键一律加引号（避免 "1" 这类被解析为数字键）；
    - 列表空值使用 []，映射空值使用 {}（尽量保持紧凑但可读）。
    """
    sp = " " * indent

    # dict
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = []
        for k, v in obj.items():
            key = _yaml_quote(str(k))  # 统一加引号，避免 YAML 解析为非字符串键
            if isinstance(v, (dict, list)):
                lines.append(f"{sp}{key}: {dump_yaml(v, indent + 2) if isinstance(v, list) and not v else ''}".rstrip())
                if isinstance(v, dict) and v:
                    lines[-1] = f"{sp}{key}:\n{dump_yaml(v, indent + 2)}"
                elif isinstance(v, list) and v:
                    lines[-1] = f"{sp}{key}:\n{dump_yaml(v, indent + 2)}"
            else:
                lines.append(f"{sp}{key}: {_format_scalar(v)}")
        return "\n".join(lines)

    # list
    if isinstance(obj, list):
        if not obj:
            return "[]"
        lines = []
        for item in obj:
            if isinstance(item, (dict, list)):
                head = f"{sp}-"
                if isinstance(item, dict) and item:
                    lines.append(f"{head} {dump_yaml(item, indent + 2) if False else ''}".rstrip())
                    lines[-1] = f"{head}\n{dump_yaml(item, indent + 2)}"
                elif isinstance(item, list) and item:
                    lines.append(f"{head}\n{dump_yaml(item, indent + 2)}")
                else:
                    # 空 dict/list
                    lines.append(f"{sp}- {dump_yaml(item, indent + 2)}")
            else:
                lines.append(f"{sp}- {_format_scalar(item)}")
        return "\n".join(lines)

    # scalar
    return f"{sp}{_format_scalar(obj)}"


# =====================
# CLI 入口
# =====================

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="将 JSON 人物卡无依赖转换为 YAML（保序、编码友好）")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("-o", "--output", help="输出 YAML 文件路径（缺省同名 .yaml）")
    args = parser.parse_args(argv)

    in_path = args.input
    if not os.path.exists(in_path):
        die(f"输入文件不存在：{in_path}")

    data = load_json_with_fallback(in_path)

    out_path = args.output
    if not out_path:
        base, _ = os.path.splitext(in_path)
        out_path = base + ".yaml"

    yaml_text = dump_yaml(data) + "\n"

    # 明确使用 UTF-8 保存，避免平台差异
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(yaml_text)

    log_info(f"已生成：{out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

