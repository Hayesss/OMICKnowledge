# AGENTS.md - 知识图谱维护指南

本文件指导 LLM Agent（如 Claude、Kimi 等）如何维护多组学知识图谱。

---

## 项目架构

```
knowledge_graph/
├── content/              # 📁 原始 YAML 源文件 (Raw Sources)
│   ├── assays/          # 实验类型定义
│   ├── tools/           # 分析工具定义
│   ├── steps/           # 分析步骤定义
│   ├── concepts/        # 关键概念定义
│   ├── stages/          # 分析阶段定义
│   ├── issues/          # 常见问题
│   └── resources/       # 外部资源
│
├── wiki/                 # 📁 LLM 可读的 Markdown Wiki
│   ├── assays/          # 实验类型页面
│   ├── tools/           # 工具页面
│   ├── steps/           # 步骤页面
│   ├── concepts/        # 概念页面
│   ├── index.md         # 📖 目录索引
│   ├── synthesis.md     # 📖 综合总结
│   └── log.md           # 📖 变更日志
│
├── edges/               # 📁 关系定义
│   └── edges.yaml       # 实体间关系
│
├── memory_core/         # 📁 语义记忆库 (向量存储)
│   └── ...
│
└── scripts/             # 📁 工具脚本
    └── yaml_to_wiki.py  # YAML → Wiki 导出
```

**架构模式**: [llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Raw Sources (YAML) → The Wiki (Markdown) → LLM Query

---

## 核心工作流程

### 1. Ingest (摄取新内容)

当用户添加/修改 YAML 文件时，执行：

```bash
# 1. 验证 YAML 语法
pixi run validate

# 2. 导出到 Wiki
python scripts/yaml_to_wiki.py

# 3. 更新记忆库
pixi run build-memory

# 4. 记录变更 (手动添加到 wiki/log.md)
```

**你的职责**:
- 确保 YAML 格式正确
- 检查必填字段: `id`, `name`, `type`, `description`
- 导出后验证 wiki 页面生成

### 2. Query (查询知识)

当用户询问问题时：

**步骤**:
1. 首先阅读 `wiki/index.md` 找到相关实体
2. 深入阅读具体实体页面 (`wiki/{type}/{id}.md`)
3. 查看 `wiki/synthesis.md` 获取全局视角
4. 综合信息生成回答
5. 引用来源页面

**工具**:
```bash
# API 搜索
pixi run query-memory

# 或直接读取 wiki 文件
cat wiki/tools/bowtie2.md
```

### 3. Lint (健康检查)

定期检查知识库健康状态：

```bash
# 检查孤立页面 (无入站链接)
python scripts/lint_wiki.py

# 检查缺失的交叉引用
python scripts/check_links.py

# 更新综合总结
# 根据新内容更新 wiki/synthesis.md
```

**检查清单**:
- [ ] 所有 YAML 都有对应的 wiki 页面
- [ ] 没有死链接
- [ ] synthesis.md 反映最新知识
- [ ] log.md 记录最新变更

---

## 内容规范

### YAML 文件格式

```yaml
id: bowtie2                    # 唯一标识符 (snake_case)
name: Bowtie2                  # 显示名称
type: tool                     # 实体类型 (assay|tool|step|concept|stage|issue|resource)
description: >                 # 简短描述 (50-100字)
  快速且内存高效的短序列比对工具...

difficulty: beginner           # 难度 (beginner|intermediate|advanced)
tags:                          # 标签列表
  - atac-seq
  - alignment

# 可选字段
detailed_explanation: >        # 详细说明 (支持 Markdown)
  Bowtie2 是基于 BWT 的...

key_params:                    # 关键参数 (工具/步骤)
  - name: -X
    description: 最大插入片段大小
    default: '1000'

input: FASTQ 文件              # 输入 (步骤特有)
output: BAM 文件               # 输出 (步骤特有)

solution: >                    # 解决方案 (issues 特有)
  如果遇到此问题，可以...
```

### Wiki 页面格式

每个实体页面自动生成，包含：

```markdown
# {实体名称}

## 基本信息
- **ID**: `{id}`
- **类型**: {type}
- **难度**: {difficulty}
- **标签**: `{tag1}` `{tag2}`

## 描述
{description}

## 详细说明
{detailed_explanation}

## 相关实体
- → [相关实体1](entity1.md) - 描述
- ← [相关实体2](entity2.md) - 描述

## 元信息
- **来源**: `content/{type}/{id}.yaml`
- **更新**: {date}
```

---

## 关系定义

在 `edges/edges.yaml` 中定义实体关系：

```yaml
edges:
  - source: bowtie2          # 源实体
    target: alignment        # 目标实体
    relation: used_by        # 关系类型
    
  - source: atac-seq
    target: macs2
    relation: uses_tool
```

**常用关系类型**:
- `uses_tool`: 使用工具
- `used_by`: 被使用
- `has_step`: 包含步骤
- `part_of`: 属于
- `requires`: 依赖
- `outputs_to`: 输出到

---

## 编码原则

1. **奥卡姆剃刀**: 如无必要，勿增实体
2. **第一性原理**: 从基础出发理解问题
3. **避免防御性编程**: 信任输入，但验证
4. **渐进披露**: 简单问题简单回答，复杂问题逐步展开

## 文档原则

1. **中文优先**: 所有文档用中文编写
2. **简洁清晰**: 避免冗余，直击要点
3. **交叉引用**: 实体间建立链接，形成网络
4. **版本控制**: 重要变更记录在 log.md

---

## 常用命令

```bash
# 验证内容
pixi run validate

# 构建记忆库
pixi run build-memory

# 导出 Wiki
python scripts/yaml_to_wiki.py

# 查询知识库
pixi run query-memory

# 启动 API
pixi run serve-memory

# 运行测试
pixi run test
```

---

## 最佳实践

### 添加新实体

1. 创建 YAML 文件: `content/{type}/{id}.yaml`
2. 确保必填字段完整
3. 运行 `pixi run validate` 检查
4. 运行 `python scripts/yaml_to_wiki.py` 导出
5. 验证 wiki 页面生成正确
6. 更新 `wiki/log.md` 记录变更

### 修改现有实体

1. 编辑 YAML 文件
2. 更新 `last_updated` 字段
3. 重新导出 Wiki
4. 检查是否影响其他实体（交叉引用）
5. 如重大变更，更新 `wiki/synthesis.md`

### 删除实体

1. 删除 YAML 文件
2. 删除 wiki 页面
3. 更新所有引用该实体的页面
4. 在 log.md 记录删除

---

## 故障排除

### Wiki 页面未生成

```bash
# 检查 YAML 语法
python -c "import yaml; yaml.safe_load(open('content/xxx.yaml'))"

# 手动导出单个实体
python scripts/yaml_to_wiki.py --entity bowtie2
```

### 记忆库构建失败

```bash
# 检查记忆库是否损坏
ls -la memory_store/

# 重建记忆库
rm -rf memory_store/
pixi run build-memory
```

### 交叉引用错误

```bash
# 检查死链接
grep -r "\[.*\](.*\.md)" wiki/ | grep -v "$(ls wiki/)"
```

---

## 参考资源

- [llm-wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [项目 README](../README.md)
- [Wiki 索引](../wiki/index.md)

---

*本指南由 LLM 和开发者共同维护，随项目演进更新*
