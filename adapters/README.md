# Code agent 接入原则

核心行为只维护在 `skills/solo-engineering-coach/`。适配层的职责是帮助某个 agent 找到这个目录，不复制访谈协议、文档契约或风险规则。

## 支持开放 skill 目录的 agent

用仓库根目录的通用安装器，将 skill 复制到该 agent 文档所声明的 skills 搜索目录：

```bash
python scripts/install_skill.py --target /path/to/agent/skills
```

安装后应得到 `/path/to/agent/skills/solo-engineering-coach/SKILL.md`。是否会自动触发、如何显式调用，取决于该 agent 的版本和产品设置，请以它自己的文档为准。

## 只支持项目指令文件的 agent

不要复制整份工作流。可在该 agent 读取的项目指令中加入一条路由，例如：

```text
当任务涉及需求澄清、功能规划、实现前设计或交付验证时，先完整读取
<仓库路径>/skills/solo-engineering-coach/SKILL.md，并按其中链接按需读取 references。
```

如果目标电脑上的仓库路径不同，只需更新这条路径。更稳妥的方式是把本仓库作为独立 Git 仓库克隆到固定位置，再从各项目引用它。

## Codex 示例

如果当前 Codex 配置使用默认个人目录，可以运行：

```powershell
python .\scripts\install_skill.py --target "$HOME\.codex\skills"
```

这个示例只负责文件安装，不假定或修改 Codex 的其他设置。团队或项目级安装位置应以当前版本的 Codex 文档为准。

## 迁移到另一台电脑

1. 克隆这个仓库，保留完整 Git 历史。
2. 在新电脑上确认目标 agent 的 skill 搜索目录。
3. 运行通用安装器，或在项目指令中引用核心 `SKILL.md`。
4. 用临时项目执行 `init_project.py`、`new_work_item.py` 和 `verify_project.py` 做一次冒烟测试。

`.sdlc/` 是项目自身的工程记忆，应随项目代码进入版本控制；agent 的 skill 安装副本不应进入业务项目仓库。
