# OMICKnowledge

> 面向多组学数据分析的个人知识管理系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 简介

OMICKnowledge 是一个专为生物信息学研究者设计的知识管理工具，帮助整理和检索多组学数据分析相关的实验方法、分析工具、概念和最佳实践。

涵盖技术：
- **CUT&Tag** — 靶点切割与标签化
- **ATAC-seq** — 染色质可及性分析
- **scRNA-seq** — 单细胞转录组
- **Hi-C** — 染色体构象捕获

### 核心特性

| 特性 | 说明 |
|------|------|
| **可视化探索** | 力导向图谱展示知识关联 |
| **Web 编辑器** | 浏览器中直接添加笔记 |
| **语义检索** | 自然语言查询知识库 |
| **版本控制** | 基于 Git 的知识管理 |

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph

# 安装依赖
pixi install

# 构建知识库
pixi run build-all
```

### 启动服务

```bash
# 一键启动
./start_pixi.sh
```

### 访问界面

| 地址 | 功能 |
|------|------|
| http://localhost:8080 | 知识图谱可视化 |
| http://localhost:8080/editor/ | **Web 编辑器** — 添加笔记 |
| http://localhost:8081 | 语义搜索 |

---

## 项目背景

多组学数据分析涉及复杂的技术栈和概念体系。本项目旨在构建一个面向多组学整合的知识图谱平台，系统整合染色质可及性、转录因子结合、表观修饰、三维基因组互作与细胞状态信息，形成可用于调控网络挖掘和关键节点发现的知识体系。

### 研究内容

1. **多组学数据标准化处理** — 建立统一的数据处理与注释流程
2. **知识图谱模式设计** — 明确实体、属性与关系类型
3. **知识抽取与融合** — 从多组学数据中提取标准化知识单元
4. **关系置信度评估** — 建立多证据融合的评分体系
5. **知识图谱应用** — 用于关键转录因子、增强子识别

---

## 使用指南

### 浏览知识

打开 http://localhost:8080 查看知识图谱：
- 缩放/平移画布
- 点击节点查看详情
- 顶部搜索框快速定位

### 添加笔记

#### 方式一：Web 编辑器（推荐）

访问 http://localhost:8080/editor/，填写表单：
- 选择实体类型（工具/步骤/概念等）
- 填写 ID、名称、描述
- 点击保存
- 执行 `pixi run build-all` 更新

#### 方式二：手动编辑 YAML

```bash
# 创建 YAML 文件
vim knowledge_graph/content/tools/my_tool.yaml

# 更新知识库
pixi run build-all
```

---

## 项目架构

```
knowledge_graph/
├── content/          # YAML 源文件（知识实体）
├── wiki/             # 自动生成的 Markdown Wiki
├── web/              # Web 界面
│   ├── editor/      # Web 编辑器
│   └── index.html   # 可视化界面
├── memory_core/      # 语义检索核心
└── scripts/          # 工具脚本
```

### 技术栈

- **存储**: YAML + NumPy 向量
- **后端**: Python + HTTP.server
- **前端**: D3.js + Vanilla JS
- **构建**: Pixi + Git

---

## 文档

| 文档 | 说明 |
|------|------|
| [knowledge_graph/README.md](knowledge_graph/README.md) | 详细使用文档 |
| [knowledge_graph/AGENTS.md](knowledge_graph/AGENTS.md) | LLM 维护指南 |
| [docs/LLM_WIKI_OPTIMIZATION.md](knowledge_graph/docs/LLM_WIKI_OPTIMIZATION.md) | 架构优化评估 |

---

## 许可证

MIT License

---

*项目基于 [Karpathy llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 架构设计*
