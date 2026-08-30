# Git 检查点与审计规则

Git 是工作流的持久检查点和审计层，不是批准机制，也不是 `.sdlc` 状态的替代品。文档正文、证据和用户确认决定工作项是否通过门禁；提交只记录当时可恢复、可审查的状态。

## 策略选择

`.sdlc/config.yaml` 的 `git_checkpoints` 支持：

- `off`：playbook 不规定提交边界，仍要求实现增量可审查、可恢复。
- `strict-only`：默认。仅 `rigor: strict` 的工作项采用下述检查点；light/standard 按项目惯例提交。
- `always`：所有需要 `.sdlc` 工作项的任务都采用检查点。琐碎修改仍不应为了凑流程创建空提交。

旧项目缺少该字段时按 `strict-only` 理解。用户或仓库规则可以覆盖默认值；在第一次提交前确认当前任务允许创建本地 Git 提交。

## 门禁与提交顺序

策略生效时，推荐顺序为：

1. **Intent agreed**：用户确认意图，正文和状态一致后，提交 `intent.md`。
2. **Specification ready**：阻塞产品决定解决、验收标准可验证后，提交 `spec.md`。
3. **Plan approved**：计划获得所需批准、包含验证与恢复路径后，提交 `plan.md`。
4. **Implement**：每条可独立验证、可独立恢复的业务链形成一个提交；不要按文件数量或编码时长机械切分。
5. **Verify and learn**：验收证据完成后提交 `verification.md`。只有确实产生跨工作项决策或可复用经验时，才同时提交 Decision 或 Lessons；不得为了流程完整而凑内容。

文档可以在门禁之间继续形成草稿，但不得通过提交草稿暗示已经批准。提交信息应描述记录下来的状态，例如：

```text
docs(sdlc): record agreed <task> intent
docs(sdlc): record ready <task> specification
docs(sdlc): record approved <task> plan
feat(<scope>): implement <independently verifiable outcome>
docs(sdlc): record <task> verification
```

`record` 比 `agree` 更准确：Git 记录已经发生的确认，不代替用户作出确认。

## 提交前检查

- 检查工作树和 staged diff，只纳入当前检查点需要的文件或明确选择的 hunks。
- 保留用户原有、其他工作项和无关格式化改动；无法安全拆分重叠改动时暂停并说明冲突。
- 文档提交前确认状态与正文证据一致；实现提交前运行该增量最小但充分的验证。
- 不用提交存在本身证明测试通过、产品批准或门禁完成。
- 不创建空提交，不为固定提交数量牺牲可理解性。

## 失败、恢复与历史

某实现增量失败时，只恢复该增量，保留已验证检查点和用户原有改动。优先使用项目允许的反向提交或精确反向补丁；不得用破坏性历史命令清除混合工作树。

如果工作已经完成但尚未提交，可以按逻辑边界补建检查点，不必改写既有历史。此时提交信息使用 `record`，并在需要时于正文或提交说明中注明这是事后记录；提交时间不代表原始确认时间。拆分或改写已经存在的提交、变基共享历史或强制推送，需要用户另行明确授权。
