# Repository Guidelines

> 面向贡献者的简明协作手册（本仓库：Spelljammer Academy）

## 项目结构与模块组织
- 根目录：核心剧情与规则 Markdown（示例：`Spelljammer Academy.md`、`Light of Xaryxis.md`）。
- `Log/`：会话日志与纪要，建议命名：`YYYY.M.D~M.D-主题.txt`（示例：`2025.8.22~8.23-某某战役.txt`）。
- `jason*/` 与其他资料目录：角色卡与数据（JSON/MD）。保留 UTF‑8 与文件名中的中文。
  - 新增：`jason人物卡/dnd-character.template.yaml`——与 JSON 模板字段完全等价的 YAML 模板（含中文注释）。

### 目录结构（补充，2025‑09‑10）
- 面向“人写”的 YAML 与模板按“领域”分目录，不再设置 `yaml/`/`json/` 顶层聚合目录：
  - `角色卡/`：后续可放置 `dnd-character.template.yaml` 与角色 YAML（按需迁移）。
  - `战利品/`：新增 `战利品.template.yaml`（顶层即物品列表，无 `items` 大帽子）。
- 模板就近存放在对应目录内（不再设单独 `templates/` 目录）。
- 机器对接所需 JSON 由脚本按需生成到任何你指定的位置（不强制 `json/` 目录）。

## 构建、测试与本地开发
- 本仓库以 Markdown/JSON 文档为主，无构建流程。
- 常用命令：
  - `git status` 查看改动；`git diff` 审阅差异；`git log --oneline` 查看历史。
  - 可选校验：JSON 用 `jq . <file.json>` 做语法检查（若已安装）。

## 人物卡模板与转换
- 模板文件：
  - JSON（现有）：`jason人物卡/dnd-character.json`
  - YAML（新增）：`jason人物卡/dnd-character.template.yaml`
- 设计原则：字段与层级 1:1 对应，不删不增，仅在 YAML 中补充了教学注释，方便协作与回顾。
- 使用建议：新建角色时优先复制 YAML 模板并填写；若已有 JSON，可使用后续提供的 `json→yaml` 转换脚本生成基础 YAML，再人工补充注释。

> 编码注意：若遇到历史文件出现乱码（常见于 GBK/UTF-8 混用），建议在转换脚本中启用自动编码回退（UTF-8 → GB18030），或在编辑器中手动切换编码以正确显示中文。

### 转换脚本
- 位置：`tools/json2yaml.py`
- 特性：
  - 零依赖纯 Python；保持键顺序；键名与字符串统一加双引号避免 YAML 歧义；
  - 自动编码回退（UTF-8 → GB18030 → 安全替换），减少历史文件乱码风险；
  - 统一日志与错误输出，失败即返回非零码。
- 用法：
  - 基本：`python tools/json2yaml.py "jason人物卡/隆金.json"`
    - 产物：`jason人物卡/隆金.yaml`
  - 指定输出：`python tools/json2yaml.py "jason人物卡/罗兰.json" -o "jason人物卡/罗兰.yaml"`
  - 校验：生成后用编辑器预览 YAML 是否渲染正常；必要时对比字段完整性。

#### 新增脚本（YAML 主导工作流）
- `tools/yaml2json.py`：通用 YAML→JSON 转换（无损、仅编码/顺序规范化，不做任何币种/单位计算）。
  - 用法：`python tools/yaml2json.py 战利品/某次-战利品.yaml -o out/某次-战利品.json`
- `tools/md_loot2yaml.py`：“战利品大全”Markdown → YAML（基于本仓库战利品 Schema 的最小解析器）。
  - 假设：条目前缀 `- `，数量写作 `×N`；类型行形如 `**类型**: 奇物 材料`。
  - 用法：`python tools/md_loot2yaml.py 战利品总结/战利品大全.md -o 战利品/某次-战利品.yaml`
- `tools/normalize_log.py`：统一 QQ 导出的战报段落，复刻仓库前半段的行格式。
  - 适用场景：Log/ 中存在“姓名: 时间”导出段落（例：`Steven: 09-22 21:53:31`）且换行/昵称与现行风格不一致时。
  - 用法：`python tools/normalize_log.py "Log/2025.9.15~9.10-布瑞尔岩奇遇.txt"`；若仅需预览，可加 `--dry-run`。
  - 处理说明：内置昵称映射（Steven→布瑞尔岩招生办主任、木夕儿→隆金、:D→罗兰、修林→奈瓦拉、咸鱼之提督→猎颅、阿芙娜→骰娘），自动合并多行文本为单行、删除时间戳并剔除骰娘 `.find/.help` 检索回包，同时直接丢弃图片消息。
  - 边界策略：若出现未登记昵称，脚本会报错提示补充映射，确保不会静默吞行。

#### 策略更新：币种
- 自 2025‑09‑10 起，统一仅使用 `gp`，仓库中不会再出现 `pp/sp/cp`；脚本不再做币种换算。

#### 战利品 Schema 要点（更新 2025‑09‑10）
- 顶层即为“物品列表”，不要再套 `items:`。
- 每个物品字段：
  - `name`（必填）
  - `quantity` 与 `weight_lb` 二选一（另一项设为 `null`）
  - `rarity`（自由文本，示例：普通/非普通/稀有/罕见/传奇）
  - `type`（仅限 7 类：武器 / 护甲 / 奇物 / 药水 / 蓝图 / 赠礼 / 不稳定；由 Markdown 一级标题 `#` 判定）
  - `appearance` / `effect`（可留空，后续补充）

#### 策略变更：硬币仅保留 gp
- 自 2025-09-10 起，转换时将 `character.equipment.coins` 统一折算为仅含 `gp`：
  - 换算：`1 pp = 10 gp`，`10 sp = 1 gp`，`100 cp = 1 gp`；结果保留两位小数。
  - 模板 `dnd-character.template.yaml` 已仅保留 `gp` 字段。
  - 历史 JSON 中若存在 `pp/sp/cp`，转换后不会保留这些键。

## 代码/文档风格与命名约定
- Markdown：
  - 标题层级清晰：`#` 章节、`##` 小节、`###` 细节；列表使用 `-`。
  - 专有名词与术语首次出现给出中文+英文；表格/统计用代码块或表格语法。
- 命名：
  - 文档允许中文与空格；数据文件建议使用短横线或日期前缀（示例：`2025-09-09-session-notes.md`）。
  - 统一使用 UTF‑8 与换行 `\n`。

## 测试与校对指南
- 目标：内容正确、链接可达、JSON 语法有效。
- 建议清单：
  - 跑一遍 JSON 语法检查（如有）；本地预览 Markdown（编辑器内置预览）。
  - 链接/引用路径可用；图片与资源相对路径指向仓库内文件。

## 提交与 Pull Request 规范
- 提交信息采用 Conventional Commits：`feat|fix|docs|test|refactor|chore(scope): message`。
  - 示例：`docs(log): 新增 2025-09-09 会话纪要`、`chore(repo): 目录整理与小修`。
- PR 要求：
  - 说明意图与影响范围，链接相关 issue；必要时附截图/日志；自检：构建/预览通过、无多余文件。

## Agent 协作注意事项（Codex）
- 仅使用内置官方工具读写与改动文件（优先 `apply_patch`）；避免使用 PowerShell `Get-Content` 等命令强行读取代码。
- 每次编辑/新增后必须：`git add -A` 与一次简洁提交（采用上述规范）。
- 若新增脚本/工具，请单一职责、分层组织，错误与边界处理独立为模块，日志与主流程解耦。
