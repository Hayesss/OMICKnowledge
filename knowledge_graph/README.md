# OMICKnowledge

> 面向多组学数据分析的个人知识管理系统

---

## 简介

OMICKnowledge 是一个专为生物信息学研究者设计的知识管理工具，帮助整理和检索多组学数据分析（CUT&Tag、ATAC-seq、scRNA-seq、Hi-C 等）相关的实验方法、分析工具、概念和最佳实践。

### 核心特性

- **可视化探索** — 通过力导向图谱直观展示知识关联
- **语义检索** — 自然语言查询，发现隐含关联
- **Web 编辑器** — 浏览器中直接添加和编辑笔记
- **版本控制** — 基于 Git 的知识版本管理

---

## 快速开始

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph

# 2. 安装依赖
pixi install

# 3. 构建知识库
pixi run build-all
```

### 启动服务

```bash
# 方式一：一键启动（推荐）
./start_pixi.sh

# 方式二：手动启动
pixi run serve-memory        # 启动 API
cd web && python -m http.server 8080   # 启动 Web 界面
```

### 访问服务

启动后访问以下地址：

| 地址 | 功能 |
|------|------|
| http://localhost:8080 | 知识图谱可视化 |
| http://localhost:8080/editor/ | **Web 编辑器** — 添加/编辑笔记 |
| http://localhost:8081 | 语义搜索界面 |

---

## 使用指南

### 浏览知识

打开 http://localhost:8080 查看知识图谱：

- **缩放/平移** — 鼠标滚轮缩放，拖拽移动画布
- **查看详情** — 点击节点查看详细信息
- **搜索** — 顶部搜索框快速定位节点
- **筛选** — 左侧面板按类型筛选

### 添加笔记

#### 方式一：Web 编辑器（推荐）

适合快速添加新知识点：

1. 访问 http://localhost:8080/editor/
2. 填写表单（ID、名称、类型、描述等）
3. 点击"保存"
4. 执行 `pixi run build-all` 更新知识库

#### 方式二：手动编辑 YAML

适合批量添加或复杂编辑：

```bash
# 创建 YAML 文件
vim content/tools/my_tool.yaml

# 提交更新
pixi run export-wiki
pixi run build-memory
```

### 查询知识

#### 语义搜索

访问 http://localhost:8081 使用自然语言查询：

```
输入："ATAC-seq 数据分析用什么工具？"
结果：Bowtie2、MACS2 等...
```

#### API 查询

```bash
# 搜索实体
curl "http://localhost:8000/search?q=CUT&Tag&k=5"

# 获取实体详情
curl "http://localhost:8000/entity?id=bowtie2"
```

---

## 项目架构

OMICKnowledge 采用三层架构：

```
┌─────────────────────────────────────────┐
│  Layer 1: Raw Sources                   │
│  ├── content/       # YAML 源文件       │
│  └── edges/         # 关系定义          │
├─────────────────────────────────────────┤
│  Layer 2: The Wiki                      │
│  ├── wiki/          # Markdown 页面     │
│  ├── index.md       # 目录索引          │
│  └── synthesis.md   # 综合总结          │
├─────────────────────────────────────────┤
│  Layer 3: Runtime                       │
│  ├── web/           # Web 界面          │
│  ├── memory_store/  # 向量存储          │
│  └── API            # RESTful 服务      │
└─────────────────────────────────────────┘
```

### 目录说明

```
knowledge_graph/
├── content/              # 知识实体定义（YAML）
│   ├── assays/          # 实验类型
│   ├── tools/           # 分析工具
│   ├── steps/           # 分析步骤
│   ├── concepts/        # 关键概念
│   ├── stages/          # 分析阶段
│   ├── issues/          # 常见问题
│   └── resources/       # 外部资源
│
├── wiki/                 # 自动生成的 Wiki 页面
├── web/                  # Web 界面
│   ├── editor/          # 编辑器
│   ├── index.html       # 主界面
│   └── static/          # 静态资源
│
├── memory_core/          # 语义检索核心
├── scripts/              # 工具脚本
└── docs/                 # 文档
```

---

## 知识库内容

当前知识库包含 **27 个实体**：

| 类别 | 数量 | 示例 |
|------|------|------|
| 实验类型 | 2 | ATAC-seq、scRNA-seq |
| 分析工具 | 4 | Bowtie2、MACS2、Seurat、Cell Ranger |
| 分析步骤 | 11 | 质控、比对、Peak Calling、降维、聚类等 |
| 关键概念 | 3 | FDR、UMAP、Fragment Size |
| 分析阶段 | 6 | 预处理、核心分析、注释等 |
| 常见问题 | 2 | 批次效应、双细胞 |

---

## 开发指南

### 常用命令

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
```

### 添加新实体

1. **确定实体类型** — assay、tool、step、concept、stage、issue、resource

2. **创建 YAML 文件** — 放在 `content/{类型}/` 目录下

3. **填写内容** — 参考以下模板：

```yaml
id: my_tool
name: My Tool
type: tool
description: 简短描述（50-100字）
difficulty: beginner
tags:
  - analysis
  - sequencing

detailed_explanation: |
  ## 原理
  
  详细说明...
  
  ## 使用方法
  
  ```bash
  my_tool input.fastq -o output/
  ```
```

4. **更新知识库** — 执行 `pixi run build-all`

---

## 架构设计

### 设计理念

OMICKnowledge 遵循 [Karpathy llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式：

- **Raw Sources** — 人类友好的 YAML 格式，便于编辑
- **The Wiki** — 自动生成 Markdown，便于 LLM 阅读
- **Runtime** — 向量存储和 API，便于检索

### 数据流

```
编辑 YAML → 导出 Wiki → 构建记忆库 → API 检索
    ↑                                          ↓
    └──────────── 浏览器可视化 ←────────────────┘
```

### 技术栈

- **存储**: YAML (源文件) + NumPy (向量)
- **后端**: Python + HTTP.server
- **前端**: D3.js (可视化) + Vanilla JS (编辑器)
- **构建**: Pixi (包管理) + Git (版本控制)

---

## 文档索引

| 文档 | 内容 |
|------|------|
| [AGENTS.md](AGENTS.md) | LLM 维护指南 |
| [PIXI_DEPLOY.md](PIXI_DEPLOY.md) | Pixi 部署指南 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 生产环境部署 |
| [MEMORY_README.md](MEMORY_README.md) | 语义记忆库架构 |
| [OPEN_WEBUI_GUIDE.md](OPEN_WEBUI_GUIDE.md) | Open WebUI 集成 |

---

## 许可证

MIT License

---

*遵循 [Karpathy llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 架构设计*
