# OMICKnowledge - 多组学知识图谱

> 一个面向多组学数据分析的**个人知识管理系统**，支持可视化浏览、语义检索和增量更新。

---

## 🎯 项目目的

多组学数据分析涉及复杂的技术栈和概念体系（CUT&Tag、ATAC-seq、scRNA-seq、Hi-C 等）。本项目旨在：

1. **结构化存储** - 将零散的知识整理为可检索的结构化数据
2. **可视化探索** - 通过图谱方式直观展示概念间关系
3. **语义检索** - 支持自然语言查询，发现隐含关联
4. **增量积累** - 持续添加笔记，自动构建个人知识库

**适用场景**：生物信息学研究者、多组学数据分析学习者、需要管理复杂技术知识的研究团队。

---

## 🏗️ 项目骨架

项目采用三层架构（受 [Karpathy llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 启发）：

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Raw Sources (原始笔记)                                 │
│  ├── content/          # YAML 格式的实体定义                     │
│  │   ├── assays/       # 实验类型 (ATAC-seq, scRNA-seq...)       │
│  │   ├── tools/        # 分析工具 (Bowtie2, MACS2, Seurat...)    │
│  │   ├── steps/        # 分析步骤 (质控、比对、Peak Calling...)   │
│  │   ├── concepts/     # 关键概念 (FDR, UMAP, Fragment Size...)  │
│  │   ├── stages/       # 分析阶段 (预处理、核心分析、注释...)     │
│  │   ├── issues/       # 常见问题 (批次效应、双细胞...)           │
│  │   └── resources/    # 外部资源 (文档、教程...)                 │
│  └── edges/            # 实体间关系定义                          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: The Wiki (LLM 可读的叙事知识)                          │
│  ├── wiki/             # Markdown 格式的 wiki 页面               │
│  │   ├── index.md      # 目录索引（快速定位）                    │
│  │   ├── synthesis.md  # 综合总结（全局视角）                    │
│  │   ├── log.md        # 变更日志（追踪演进）                    │
│  │   └── {type}/       # 按类型组织的实体页面                    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Runtime (运行时服务)                                   │
│  ├── memory_store/     # 向量存储（语义检索）                    │
│  ├── web/              # D3.js 可视化界面                        │
│  ├── web_memory/       # 语义搜索界面                            │
│  └── API (port 8000)   # RESTful API 服务                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 项目内容

当前知识库包含 **27 个知识实体**：

| 类别 | 数量 | 示例 |
|------|------|------|
| **实验类型** | 2 | ATAC-seq, scRNA-seq |
| **分析工具** | 4 | Bowtie2, MACS2, Seurat, Cell Ranger |
| **分析步骤** | 11 | 质控、比对、Peak Calling、降维、聚类... |
| **关键概念** | 3 | FDR、Fragment Size、UMAP |
| **分析阶段** | 6 | 预处理、核心分析、注释... |
| **常见问题** | 2 | 批次效应、双细胞 |
| **外部资源** | 1 | MACS2 文档 |

**关系网络**：37 条实体间关系，形成完整的知识图谱。

---

## 🚀 快速开始

### 前置要求

- [Pixi](https://pixi.sh/) 包管理器（自动安装 Python 和依赖）
- 现代浏览器（Chrome/Firefox/Safari）

### 安装

```bash
# 克隆仓库
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph

# 安装依赖（首次使用）
pixi install

# 构建知识库
pixi run build-all
```

### 启动服务

**方式一：一键启动全部（推荐）**

```bash
./start_pixi.sh
# 选择 1) API + 传统 Web 界面
```

**方式二：手动启动**

```bash
# 终端 1：启动 API 服务
pixi run serve-memory

# 终端 2：启动可视化界面
cd web && python -m http.server 8080
```

### 访问界面

| 服务 | 地址 | 说明 |
|------|------|------|
| **图谱可视化** | http://localhost:8080 | D3.js 力导向图，支持缩放、拖拽、搜索 |
| **知识编辑器** | http://localhost:8080/editor/ | 🆕 浏览器中直接添加/编辑笔记 |
| **语义搜索** | http://localhost:8081 | 自然语言查询知识库 |
| **API 服务** | http://localhost:8000 | RESTful API，返回 JSON 数据 |

---

## ✏️ 添加笔记（增量更新知识库）

> **是否已实现？** ✅ **已实现**。支持添加 YAML 笔记后自动/手动更新知识库。

### 添加新知识的流程

#### 方式一：使用 Web 编辑器（推荐）

**Step 1: 打开编辑器**

访问 http://localhost:8080/editor/ 或点击主界面右上角的 "📝 编辑" 按钮。

**Step 2: 填写表单**

- 选择实体类型（工具/步骤/概念等）
- 填写 ID（唯一标识，如 `my-tool`）
- 填写名称（显示名称）
- 添加标签（按回车添加）
- 填写描述和详细说明（支持 Markdown）

**Step 3: 保存并更新**

点击 "💾 保存并更新知识库"，然后执行：

```bash
pixi run build-all   # 一键更新知识库
```

#### 方式二：手动编辑 YAML

**Step 1: 创建 YAML 笔记**

在 `content/` 下选择对应类别，创建新的 YAML 文件：

```bash
# 示例：添加新的分析工具
vim content/tools/my_tool.yaml
```

文件格式：
```yaml
id: my_tool                    # 唯一标识符
name: My Tool                  # 显示名称
type: tool                     # 实体类型
description: >                 # 简短描述
  这是一个示例工具，用于...

difficulty: beginner           # 难度级别
tags:                          # 标签，便于分类
  - analysis
  - sequencing

detailed_explanation: >        # 详细说明（支持 Markdown）
  ## 原理
  
  该工具基于...算法。
  
  ## 使用方法
  
  ```bash
  my_tool input.fastq -o output/
  ```

key_params:                    # 关键参数
  - name: --threads
    description: 并行线程数
    default: '4'
```

**Step 2: 定义关系（可选）**

在 `edges/edges.yaml` 中添加与其他实体的关系：

```yaml
edges:
  - source: my_tool
    target: quality-control     # 用于质控步骤
    relation: used_by
```

**Step 3: 更新知识库**

```bash
# 方式一：手动更新（推荐）
pixi run export-wiki           # 导出到 wiki/
pixi run build-memory          # 更新向量存储

# 方式二：完整重建
pixi run build-all             # 校验 → 导出 → 构建 → 更新
```

**Step 4: 验证更新**

```bash
# 查看新生成的 wiki 页面
cat wiki/tools/my_tool.md

# 测试 API 是否包含新实体
curl http://localhost:8000/entity?id=my_tool
```

**Step 5: 刷新浏览器**

无需重启服务，直接刷新 http://localhost:8080 即可看到更新。

---

## 🔄 自动化更新（Git 钩子）

已配置 Git 钩子，提交笔记时自动触发更新：

```bash
# 启用 Git 钩子（首次设置）
git config core.hooksPath .githooks

# 正常使用流程
git add content/tools/my_tool.yaml
git commit -m "content: add my_tool notes"  # 自动校验 + 后台构建

# 推送到远程
git push origin main                          # CI/CD 自动构建和部署
```

**自动执行的操作**：
1. ✅ YAML 语法校验
2. ✅ Schema 合规检查
3. ✅ 自动生成 wiki 页面
4. ✅ 更新向量存储（记忆库）
5. ✅ 记录变更日志

---

## 🛠️ 常用命令

```bash
# 开发工作流
pixi run validate              # 校验 YAML 语法
pixi run export-wiki           # 导出到 wiki/
pixi run build-memory          # 构建向量存储
pixi run test                  # 运行测试

# 启动服务
pixi run serve-memory          # 启动 API
pixi run serve                 # 启动 Web 界面

# 完整构建
pixi run build-all             # 一键构建全部

# 查询知识库
pixi run query-memory          # 交互式查询
```

---

## 📖 文档索引

| 文档 | 内容 |
|------|------|
| [AGENTS.md](AGENTS.md) | LLM 维护指南，定义知识库结构和工作流程 |
| [PIXI_DEPLOY.md](PIXI_DEPLOY.md) | Pixi 部署指南（无 Docker） |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 生产环境部署指南（含 Nginx/SSL） |
| [MEMORY_README.md](MEMORY_README.md) | 语义记忆库架构说明 |
| [OPEN_WEBUI_GUIDE.md](OPEN_WEBUI_GUIDE.md) | Open WebUI 集成指南 |
| [CI_CD_GUIDE.md](CI_CD_GUIDE.md) | CI/CD 配置和自动化 |

---

## 🌟 核心特性

### 1. 可视化浏览
- **力导向图**：D3.js 渲染，支持缩放、拖拽、聚焦
- **多视图**：网络视图 + 流程视图切换
- **实时搜索**：快速定位节点

### 2. 语义检索
- **向量嵌入**：基于 sentence-transformers
- **相似度搜索**：自然语言查询，返回最相关知识
- **API 接口**：RESTful API，支持集成

### 3. 增量更新
- **YAML 编辑**：人类友好的笔记格式
- **自动导出**：YAML → Markdown → 向量存储
- **热更新**：无需重启服务，刷新即可见

### 4. 版本控制
- **Git 管理**：所有内容纳入版本控制
- **变更追踪**：wiki/log.md 记录演进历史
- **协作支持**：多人协作编辑知识库

---

## 🤝 贡献

欢迎提交 Pull Request 添加新的知识实体或改进文档。

---

## 📄 许可证

MIT License

---

*本项目遵循 [Karpathy llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 架构设计*
