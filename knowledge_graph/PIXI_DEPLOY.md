# Pixi 部署指南（无 Docker）

使用 Pixi 管理依赖和启动服务，无需 Docker。

## 环境要求

- Linux/macOS/Windows
- Pixi (自动安装 Python 和依赖)
- 内存: 2GB+

## 安装 Pixi

```bash
curl -fsSL https://pixi.sh/install.sh | bash
source ~/.bashrc
```

## 快速启动

### 方式 1: 交互式启动（推荐）

```bash
./start_pixi.sh
```

选择启动模式:
- `1` - API + 传统 Web 界面
- `2` - API + 语义搜索界面
- `3` - 仅 API
- `4` - 停止所有服务

### 方式 2: 手动启动

```bash
# 1. 启动 API (后台运行)
nohup pixi run serve-memory > logs/api.log 2>&1 &

# 2. 启动传统 Web 界面
cd web && python -m http.server 8080

# 3. 或启动语义搜索界面
cd web_memory && python -m http.server 8081
```

### 方式 3: Pixi 任务

```bash
# 查看所有可用任务
pixi task list

# 常用任务
pixi run validate        # 校验内容
pixi run build           # 构建图谱
pixi run build-memory    # 构建记忆库
pixi run test            # 运行测试
pixi run serve-memory    # 启动 API
pixi run query-memory    # 交互式查询
```

## 访问服务

启动后访问:

| 服务 | 地址 |
|------|------|
| API | http://localhost:8000 |
| 传统图谱 | http://localhost:8080 |
| 语义搜索 | http://localhost:8081 |

## 进程管理

### 查看运行状态

```bash
# 查看 API 是否在运行
curl http://localhost:8000/health

# 查看进程
ps aux | grep "serve-memory"
ps aux | grep "http.server"

# 查看端口占用
lsof -Pi :8000
lsof -Pi :8080
```

### 停止服务

```bash
# 方式 1: 使用脚本
./start_pixi.sh
# 选择 4) 停止所有服务

# 方式 2: 手动停止
kill $(cat .api.pid)      # 停止 API
kill $(cat .web.pid)      # 停止 Web
kill $(cat .memory_web.pid)  # 停止语义搜索
```

### 使用 systemd 管理（生产环境）

创建 `/etc/systemd/system/kg-api.service`:

```ini
[Unit]
Description=Knowledge Graph API
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/knowledge_graph
ExecStart=/path/to/pixi run serve-memory
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kg-api
sudo systemctl start kg-api
sudo systemctl status kg-api
```

## 日志查看

```bash
# API 日志
tail -f logs/api.log

# Web 日志
tail -f logs/web.log

# 实时查看所有日志
tail -f logs/*.log
```

## 更新项目

```bash
# 拉取最新代码
git pull origin main

# 重新构建记忆库
pixi run build-memory

# 重启服务
./start_pixi.sh
# 选择 4 停止，然后选择 1/2/3 启动
```

## 故障排除

### API 无法启动

```bash
# 检查端口占用
lsof -Pi :8000

# 释放端口
kill -9 $(lsof -Pi :8000 -sTCP:LISTEN -t)

# 手动启动查看错误
pixi run serve-memory
```

### 记忆库不存在

```bash
# 重新构建
pixi run build-memory
```

### 依赖问题

```bash
# 重新安装依赖
rm -rf .pixi/envs/default
pixi install
```

## 与 Docker 方案对比

| 特性 | Pixi 方案 | Docker 方案 |
|------|----------|------------|
| 安装复杂度 | 简单 | 需要 Docker |
| 启动速度 | 快 | 中等 |
| 资源占用 | 低 | 中等 |
| 隔离性 | 进程级 | 容器级 |
| 适用场景 | 开发/测试 | 生产/复杂环境 |
| Open WebUI | 需单独安装 | 内置 |

## 推荐场景

- **开发环境**: Pixi 方案
- **测试环境**: Pixi 或 Docker
- **生产环境**: Docker + Nginx
- **快速体验**: Pixi 方案

## 完整工作流

```bash
# 1. 克隆项目
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph

# 2. 一键启动
./start_pixi.sh

# 3. 选择模式 (推荐 1 或 2)

# 4. 访问服务
# API: http://localhost:8000
# Web: http://localhost:8080 或 http://localhost:8081

# 5. 开发编辑内容
vim content/tools/new_tool.yaml

# 6. 重新构建
pixi run build-memory

# 7. 查看效果（无需重启，API 自动加载）
```

## 相关文档

- [快速开始](QUICK_START.md)
- [API 文档](MEMORY_README.md)
- [Pixi 官方文档](https://pixi.sh/)
