"""
“战利品大全” Markdown → YAML 转换器（面向当前自定义战利品 Schema）

教学向设计（按你最新要求收敛类型）：
- 仅允许 7 个大类：武器 / 护甲 / 奇物 / 药水 / 蓝图 / 赠礼 / 不稳定；
- 以 Markdown 一级标题 `# 大类` 判定物品 `type`；忽略条目内“**类型**:”里的冗余标签；
- 条目以二级标题 `## 名称` 开始；名称可在末尾携带数量标记：`xN` 或 `×N`（大小写不敏感、可含空格），未写则默认为 1；
- 从条目下的列表行提取：`**外观**: ...` 与 `**效果**: ...`；
- 可选：从 `**类型**:` 行中提取稀有度关键词（普通/非普通/稀有/罕见/传奇）；
- 数量/重量二选一：本解析仅设置 `quantity`；`weight_lb` 固定为 `null`，以便后续人工补全。

YAML 输出（顶层为物品数组）：
- 每个物品包含：name, quantity, weight_lb, rarity, type, appearance, effect。

用法：
  python tools/md_loot2yaml.py <战利品大全.md> -o 战利品/导出.yaml
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from common.io_utils import write_text, read_text
from common.logging import logger


# 一级大类（决定 type）与二级条目（决定 name）
H1_RE = re.compile(r"^#\s+(?P<cat>.+?)\s*$")
H2_RE = re.compile(r"^##\s+\*\*(?P<name>.+?)\*\*\s*(?P<qty>(?:[xX×]\s?\d+)?)\s*$")

# 列表行属性抓取
LINE_APPEAR = re.compile(r"^[\-*]\s*\*\*外观\*\*\s*[:：]\s*(?P<val>.+?)\s*$")
LINE_EFFECT = re.compile(r"^[\-*]\s*\*\*效果\*\*\s*[:：]\s*(?P<val>.+?)\s*$")
LINE_TYPE = re.compile(r"^[\-*]\s*\*\*类型\*\*\s*[:：]\s*(?P<val>.+?)\s*$")


ALLOWED = ("武器", "护甲", "奇物", "药水", "蓝图", "赠礼", "不稳定")


def normalize_category(h1_title: str) -> str:
    """将一级标题映射为 7 个允许的大类之一。

    - 直接命中：返回原中文（严格匹配）；
    - 常见变体映射：如“超自然赠礼”→“赠礼”；
    - 其他任何未知标题：归为“不稳定”。
    """

    t = h1_title.strip()
    if t in ALLOWED:
        return t
    variants = {
        "超自然赠礼": "赠礼",
        "魔法武器": "武器",
        "武器/Weapon": "武器",
        "法术卷轴": "奇物",
        "材料": "奇物",
    }
    return variants.get(t, "不稳定")


def parse_md(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cur_cat = "不稳定"
    cur_item: dict[str, Any] | None = None

    def close_item():
        nonlocal cur_item
        if cur_item is not None:
            # 补默认值与清理
            cur_item.setdefault("quantity", 1)
            cur_item.setdefault("weight_lb", None)
            cur_item.setdefault("rarity", None)
            cur_item.setdefault("appearance", None)
            cur_item.setdefault("effect", None)
            items.append(cur_item)
            cur_item = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue

        # 一级标题：切换大类
        m1 = H1_RE.match(line)
        if m1:
            close_item()
            cur_cat = normalize_category(m1.group("cat"))
            continue

        # 二级标题：开始新条目
        m2 = H2_RE.match(line)
        if m2:
            close_item()
            name = m2.group("name").strip()
            qty_str = (m2.group("qty") or "").lower().replace("×", "x").replace(" ", "")
            qty = 1
            if qty_str.startswith("x") and qty_str[1:].isdigit():
                qty = int(qty_str[1:])
            cur_item = {
                "name": name,
                "quantity": qty,
                "weight_lb": None,
                "rarity": None,
                "type": cur_cat,
                "appearance": None,
                "effect": None,
            }
            continue

        if cur_item is None:
            continue

        # 抓取外观/效果/类型（用于提取稀有度）
        ma = LINE_APPEAR.match(line)
        if ma:
            cur_item["appearance"] = ma.group("val").strip()
            continue

        me = LINE_EFFECT.match(line)
        if me:
            cur_item["effect"] = me.group("val").strip()
            continue

        mt = LINE_TYPE.match(line)
        if mt:
            val = mt.group("val")
            # 稀有度关键词
            if any(k in val for k in ("传奇", "罕见", "稀有", "非普通", "普通")):
                for k in ("传奇", "罕见", "稀有", "非普通", "普通"):
                    if k in val:
                        cur_item["rarity"] = k
                        break
            continue

    close_item()
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
