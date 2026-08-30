# 跨 agent 与跨电脑可移植性

## 单一事实源

仓库内 `skills/solo-engineering-coach/` 是行为和资源的唯一事实源。安装到各 agent 的目录只是副本。升级时从仓库重新安装，避免分别编辑副本产生漂移。

项目事实存放在业务仓库的 `.sdlc/`，并随代码进入版本控制。任何新 agent 都应先读取业务仓库自身的 instructions、代码和 `.sdlc/config.yaml`，而不是依赖上一段聊天历史。

## 最小能力假设

核心 skill 只假设 agent 能够：

- 读取 Markdown 和本地项目文件。
- 与用户进行多轮对话。
- 在获得授权后编辑文件、执行适当验证。

它不要求专属 API、hook、IDE、后台任务、子 agent 或特定模型。Python 脚本是可选确定性工具；没有 Python 时，agent 仍可按文档契约手工创建材料。

## 安装策略

1. 若 agent 支持开放 skill 包，把整个 `solo-engineering-coach/` 目录复制到它声明的 skills 搜索目录。
2. 若 agent 只支持项目指令，在该指令中路由到核心 `SKILL.md`，不要复制其内容。
3. 若 agent 不支持外部 instructions，只能在会话中显式要求它读取核心文件；这属于降级接入，不能保证自动触发。

仓库根目录 `scripts/install_skill.py --target <skills-dir>` 提供通用复制。它不会探测或修改未知 agent 的配置，也不会声称兼容未验证的产品版本。

## 路径与平台

- 文档引用使用相对路径；运行时路径由安装位置解析。
- 脚本只使用 Python 标准库和 `pathlib`，不用 shell 专属语法。
- 模板采用 UTF-8 和 LF；Git 可按团队设置处理工作区换行。
- 不在 skill 中写入用户名、磁盘盘符、密钥或机器特定目录。

## 迁移检查

在新电脑或新 agent 上：

1. 确认能读取 `SKILL.md` 以及四份 reference。
2. 在临时项目运行初始化和新建工作项脚本。
3. 再次运行相同命令，确认初始化不覆盖现有文件、重复 slug 被拒绝。
4. 运行普通校验和 `--strict`，确认后者能识别未完成标记。
5. 用一个真实但低风险需求测试：agent 是否先读上下文、每轮只问少量高价值问题，并在确认后才形成 intent。

最后一项是行为验证，无法由目录结构检查替代。仓库提供了 `tests/scenarios/ambiguous-feature.md` 作为可重复执行的最小场景。不同 agent 对 skill 自动发现和触发的机制不同，应以其官方说明和实际冒烟结果为准。
