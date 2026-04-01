# 多组学分析知识图谱

基于 YAML 内容 + Python 构建脚本 + D3.js 可视化的轻量级知识图谱系统。

## 快速开始

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
3. 运行 `python scripts/validate.py` 校验
4. 运行 `python scripts/build_graph.py` 重新构建
5. 刷新浏览器查看更新
