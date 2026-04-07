# 多组学分析知识图谱

基于 YAML 内容 + Python 构建脚本 + D3.js 可视化的轻量级知识图谱系统。

## 🚀 功能概览

本项目提供三种使用方式：

| 方式 | 描述 | 访问地址 |
|------|------|----------|
| **传统图谱** | D3.js 可视化，结构化浏览 | http://localhost:8080 |
| **语义搜索** | 向量嵌入 + 相似度检索 | http://localhost:8081 |
| **Open WebUI** | 对话式 AI 助手，集成知识检索 | http://localhost:3000 |

## 🔄 CI/CD 自动化

知识库支持完整的自动化流程：

```bash
# 本地 Git 钩子（自动校验和构建）
git add content/tools/new.yaml
git commit -m "content: add new tool"  # 自动校验 + 后台构建

# 远程 CI/CD（GitHub Actions）
git push origin main  # 自动测试 → 构建 → 部署
```

**特性：**
- ✅ Git 钩子：提交前自动校验，提交后自动构建
- ✅ GitHub Actions：PR 校验、自动构建、多环境部署
- ✅ 版本管理：语义化版本、自动生成 Changelog
- ✅ Docker 部署：一键启动完整栈

**快速开始 CI/CD**: [CI_CD_GUIDE.md](CI_CD_GUIDE.md)

## 🆕 新增：Open WebUI 集成

将知识图谱作为 Tool 集成到 Open WebUI，实现对话中的智能知识检索：

```
用户: CUT&Tag 数据分析需要哪些步骤？
AI: [自动检索知识图谱]
    根据知识库，CUT&Tag 数据分析主要包括以下步骤：
    1. 质控（FastQC）...
    2. 比对（Bowtie2）...
    ...
```

**快速开始**: [QUICK_START_OPENWEBUI.md](QUICK_START_OPENWEBUI.md) | **完整指南**: [OPEN_WEBUI_GUIDE.md](OPEN_WEBUI_GUIDE.md)

## 🧠 语义记忆库 (Karpathy-style)

基于向量嵌入的语义检索系统：
- **语义搜索**：自然语言查询，发现隐含关联
- **相似度推荐**：基于向量相似度推荐相关内容
- **轻量高效**：纯 numpy 实现，无需外部数据库

查看 [MEMORY_README.md](MEMORY_README.md) 了解详情。

## 快速开始（使用 Pixi）

本项目使用 [Pixi](https://pixi.sh/) 管理环境和任务。

### 1. 一键完整启动

```bash
pixi run start
```

这会依次执行：校验 → 构建 → 测试 → 启动服务器，然后访问 http://localhost:8080 查看可视化界面。

### 2. 分步执行

```bash
# 仅安装依赖（首次使用）
pixi install

# 校验内容
pixi run validate

# 构建图谱数据
pixi run build

# 运行测试
pixi run test

# 启动本地服务器
pixi run serve
```

### 3. 常用组合任务

```bash
# 校验 + 构建 + 测试（不启动服务器）
pixi run prep
```

## 传统方式（不使用 Pixi）

### 1. 安装依赖

```bash
pip install pyyaml pytest
```

### 2. 校验内容

```bash
python scripts/validate.py
```

### 3. 构建图谱数据

```bash
python scripts/build_graph.py
```

### 4. 启动本地服务器浏览

```bash
cd web && python -m http.server 8080
```

打开浏览器访问 `http://localhost:8080`

## 项目结构

- `schema/` — 知识图谱 schema 定义
- `content/` — 实体内容（YAML 文件）
- `edges/` — 关系定义
- `scripts/` — 校验、构建、自动抓取脚本
- `tests/` — 单元测试
- `web/` — 前端可视化页面

## 添加新知识

1. 在 `content/` 下对应目录创建 YAML 文件
2. 在 `edges/edges.yaml` 中添加关系
3. 运行 `pixi run validate` 校验
4. 运行 `pixi run build` 重新构建
5. 刷新浏览器查看更新
