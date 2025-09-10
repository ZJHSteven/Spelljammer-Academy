"""
YAML → JSON 通用转换器（无损、无币种转换版）

教学向说明：
- 背景：人类以 YAML 为主写作；对接外部系统（如 5etool）需要 JSON。
- 目标：在不改变字段含义与顺序的前提下，将 YAML 转为 JSON；保留中文；不做任何币种/单位计算。
- 设计取舍：
  - 仅使用标准库 + PyYAML（若不可用则报错提示安装），避免引入重量依赖；
  - 严格区分主流程与错误处理/日志，便于维护与扩展；
  - 通过 `OrderedDict`（Python 3.7+字典已保证插入有序）保持键顺序；

用法：
  python tools/yaml2json.py <input.yaml> [-o <output.json>]

示例：
  python tools/yaml2json.py "战利品/示例-战利品.yaml" -o "out/示例-战利品.json"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common.io_utils import read_text, write_json
from common.logging import logger


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except Exception as e:  # noqa: BLE001
        logger.error(
            "未安装 PyYAML，请先安装：pip install pyyaml>=6。错误：" + str(e)
        )
        sys.exit(2)

    text = read_text(path)
    try:
        # 使用 SafeLoader，避免执行任意对象构造。
        data = yaml.safe_load(text)
    except Exception as e:  # noqa: BLE001
        logger.error(f"YAML 解析失败：{path} => {e}")
        sys.exit(1)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="YAML 转 JSON（无损）")
    parser.add_argument("input", help="输入 YAML 文件路径")
    parser.add_argument(
        "-o", "--output", help="输出 JSON 文件路径（省略则打印到 stdout）"
    )

    args = parser.parse_args(argv)
    in_path = Path(args.input)
    if not in_path.exists():
        logger.error(f"输入文件不存在：{in_path}")
        return 1

    data = load_yaml(in_path)

    if args.output:
        write_json(args.output, data, ensure_ascii=False, indent=2)
    else:
        import json

        sys.stdout.write(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

