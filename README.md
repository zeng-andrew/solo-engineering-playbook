# Solo Engineering Playbook

面向个人开发者的 AI 工程协作手册与可移植 skill。它的重点不是让 AI 套一组文档模板，而是让 AI 先像经验丰富的同事一样与你讨论：澄清问题、解释取舍、挑战隐含假设，再把共识沉淀为可执行的工程材料。

核心 skill 是 [`solo-engineering-coach`](skills/solo-engineering-coach/SKILL.md)。它不依赖某个 code agent 的专属 API、hook 或多 agent 能力；支持开放 skill 目录的 agent 可直接加载，不支持的 agent 也可以通过自己的项目指令文件引用它。

## 它解决什么问题

- 想法还模糊时，AI 每轮只提出 1–3 个真正影响方向的问题，并解释为什么要问。
- 你不确定答案时，AI 给出 2–3 个可选方案、代价和明确建议，而不是把决定丢回给你。
- 产品决定由你确认；低风险的工程实现细节可以授权 AI 自行处理。
- 共识依次沉淀为 `intent.md`、`spec.md`、`plan.md`、`verification.md`，而不是先写一堆看似完整但未经讨论的文档。
- 流程强度按风险调整，小修改不会被重流程拖慢，支付、权限、数据迁移等高风险改动则会得到更严格的检查。
- Git 是可配置的审计与恢复层：strict 工作项默认形成文档门禁和可独立验证的实现提交，普通任务不按固定数量机械拆分。

## 仓库结构

```text
skills/solo-engineering-coach/   核心 skill，唯一行为规范来源
  SKILL.md                       入口和工作流路由
  references/                    访谈、风险、文档契约、可移植性说明
  assets/templates/              写入项目 .sdlc/ 的模板
  scripts/                       初始化、建工作项、结构校验工具
adapters/README.md               不同 agent 的轻量接入方式
scripts/install_skill.py         通用复制安装器
tests/                           脚本和包结构测试
  scenarios/                    跨 agent 的人工行为冒烟场景
```

## 安装到 code agent

先确认你的 agent 从哪个目录发现 skills，然后把这个目录作为 `--target`。安装器只复制核心 skill，不修改 agent 的全局配置：

```bash
python scripts/install_skill.py --target /path/to/agent/skills
```

例如 Codex 的个人 skills 目录通常可以指定为 `~/.codex/skills`。Windows PowerShell 可写为：

```powershell
python .\scripts\install_skill.py --target "$HOME\.codex\skills"
```

若目标已经存在，安装器默认拒绝覆盖。确认要升级时显式使用 `--replace`；旧版本会先被重命名为带时间戳的备份。其他 agent 的接入原则见 [`adapters/README.md`](adapters/README.md)。

仓库中的 `skills/solo-engineering-coach` 是单一事实源。修改后重新执行安装命令，不要在多个安装副本中分别维护。

## 在项目中使用

对 agent 说：

> 使用 solo-engineering-coach 帮我梳理这个想法。先和我讨论，不要直接实现：……

首次使用时，skill 会先读取项目上下文，并建议交互方式与严谨度。默认适合个人开发者的是：

- `interaction: coach`：多解释、多引导、主动教学。
- `rigor: standard`：保留关键文档和验证，但不过度增加仪式。
- `git_checkpoints: strict-only`：只对 strict 工作项启用 Git 检查点；可改为 `off` 或 `always`。

也可以手工初始化 `.sdlc/`：

```bash
python /path/to/solo-engineering-coach/scripts/init_project.py --project . --git-checkpoints strict-only
python /path/to/solo-engineering-coach/scripts/new_work_item.py --project . --slug user-login --title "用户登录"
python /path/to/solo-engineering-coach/scripts/verify_project.py --project .
```

`verify_project.py` 默认把尚未讨论完成的标记作为警告；准备进入实现或交付前使用 `--strict`，此时未解决标记会导致非零退出码。

## 开发与验证

本仓库不需要第三方 Python 包：

```bash
python -m unittest discover -s tests -v
python -m compileall -q skills/solo-engineering-coach/scripts scripts
```

支持 Python 3.9 及以上版本。路径处理使用标准库 `pathlib`，脚本在 Windows、macOS 和 Linux 上采用相同参数。

## 版本边界

v0.1 提供的是可移植的交互协议、文档契约和本地文件工具。它不会自动调用 issue tracker、CI、云服务或多个 agent，也不会替你决定尚未确认的产品问题。具体 code agent 是否自动发现 skill，取决于该 agent 自己的加载机制。

迁移到新 agent 后，除运行脚本测试外，还应按 [`tests/scenarios/ambiguous-feature.md`](tests/scenarios/ambiguous-feature.md) 做一次对话冒烟测试；需要 Git 门禁时再执行 [`tests/scenarios/strict-git-checkpoints.md`](tests/scenarios/strict-git-checkpoints.md)。目录结构正确不等于交互行为正确。
