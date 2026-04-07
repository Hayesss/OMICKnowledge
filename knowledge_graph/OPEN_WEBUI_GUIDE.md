# Open WebUI 集成指南

将多组学知识图谱与 Open WebUI 集成，通过 Tool 调用实现对话中的智能知识检索。

## 架构概述

```
┌─────────────────┐     HTTP      ┌──────────────────┐
│   Open WebUI    │ ───────────── │  知识图谱 API    │
│  (Docker:3000)  │               │   (:8000)        │
└─────────────────┘               └──────────────────┘
        │                                   │
        │ 调用 Tool: query_knowledge()      │ 语义搜索
        │                                   │
        ▼                                   ▼
┌─────────────────────────────────────────────────────┐
│                   向量记忆库 (MemoryStore)           │
│              27 条多组学知识 + 语义嵌入              │
└─────────────────────────────────────────────────────┘
```

## 快速开始

### 步骤 1：启动知识图谱 API

```bash
cd /home/zhs/project/project2026/.worktrees/kg/knowledge_graph

# 确保记忆库已构建
pixi run build-memory

# 启动 API 服务（在后台运行）
pixi run serve-memory

# 或使用模块方式
python -m memory_core server --port 8000
```

服务将运行在 `http://localhost:8000`，测试：
```bash
curl http://localhost:8000/health
# 应返回: {"status": "ok", "items": 27}
```

### 步骤 2：启动 Open WebUI

**方式 A：Docker（推荐）**

```bash
# 标准安装
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main

# 带 GPU 支持
docker run -d -p 3000:8080 \
  --gpus all \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:cuda
```

> **注意**：`--add-host=host.docker.internal:host-gateway` 是 Linux 必需的，允许容器访问主机的 API 服务。

**方式 B：独立安装**

```bash
# 安装 Open WebUI
pip install open-webui

# 启动
open-webui serve --port 3000
```

访问 http://localhost:3000，注册第一个账户（自动成为管理员）。

### 步骤 3：导入知识图谱 Tool

1. 登录 Open WebUI，进入 **Admin Panel**（左下角用户图标 → Admin Panel）

2. 选择 **Functions** → **Create Function**

3. 复制粘贴 Tool 代码：
   - 复制 `open_webui_tools/kg_memory_tool_with_valves.py` 的全部内容
   - 粘贴到代码编辑器中

4. 配置参数（Valves）：
   - **API Base URL**: 
     - Docker 方式: `http://host.docker.internal:8000`
     - 独立安装: `http://localhost:8000`
   - **Request Timeout**: `10`
   - **Default Top K**: `5`

5. 点击 **Save** 保存

6. 在 Functions 列表中，启用该 Tool（切换开关）

### 步骤 4：创建知识增强模型

1. 进入 **Workspace** → **Models** → **Create Model**

2. 配置模型：
   - **Model Name**: `多组学知识助手`
   - **Base Model**: 选择你的 LLM（如 qwen2.5, llama3.2 等）
   - **Description**: `集成多组学知识图谱，可回答 CUT&Tag、ATAC-seq、单细胞分析等相关问题`

3. **System Prompt**（系统提示）：
```
你是多组学数据分析专家，擅长 CUT&Tag、ATAC-seq、单细胞 RNA-seq、Hi-C 等组学技术。

当用户询问实验方法、分析工具、分析步骤或概念时，请使用知识图谱检索工具获取准确信息。

检索后，请：
1. 基于检索结果回答用户问题
2. 解释相关概念时保持准确和专业
3. 如有多个相关工具或方法，进行比较说明
4. 对于复杂流程，给出步骤化建议
```

4. **Tools**: 启用 `多组学知识图谱检索`

5. 点击 **Save** 保存

### 步骤 5：开始对话

1. 新建对话，选择 `多组学知识助手` 模型
2. 输入问题，例如：
   - "CUT&Tag 数据分析需要哪些步骤？"
   - "Bowtie2 和 BWA 有什么区别？"
   - "单细胞聚类有哪些常用工具？"

3. LLM 会自动调用知识图谱检索工具，并基于检索结果回答问题。

## 功能说明

### 提供的工具函数

| 函数 | 描述 | 使用场景 |
|------|------|----------|
| `query_knowledge` | 语义检索知识 | 通用查询，如"什么是 FDR" |
| `get_entity_detail` | 获取实体详情 | 查询特定工具/概念，如"bowtie2" |
| `find_related` | 查找相关内容 | 发现关联知识，如"与 MACS2 相关的工具" |

### 支持的实体类型

- 🧪 **assay**: 实验类型（CUT&Tag, ATAC-seq, scRNA-seq, Hi-C）
- 🔧 **tool**: 分析工具（Bowtie2, MACS2, Seurat, Cell Ranger）
- 📋 **step**: 分析步骤（质控、比对、peak calling、聚类）
- 💡 **concept**: 关键概念（FDR, fragment size, UMAP, PCA）
- ⚠️ **issue**: 常见问题及解决方案
- 📊 **stage**: 分析阶段
- 📚 **resource**: 外部资源

## 故障排除

### 问题：无法连接到知识图谱 API

**症状**：
```
❌ 无法连接到知识图谱服务 (http://host.docker.internal:8000)
```

**解决方案**：

1. **检查 API 服务是否运行**：
   ```bash
   curl http://localhost:8000/health
   ```

2. **Docker 网络问题（Linux）**：
   ```bash
   # 停止容器
   docker stop open-webui
   docker rm open-webui
   
   # 重新运行，添加 host 映射
   docker run -d -p 3000:8080 \
     --add-host=host.docker.internal:host-gateway \
     -v open-webui:/app/backend/data \
     --name open-webui \
     ghcr.io/open-webui/open-webui:main
   ```

3. **使用主机网络模式**：
   ```bash
   docker run -d --network host \
     -v open-webui:/app/backend/data \
     --name open-webui \
     ghcr.io/open-webui/open-webui:main
   
   # 然后访问 http://localhost:8080
   ```

4. **使用 IP 地址替代 hostname**：
   ```bash
   # 获取主机 IP
   hostname -I
   # 假设 IP 是 192.168.1.100
   
   # 在 Tool 配置中设置 API Base URL 为:
   # http://192.168.1.100:8000
   ```

### 问题：Tool 未生效

**检查清单**：
- [ ] Tool 已保存
- [ ] Tool 已启用（开关打开）
- [ ] 模型配置中启用了该 Tool
- [ ] 使用的模型支持 Function Calling

### 问题：检索结果为空

**检查**：
```bash
# 测试 API 是否正常工作
curl "http://localhost:8000/search?q=CUT&Tag&k=3"

# 检查记忆库内容
python -m memory_core stats
```

## 高级配置

### 自定义嵌入模型

编辑 `memory_core/memory_builder.py`，修改模型：
```python
embedder = Embedder("BAAI/bge-large-zh-v1.5")  # 中文优化
```

重新构建记忆库：
```bash
pixi run build-memory
```

### 多实例部署

如需部署到服务器：
```bash
# 1. 构建记忆库
pixi run build-memory

# 2. 使用 gunicorn 启动 API（生产环境）
pixi add gunicorn
pixi run gunicorn -w 4 -b 0.0.0.0:8000 "memory_core.server:app"
```

### 与 Ollama 集成

```bash
# 启动 Ollama
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# 拉取模型
ollama pull qwen2.5:14b

# 启动 Open WebUI（连接外部 Ollama）
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

## 一键启动脚本

```bash
# 同时启动 API 和 Open WebUI
pixi run start-all

# 或分别启动
pixi run serve-memory    # 终端 1：API 服务
pixi run serve-openwebui # 终端 2：Open WebUI（Docker）
```

## 相关链接

- [Open WebUI 文档](https://docs.openwebui.com/)
- [Open WebUI GitHub](https://github.com/open-webui/open-webui)
- [记忆库 API 文档](MEMORY_README.md)
