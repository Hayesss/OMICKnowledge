# CI/CD 指南

知识库的持续集成和持续部署方案。

## 概览

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Commit    │ -> │   Validate  │ -> │    Build    │ -> │   Deploy    │
│   (Git)     │    │  (Schema)   │    │ (Artifacts) │    │  (Release)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
  Git Hooks          GitHub Actions      Build Memory      Deploy API
  - pre-commit       - YAML lint         - Graph JSON      - Staging
  - post-commit      - Tests             - Embeddings      - Production
  - post-merge       - Security scan     - Open WebUI
```

## 快速配置

### 1. 启用 Git 钩子（本地）

```bash
# 配置 Git 使用项目钩子
git config core.hooksPath .githooks

# 验证
ls -la .githooks/
```

### 2. 配置 GitHub Actions（远程）

已自动配置，无需额外操作。工作流文件：`.github/workflows/build-and-deploy.yml`

### 3. 配置 GitLab CI（如果使用 GitLab）

创建 `.gitlab-ci.yml`：

```yaml
stages:
  - validate
  - build
  - deploy

variables:
  PIXI_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pixi"

cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - .cache/pixi
    - .pixi

validate:
  stage: validate
  image: ghcr.io/prefix-dev/pixi:latest
  script:
    - pixi install
    - pixi run validate
    - pixi run test
  only:
    - merge_requests
    - main

build:
  stage: build
  image: ghcr.io/prefix-dev/pixi:latest
  script:
    - pixi install
    - pixi run build
    - pixi run build-memory
  artifacts:
    paths:
      - web/data/graph.json
      - memory_store/
    expire_in: 1 week
  only:
    - main

deploy_staging:
  stage: deploy
  image: alpine:latest
  script:
    - echo "Deploy to staging"
  environment:
    name: staging
  only:
    - develop

deploy_production:
  stage: deploy
  image: alpine:latest
  script:
    - echo "Deploy to production"
  environment:
    name: production
  only:
    - main
```

## 自动化流程

### 本地开发流程

```bash
# 1. 编辑 YAML 内容
vim content/tools/new_tool.yaml

# 2. 添加并提交
git add content/tools/new_tool.yaml
git commit -m "content: add new tool XYZ"

# 3. 自动触发（Git 钩子）
🔍 Pre-commit: 校验 YAML 语法和 Schema
✅ Validation passed
💾 Commit created: content: add new tool XYZ
🔄 Post-commit: 后台构建记忆库
⏳ Build started in background

# 4. 推送触发 CI
git push origin main
🚀 GitHub Actions: 完整构建和部署
```

### Git 钩子说明

| 钩子 | 触发时机 | 功能 |
|------|----------|------|
| `pre-commit` | 提交前 | 校验 YAML 语法、Schema 合规性 |
| `post-commit` | 提交后 | 后台构建记忆库（仅内容变更） |
| `post-merge` | 合并后 | 自动重建（仅内容变更） |

### GitHub Actions 工作流

| Job | 触发条件 | 功能 |
|-----|----------|------|
| `validate` | 所有 PR 和 Push | 运行测试和校验 |
| `build` | Push 到 main/develop | 构建 graph.json 和 memory store |
| `deploy-api` | Push 到 develop | 部署到 Staging |
| `deploy-production` | Push 到 main | 部署到 Production |
| `sync-openwebui` | Push 到 main | 生成 Open WebUI 导入包 |
| `changelog` | Push 到 main | 生成更新日志 |

## 版本管理

### 语义化版本

```bash
# 查看当前版本
python scripts/version_manager.py version
# Current version: 0.1.0

# 升级版本
python scripts/version_manager.py bump patch   # 0.1.0 -> 0.1.1
python scripts/version_manager.py bump minor   # 0.1.1 -> 0.2.0
python scripts/version_manager.py bump major   # 0.2.0 -> 1.0.0

# 生成更新日志
python scripts/version_manager.py changelog

# 创建发布
python scripts/version_manager.py release --type minor
```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
content: 新增/修改内容
data(atac-seq): 添加实验类型定义
tool(bowtie2): 更新版本信息
fix(schema): 修复校验规则
docs(readme): 更新文档
chore(deps): 更新依赖
```

## 手动构建

### 完整构建

```bash
./scripts/build.sh
```

### 部分构建

```bash
# 仅构建图谱，跳过记忆库
./scripts/build.sh --no-memory

# 跳过测试（快速构建）
./scripts/build.sh --no-test

# 详细输出
./scripts/build.sh --verbose
```

### Pixi 任务

```bash
# 校验
pixi run validate

# 构建图谱
pixi run build

# 构建记忆库
pixi run build-memory

# 运行测试
pixi run test

# 完整准备流程
pixi run prep
```

## 部署方案

### 方案 1：本地部署（开发）

```bash
# 启动所有服务
./scripts/start_openwebui_stack.sh
```

### 方案 2：Docker Compose（测试）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  kg-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./memory_store:/app/memory_store:ro
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - open-webui:/app/backend/data
    restart: unless-stopped
    depends_on:
      - kg-api

  ollama:
    image: ollama/ollama
    volumes:
      - ollama:/root/.ollama
    restart: unless-stopped

volumes:
  open-webui:
  ollama:
```

### 方案 3：云服务部署（生产）

#### AWS ECS

```bash
# 构建镜像
docker build -t kg-api:latest .
docker tag kg-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/kg-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/kg-api:latest

# 部署
ecs-cli compose --file docker-compose.prod.yml up
```

#### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kg-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kg-api
  template:
    metadata:
      labels:
        app: kg-api
    spec:
      containers:
      - name: api
        image: kg-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: memory-store
          mountPath: /app/memory_store
          readOnly: true
      volumes:
      - name: memory-store
        configMap:
          name: kg-memory-store
```

## 监控和日志

### GitHub Actions 监控

- 访问仓库的 **Actions** 标签页查看构建状态
- 配置通知：Settings > Notifications > Actions

### API 健康检查

```bash
# 添加到 cron 每分钟检查
*/5 * * * * curl -f http://api.example.com/health || echo "API down" | mail -s "Alert" admin@example.com
```

### 日志收集

```bash
# 使用 Docker 日志驱动
docker run --log-driver=fluentd kg-api:latest

# 或使用 journald
docker run --log-driver=journald kg-api:latest
```

## 回滚策略

### 快速回滚

```bash
# Git 回滚
git revert HEAD
git push origin main

# 或使用标签回滚
git checkout v0.1.0
./scripts/build.sh
git checkout main
```

### 蓝绿部署

```yaml
# docker-compose.blue.yml (当前版本)
# docker-compose.green.yml (新版本)

# 部署新版本（绿色）
docker-compose -f docker-compose.green.yml up -d

# 健康检查
curl http://localhost:8001/health

# 切换流量（更新 Nginx/HAProxy 配置）
# 如果失败，切回蓝色
```

## 故障排除

### Git 钩子不生效

```bash
# 检查钩子路径
git config core.hooksPath

# 重新设置
git config core.hooksPath .githooks
chmod +x .githooks/*
```

### GitHub Actions 失败

```bash
# 本地模拟 Actions 环境
act -j validate

# 详细日志
act -v -j build
```

### 构建失败

```bash
# 清理缓存
rm -rf .pixi/envs/default
pixi install

# 重新构建
./scripts/build.sh --verbose
```

## 最佳实践

1. **频繁提交**：小步快跑，每次提交一个逻辑变更
2. **分支策略**：[Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) 或 [Trunk Based](https://trunkbaseddevelopment.com/)
3. **代码审查**：所有变更通过 PR 合并
4. **自动化测试**：保持测试覆盖率 > 80%
5. **文档同步**：更新知识库时同步更新文档

## 相关资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Pixi 文档](https://pixi.sh/)
