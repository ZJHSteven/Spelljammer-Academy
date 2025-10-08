#!/usr/bin/env python3
"""将混合来源的跑团日志规范化为统一的行格式。

本脚本针对 QQ 导出的“姓名: 时间”记录段落进行清洗，目标效果如下：
1. 姓名统一映射成仓库前半段使用的带中括号角色称谓。
2. 每条消息压缩为单行文本，去掉时间戳与多余空行。
3. 图片等特殊内容视为噪声直接移除，保留纯文本剧情。

运行示例：
    python tools/normalize_log.py Log/2025.9.15~9.10-布瑞尔岩奇遇.txt
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# === 配置区（调优时集中修改） ===================================================

# 正则用于匹配“姓名: 09-22 21:53:31”形式的行。
HEADER_PATTERN = re.compile(r"^(?P<name>.+?):\s*\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*$")

# 名称映射：value = (前缀, 目标姓名)
# 前缀用于补齐像骰娘那样前置的“# ”。
NAME_MAPPING: Dict[str, Tuple[str, str]] = {
    "阿芙娜": ("# ", "[阿芙娜]"),
    "Steven": ("", "[布瑞尔岩招生办主任]"),
    "木夕儿": ("", "[隆金 AC17 HP 46/46 DC12]"),
    "木希尔": ("", "[隆金 AC17 HP 46/46 DC12]"),
    "修林": ("", "[奈瓦拉-阿玛斯塔夏]"),
    ":D": ("", "[罗兰 hp5/26 ac12dc14先6二0/3一0/4时0/2往2/2]"),
    "大D": ("", "[罗兰 hp5/26 ac12dc14先6二0/3一0/4时0/2往2/2]"),
    "咸鱼之提督": ("", "[猎颅 ac18 hp31/31 dc14]"),
}

# 需要丢弃的骰娘查询型行（例如 .find/.help 的百科返回）。
ARIFUNA_SEARCH_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r'^# \[阿芙娜\]:\s*$'),
    re.compile(r'^# \[阿芙娜\]:\s*\[.*'),
    re.compile(r'^# \[阿芙娜\]:\s*使用[\"\.].*'),
    re.compile(r'^# \[阿芙娜\]:\s*本页结果'),
    re.compile(r'^# \[阿芙娜\]:\s*共\d+条结果.*'),
    re.compile(r'^# \[阿芙娜\]:\s*帮助.*'),
    re.compile(r'^# \[阿芙娜\]:\s*词条.*'),
    re.compile(r'^# \[阿芙娜\]:\s*·.*'),
)

# 玩家输入的百科检索命令（用于跳过后续回包）。
ARIFUNA_QUERY_COMMAND = re.compile(r'^\[[^\]]+\]:\s*[\.。](?:find|help)', re.IGNORECASE)


def build_parser() -> argparse.ArgumentParser:
    """构建命令行解析器（单独拆出便于单测 & 复用）。"""
    parser = argparse.ArgumentParser(
        description="将 QQ 导出的跑团日志段落转换为统一格式。",
    )
    parser.add_argument(
        "target",
        type=Path,
        help="待格式化的日志文件路径。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅输出预览结果，不写回原文件。",
    )
    return parser


def load_lines(path: Path) -> List[str]:
    """以 UTF-8 读取文件，并在失败时抛出详细日志。

    说明：Windows 默认编码为 GBK，因此显式指定 UTF-8，避免中文注释乱码。
    """
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise RuntimeError(f"找不到目标文件：{path}") from exc
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"读取文件失败，疑似编码非 UTF-8：{path}") from exc


def sanitize_payload(raw_lines: Sequence[str]) -> Optional[str]:
    """将同一条消息的多行正文整合到单行。

    处理策略：
    - 删除空行，避免生成多余空白。
    - 图片消息视为噪声直接丢弃。
    - 其他文本直接保留，多个片段之间插入空格。
    """
    chunks: List[str] = []
    for raw in raw_lines:
        text = raw.strip()
        if not text:
            continue
        if text.startswith("<img"):
            continue
        chunks.append(text)
    if not chunks:
        return None
    return " ".join(chunks).strip()


def is_dice_feedback(line: str) -> bool:
    """判断骰娘输出是否属于检定/掷骰反馈，而非百科查询。"""
    return any(token in line for token in ("掷", "检定", "<dice>"))


def map_name(source_name: str) -> Tuple[str, str]:
    """将 QQ 显示名映射为日志内约定的角色名。

    若出现未知名称，立即抛错提醒人工补录，避免悄然丢数据。
    """
    cleaned = source_name.strip()
    if cleaned in NAME_MAPPING:
        return NAME_MAPPING[cleaned]
    raise KeyError(f"未配置的玩家昵称：{cleaned}")


def iter_messages(lines: Sequence[str]) -> Iterable[Tuple[int, str, List[str]]]:
    """按顺序产生日志消息块。

    返回值：yield (起始行号, 原始姓名, 正文列表)
    行号信息便于调试定位。
    """
    i = 0
    total = len(lines)
    while i < total:
        head = lines[i]
        match = HEADER_PATTERN.match(head)
        if not match:
            start = i
            yield start, "", [head]
            i += 1
            continue
        start = i
        name = match.group("name").strip()
        i += 1
        payload: List[str] = []
        while i < total and not HEADER_PATTERN.match(lines[i]):
            payload.append(lines[i])
            i += 1
        yield start, name, payload


def normalize_lines(lines: Sequence[str]) -> List[str]:
    """主流程：遍历整份文档，将匹配的区块改写为统一格式。"""
    output: List[str] = []
    skip_arifuna_block = False

    for index, raw_name, payload in iter_messages(lines):
        if not raw_name:
            trimmed = [line.strip() for line in payload if line.strip()]
            if not trimmed:
                output.extend(payload)
                continue

            if any(ARIFUNA_QUERY_COMMAND.match(line) for line in trimmed):
                skip_arifuna_block = True
                output.extend(payload)
                continue

            if trimmed and all("图片消息" in line for line in trimmed):
                logging.debug("丢弃图片消息行：%s", " / ".join(trimmed))
                continue

            is_arifuna_line = all(line.startswith("# [阿芙娜]:") for line in trimmed)
            if is_arifuna_line:
                if skip_arifuna_block and not any(is_dice_feedback(line) for line in trimmed):
                    logging.debug("丢弃骰娘百科信息：%s", " / ".join(trimmed))
                    continue
                if trimmed and all(
                    any(pattern.match(line) for pattern in ARIFUNA_SEARCH_PATTERNS)
                    for line in trimmed
                ):
                    logging.debug("丢弃骰娘百科信息：%s", " / ".join(trimmed))
                    continue
            else:
                skip_arifuna_block = False

            # 非“姓名: 时间”结构，原样保留。
            output.extend(payload)
            continue

        try:
            prefix, target_name = map_name(raw_name)
        except KeyError as exc:
            raise RuntimeError(f"第 {index} 行附近出现未知昵称：{exc}") from exc

        content = sanitize_payload(payload)
        if content is None:
            continue
        if not content:
            content = "（无文字内容）"
        normalized = f"{prefix}{target_name}:{content}"
        output.append(normalized)

    return output


def write_back(path: Path, lines: Sequence[str]) -> None:
    """覆盖写回原文件（带换行结尾）。"""
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")


def dry_preview(lines: Sequence[str]) -> None:
    """控制台预览首尾片段，方便人工确认。"""
    head = "\n".join(lines[:5])
    tail = "\n".join(lines[-5:])
    logging.info("=== 预览(前 5 行) ===\n%s", head)
    logging.info("=== 预览(后 5 行) ===\n%s", tail)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    content = load_lines(args.target)
    normalized = normalize_lines(content)

    if args.dry_run:
        dry_preview(normalized)
        return

    write_back(args.target, normalized)
    logging.info("已完成格式化：%s", args.target)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 —— 统一出口打印中文错误
        logging.error("格式化失败：%s", exc)
        raise
