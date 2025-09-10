"""
“战利品大全” Markdown → YAML 转换器（面向当前自定义战利品 Schema）

教学向设计：
- 问题背景：历史“战利品大全”是 Markdown，名称后以“×N”标注数量（如“翡翠指环×2”）。
- 目标：解析分组标题（类型大类）与条目，生成符合本仓库战利品 YAML 的最小可用数据；
- 取舍：
  - 不做币种转换与估值计算；
  - 数量与重量二选一：解析到“×N”则填 quantity，weight_lb 留空（null）。
  - 内容规整假设：
    * 大类以二级或三级标题表示（## 或 ###），如“## 武器/Weapon”；
    * 条目以列表行表示：以 “- ” 或 “* ” 开头，名称后可带“×N”；
    * 其他描述暂存入 `appearance` 字段（无法可靠区分外观/效果时，全部归为外观，后续人工细化）。

YAML 目标结构（无顶层 items 大帽子）：
  - 顶层为序列（list）；每个元素是一个物品字典：
    name, quantity|weight_lb（二选一）, rarity, type, appearance, effect

用法：
  python tools/md_loot2yaml.py <loot.md> -o 戰利品/xxx.yaml
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from common.io_utils import write_text, read_text
from common.logging import logger


HEADER_RE = re.compile(r"^(#{2,3})\s+(?P<title>.+?)\s*$")
ITEM_RE = re.compile(r"^[\-*]\s+(?P<name>.+?)(?:[×x](?P<count>\d+))?\s*$")


def normalize_type(title: str) -> str:
    """根据标题粗略归一化类型。

    说明：这里只做最小映射，后续可在此补充更多规则或维护映射表。
    """

    t = title.strip().lower()
    mapping = {
        "武器": "weapon",
        "weapon": "weapon",
        "奇物": "wondrous_item",
        "wondrous": "wondrous_item",
        "药水": "potion",
        "potion": "potion",
        "其他": "other",
        "杂项": "other",
        "other": "other",
    }
    for k, v in mapping.items():
        if k in t:
            return v
    # 默认 other
    return "other"


def parse_md(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cur_type = "other"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        # 标题：更新当前类型
        m_h = HEADER_RE.match(line)
        if m_h:
            cur_type = normalize_type(m_h.group("title"))
            continue

        # 列表条目：解析名称与数量
        m_i = ITEM_RE.match(line)
        if m_i:
            name = m_i.group("name").strip()
            count = m_i.group("count")
            quantity = int(count) if count else 1
            item = {
                "name": name,
                # 二选一：数量有值，则重量为 null
                "quantity": quantity,
                "weight_lb": None,
                # 稀有度未知留空，后续人工补充
                "rarity": None,
                # 归一化的大类
                "type": cur_type,
                # 初版将行内文本作为外观描述；效果描述留空
                "appearance": None,
                "effect": None,
            }
            items.append(item)
            continue

    return items


def dump_yaml(data: Any) -> str:
    try:
        import yaml  # type: ignore
    except Exception as e:  # noqa: BLE001
        logger.error(
            "未安装 PyYAML，请先安装：pip install pyyaml>=6。错误：" + str(e)
        )
        raise

    # 让 YAML 更适合人工阅读：保持键顺序、使用缩进 2、禁用别名
    class NoAliasDumper(yaml.SafeDumper):
        def ignore_aliases(self, data):  # type: ignore[override]
            return True

    return yaml.dump(
        data,
        Dumper=NoAliasDumper,
        allow_unicode=True,
        sort_keys=False,
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="战利品 Markdown 转 YAML")
    parser.add_argument("input", help="战利品大全 Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出 YAML 路径", required=True)
    args = parser.parse_args(argv)

    in_path = Path(args.input)
    if not in_path.exists():
        logger.error(f"输入文件不存在：{in_path}")
        return 1

    items = parse_md(read_text(in_path))
    yml = dump_yaml(items)
    write_text(args.output, yml)
    logger.info(f"已写出 YAML：{args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys as _sys

    from common.logging import logger as _logger

    try:
        raise SystemExit(main())
    except Exception as _e:  # noqa: BLE001
        _logger.error(f"转换失败：{_e}")
        raise

