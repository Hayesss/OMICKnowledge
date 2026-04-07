# Open WebUI 集成快速开始

5 分钟内将知识图谱接入 Open WebUI。

## 前置要求

- Docker 已安装
- Pixi 已安装
- 至少 4GB 可用内存

## 一键启动（推荐）

```bash
cd /home/zhs/project/project2026/.worktrees/kg/knowledge_graph

# 使用一键启动脚本
./scripts/start_openwebui_stack.sh
```

脚本会自动：
1. ✅ 检查依赖（Docker、Pixi）
2. ✅ 构建记忆库（如未构建）
3. ✅ 启动知识图谱 API（端口 8000）
4. ✅ 启动 Open WebUI（端口 3000）

等待约 30 秒后，访问：
- Open WebUI: http://localhost:3000
- API 文档: http://localhost:8000

## 手动启动

如需分别控制服务：

### 终端 1：启动 API
```bash
pixi run serve-memory
```

### 终端 2：启动 Open WebUI
```bash
pixi run serve-openwebui
```

或手动运行 Docker：
```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

## 配置 Tool

### 步骤 1：导入 Tool

1. 访问 http://localhost:3000
2. 注册第一个账户（自动成为管理员）
3. 进入 Admin Panel → Functions → Create Function
4. 复制 `open_webui_tools/kg_memory_tool_with_valves.py` 的内容
5. 保存并启用

### 步骤 2：配置参数

在 Tool 设置中：
- **API Base URL**: `http://host.docker.internal:8000`（Docker）或 `http://localhost:8000`（独立安装）
- **Timeout**: 10
- **Top K**: 5

### 步骤 3：创建模型

1. Workspace → Models → Create Model
2. 选择 Base Model（如 qwen2.5, llama3 等）
3. 启用 Tool：多组学知识图谱检索
4. 保存

## 测试对话

新建对话，选择配置好的模型，尝试提问：

```
用户: CUT&Tag 是什么？
AI: [自动调用 Tool] CUT&Tag (Cleavage Under Targets and Tagmentation) 是一种...

用户: 用什么工具做 ATAC-seq 比对？
AI: [自动调用 Tool] 推荐使用 Bowtie2，它是...

用户: 单细胞聚类有哪些步骤？
AI: [自动调用 Tool] 单细胞聚类主要包括以下步骤...
```

## 常见问题

### API 连接失败
```
❌ 无法连接到知识图谱服务
```
**解决**: 
- 检查 API 是否运行：`curl http://localhost:8000/health`
- Linux 用户需添加 `--add-host=host.docker.internal:host-gateway`

### 无法导入 Tool
- 确保使用 `kg_memory_tool_with_valves.py`（带配置界面）
- 检查 Open WebUI 版本 >= 0.5.0

### 检索无结果
```bash
# 重建记忆库
pixi run build-memory
```

## 停止服务

```bash
# 停止 API
Ctrl+C 或 kill %1

# 停止 Open WebUI
docker stop open-webui

# 完全移除
docker rm open-webui
docker volume rm open-webui
```

## 下一步

- 📖 完整指南: [OPEN_WEBUI_GUIDE.md](OPEN_WEBUI_GUIDE.md)
- 🔧 Tool 代码: [open_webui_tools/](open_webui_tools/)
- 🧪 测试: `pixi run pytest tests/test_openwebui_integration.py -v`
