# GitHub Actions Workflows

## Update Leaderboard

这个 workflow 会在以下情况下自动运行：

### 触发条件

1. **自动触发**：当提交到 `main` 分支时，如果修改了 `benchmark-result/summary-*.json` 文件
2. **手动触发**：可以在 GitHub Actions 页面手动运行

### 工作流程

1. **检出代码**：获取仓库的最新代码
2. **设置 Python 环境**：安装 Python 3.11
3. **安装依赖**：安装必要的 Python 包（megfile）
4. **生成报告**：运行 `benchmark-result/generate_report.py` 脚本
   - 生成 `benchmark-result/report.md` 完整报告
   - 更新 `README.md` 中的 `## 评估榜单` 部分
5. **检查变更**：检查是否有文件被修改
6. **提交变更**：如果有变更，自动提交并推送到仓库
   - 提交信息：`chore: update leaderboard and report [skip ci]`
   - 使用 `[skip ci]` 避免触发新的 CI 运行

### 权限

workflow 需要 `contents: write` 权限来提交和推送代码。

### 注意事项

- 提交信息中包含 `[skip ci]` 标记，防止无限循环触发
- 使用 GitHub Actions bot 账户进行提交
- 只有在检测到实际变更时才会提交
