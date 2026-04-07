# GitHub 仓库设置指南

你的代码已准备就绪，现在需要推送到 GitHub 仓库。

## 快速推送命令

```bash
cd /home/zhs/project/project2026/.worktrees/kg

# 方法 1: 使用 HTTPS (需要输入用户名和密码/Token)
git push https://github.com/Hayesss/OMICKnowledge.git feature/kg:main

# 方法 2: 如果你配置了 SSH
git push git@github.com:Hayesss/OMICKnowledge.git feature/kg:main
```

## 配置 GitHub 认证

### 方法 1: 使用 Personal Access Token (推荐)

1. 访问 GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 "Generate new token (classic)"
3. 选择权限: `repo` (完整仓库访问)
4. 生成并复制 Token

5. 配置 Git 使用 Token:
```bash
git remote set-url github https://<TOKEN>@github.com/Hayesss/OMICKnowledge.git
```

6. 推送:
```bash
git push github feature/kg:main
```

### 方法 2: 使用 SSH 密钥

1. 生成 SSH 密钥 (如果还没有):
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

2. 添加公钥到 GitHub:
   - 复制 `~/.ssh/id_ed25519.pub` 内容
   - GitHub → Settings → SSH and GPG keys → New SSH key

3. 配置远程使用 SSH:
```bash
git remote set-url github git@github.com:Hayesss/OMICKnowledge.git
```

4. 推送:
```bash
git push github feature/kg:main
```

## 推送后设置

推送完成后，建议设置默认分支：

```bash
# 切换到 main 分支
git checkout -b main

# 设置上游
git branch --set-upstream-to=github/main main
```

## 验证推送

推送成功后，访问:
https://github.com/Hayesss/OMICKnowledge

你应该能看到:
- 所有代码文件
- GitHub Actions 工作流 (.github/workflows/)
- 完整的 README

## GitHub Actions 配置

推送后，GitHub Actions 会自动运行。你可以在仓库页面点击 **Actions** 标签查看。

首次运行可能需要批准:
1. 进入 Actions 页面
2. 点击 "I understand my workflows, go ahead and enable them"

## 下一步

推送完成后:

1. **设置 Git 钩子** (本地开发):
```bash
git config core.hooksPath .githooks
```

2. **创建初始版本标签**:
```bash
python knowledge_graph/scripts/version_manager.py release --type minor
```

3. **部署测试**:
```bash
cd knowledge_graph
./scripts/start_openwebui_stack.sh
```

## 常见问题

### 推送被拒绝

```bash
# 如果提示需要先 pull
git pull github main --rebase
git push github feature/kg:main
```

### 权限错误

确保你的 Token 或 SSH 密钥有 `repo` 权限。

### 大文件推送失败

如果 d3.v7.min.js 或 dagre.min.js 推送失败，它们已经被添加到仓库。确保你的 Git 没有文件大小限制：

```bash
git config --local http.postBuffer 524288000
```
