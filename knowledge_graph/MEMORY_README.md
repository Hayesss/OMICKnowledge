# 语义记忆库 (Karpathy-style Memory Store)

基于向量嵌入和余弦相似度的轻量级知识检索系统，灵感来自 Andrej Karpathy 的极简设计理念。

## 架构对比

### 传统知识图谱
```
YAML → 节点+边 → D3.js 可视化
         ↓
    结构化查询（ID/关系）
```

### 语义记忆库
```
YAML → 文本嵌入 → 向量存储
              ↓
    语义相似度检索（自然语言）
```

## 快速开始

### 1. 安装依赖
```bash
pixi install
```

### 2. 构建记忆库
```bash
# 从 YAML 内容构建向量存储
pixi run build-memory

# 或使用 Python 模块
python -m memory_core build
```

### 3. 启动 API 服务
```bash
pixi run serve-memory

# 服务运行在 http://localhost:8000
```

### 4. 查询记忆库
```bash
# 交互式查询
pixi run query-memory

# 或单次查询
python -m memory_core.query -q "单细胞分析" -k 5
```

### 5. 打开 Web 界面
```bash
# 启动传统图谱可视化
cd web && python -m http.server 8080

# 或启动新的语义搜索界面
cd web_memory && python -m http.server 8081
```

## API 接口

### 健康检查
```bash
GET /health
```

### 语义搜索
```bash
GET /search?q=ATAC-seq数据分析&k=5&type=tool
```

### 获取实体
```bash
GET /entity?id=bowtie2
```

### 获取相关实体
```bash
GET /related?id=bowtie2&k=5
```

### 统计信息
```bash
GET /stats
```

### 文本相似度（POST）
```bash
POST /similar
Content-Type: application/json

{"text": "如何分析单细胞数据", "k": 5}
```

## 核心组件

```
memory_core/
├── memory_store.py    # 向量存储核心（numpy + 余弦相似度）
├── embedder.py        # 文本嵌入（sentence-transformers）
├── memory_builder.py  # YAML → 记忆库构建器
├── query.py           # 查询接口（CLI）
├── server.py          # HTTP API 服务器
└── __main__.py        # 统一入口
```

## 设计原则（Karpathy-style）

1. **简单**：纯 numpy 数组，无复杂数据库依赖
2. **高效**：预归一化向量，点积即余弦相似度
3. **本地**：所有计算本地完成，无需外部服务
4. **轻量**：MiniLM 模型（约 100MB），CPU 即可运行

## 混合使用建议

- **探索发现**：使用语义搜索找到相关概念
- **关系理解**：使用传统图谱可视化查看连接
- **深度学习**：结合两者理解知识全貌
