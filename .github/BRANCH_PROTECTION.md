# GitHub 分支保护规则配置指南

> 配合 `.github/workflows/quality-check.yml` 使用  
> 请按以下步骤在 GitHub Repository Settings 中配置

---

## 第一步：进入分支保护规则

1. 打开仓库页面 → **Settings** → **Branches**
2. 在 **Branch protection rules** 下点击 **Add rule**
3. **Branch name pattern** 填入：`main`（再为 `develop` 重复一次）

---

## 第二步：启用以下保护选项

```
✅ Require a pull request before merging
    ✅ Require approvals: 1
    ✅ Dismiss stale pull request approvals when new commits are pushed

✅ Require status checks to pass before merging
    ✅ Require branches to be up to date before merging

    # 在搜索框中添加以下 Required status checks（名称须精确匹配）：
    ─────────────────────────────────────────────────────────
    ❌ BLOCKING checks（必须全部通过才能合并）：
    ─────────────────────────────────────────────────────────
    • ❌ Lint (blocking)
    • ❌ Unit Tests / Python 3.11 (blocking)
    • ❌ Unit Tests / Python 3.12 (blocking)
    • ❌ Security Scan (blocking on HIGH)
    • Quality Gate Summary

    ─────────────────────────────────────────────────────────
    ⚠️ WARNING-ONLY checks（不添加到 Required，仅在 PR 页面显示）：
    ─────────────────────────────────────────────────────────
    • ⚠️ Integration Tests (warn only)   ← 不要加入 Required
    ─────────────────────────────────────────────────────────

✅ Require conversation resolution before merging
✅ Do not allow bypassing the above settings
```

---

## 第三步：质量门控行为确认

| 场景 | 行为 |
|------|------|
| `lint` job 失败 | ❌ PR **不可合并**，GitHub 显示红色 × |
| 任一 Python 版本单元测试失败 | ❌ PR **不可合并** |
| `bandit`/`safety` 发现 HIGH 漏洞 | ❌ PR **不可合并** |
| 集成测试失败 | ⚠️ PR 页面显示黄色警告，**仍可合并** |
| 全部 blocking checks 通过 | ✅ 可以合并 |

---

## 第四步：本地验证（提交前）

```bash
# 快速检查（~30 秒，只用当前 Python 版本）
python scripts/pre-commit-check.py

# 完整检查（~2-3 分钟，模拟完整 CI 矩阵）
python scripts/pre-commit-check.py --full

# 只跑某个 gate
python scripts/pre-commit-check.py --gate lint
python scripts/pre-commit-check.py --gate unit
python scripts/pre-commit-check.py --gate security

# 安装 pre-commit 钩子（一次性）
pip install pre-commit
pre-commit install
```

---

## CI 工作流文件清单

| 文件 | 用途 |
|------|------|
| `.github/workflows/quality-check.yml` | 主流水线：lint → 单测 → 安全扫描 → 集成测试 → 汇总 |
| `.github/workflows/security-scan.yml` | 每周定时安全扫描（bandit + safety） |
| `.github/workflows/ci-cd.yml` | 原有流水线：Docker 构建 + 前后端测试 |
| `.pre-commit-config.yaml` | 本地提交前自动检查 |
| `scripts/pre-commit-check.py` | 手动运行本地质量检查 |

---

## 常见问题

**Q: 集成测试在 CI 上始终失败怎么办？**  
A: 集成测试用了 `continue-on-error: true`，失败只在 PR 页面显示警告，不阻断合并。如需在 CI 中提供外部服务，在 `integration-tests` job 的 `services` 节中添加对应 Docker 服务。

**Q: 如何临时跳过集成测试？**  
A: 集成测试只在 `main`/`develop` 分支或带 `run-integration` 标签的 PR 上运行。普通 feature 分支的 PR 默认跳过。

**Q: bandit 报告 MEDIUM 级别漏洞怎么办？**  
A: MEDIUM/LOW 只记录到 artifact，不阻断合并。可在代码中用 `# nosec B[code]` 注释来抑制已知的误报。

**Q: 如何添加更多 Python 版本到矩阵？**  
A: 编辑 `quality-check.yml` 中的 `matrix.python-version`，同时在 GitHub 分支保护规则中添加对应的 Required status check。
