# Development Rules - 开发规则

## 分支策略 - Branch Strategy

### 分支类型 - Branch Types

| 分支类型 | 分支名 | 用途 |
|---------|--------|------|
| **主分支** | `main` | 仅用于首次提交和稳定版本发布 |
| **开发分支** | `develop` | 集成开发分支，所有功能合并到此 |
| **功能/bug修复分支** | `feature/*`, `bugfix/*` | 新功能开发或bug修复 |

---

## 工作流程 - Workflow

### 1. 首次提交 - First Commit

```
使用 main 分支进行首次代码提交
```

### 2. 日常开发流程 - Daily Development

```
1. 从 develop 分支创建新的功能分支
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name

2. 在功能分支上开发和提交代码

3. 等待指令："可以合并"

4. 合并到 develop 分支
   git checkout develop
   git pull origin develop
   git merge --no-ff feature/your-feature-name
   git push origin develop

5. 删除功能分支
   git branch -d feature/your-feature-name
```

---

## 规则说明 - Rules Summary

- ✅ **首次提交** → 使用 `main` 分支
- ✅ **新增功能** → 从 `develop` 分支 fork 新分支
- ✅ **合并时机** → 当说"可以合并"时，才 merge 到 `develop` 分支
- ❌ **不要** → 直接 push 到 develop 或 main 分支
- ❌ **不要** → 未经许可合并代码

---

## 分支命名规范 - Branch Naming Convention

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能分支 | `feature/description` | `feature/risk-model`, `feature/visualization` |
| Bug修复分支 | `bugfix/description` | `bugfix/normalization-error`, `bugfix/demo-fail` |
