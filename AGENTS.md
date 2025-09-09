# Repository Guidelines

> 面向贡献者的简明协作手册（本仓库：Spelljammer Academy）

## 项目结构与模块组织
- 根目录：核心剧情与规则 Markdown（示例：`Spelljammer Academy.md`、`Light of Xaryxis.md`）。
- `Log/`：会话日志与纪要，建议命名：`YYYY.M.D~M.D-主题.txt`（示例：`2025.8.22~8.23-某某战役.txt`）。
- `jason*/` 与其他资料目录：角色卡与数据（JSON/MD）。保留 UTF‑8 与文件名中的中文。

## 构建、测试与本地开发
- 本仓库以 Markdown/JSON 文档为主，无构建流程。
- 常用命令：
  - `git status` 查看改动；`git diff` 审阅差异；`git log --oneline` 查看历史。
  - 可选校验：JSON 用 `jq . <file.json>` 做语法检查（若已安装）。

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

