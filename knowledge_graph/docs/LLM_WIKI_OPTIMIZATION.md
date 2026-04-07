# 基于 Karpathy llm-wiki 模式的项目优化评估

## 当前架构 vs llm-wiki 模式

| 维度 | 当前项目 | llm-wiki 模式 | 优化建议 |
|------|---------|--------------|---------|
| **数据结构** | YAML 结构化数据 | Markdown + 交叉引用 | ✅ 已有 YAML，可导出 Markdown wiki |
| **知识维护** | 手动编辑 | LLM 自动维护 | ⚠️ 半自动：YAML 手动，导出自动 |
| **查询方式** | API 语义搜索 | 读取 wiki 页面 | ✅ 结合两者：API + Markdown wiki |
| **内容格式** | 结构化 YAML | 叙事性 Markdown | ⚠️ 保持 YAML 主存储，导出 Markdown 阅读版 |
| **增量构建** | 需重新构建记忆库 | 实时更新 wiki | ✅ 改进：监听 YAML 变更自动导出 |

## 核心改进点

### 1. 添加三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  Raw Sources (原始文档)                                      │
│  - content/*.yaml (实体定义)                                  │
│  - edges/*.yaml (关系定义)                                    │
│  - 论文/文档/网页 (外部源)                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Ingest
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  The Wiki (LLM 可读的 Markdown)                              │
│  - wiki/entities/*.md (实体页面)                              │
│  - wiki/concepts/*.md (概念页面)                              │
│  - wiki/synthesis.md (综合总结)                               │
│  - wiki/index.md (目录索引)                                   │
│  - wiki/log.md (变更日志)                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Query
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Schema (AGENTS.md)                                          │
│  - 告诉 LLM 如何维护 wiki                                    │
│  - 定义页面格式和约定                                         │
│  - 工作流程：Ingest/Query/Lint                               │
└─────────────────────────────────────────────────────────────┘
```

### 2. 新增核心文件

#### wiki/index.md (目录索引)

```markdown
# 多组学知识图谱索引

## 实体类型 (Entity Types)

### 实验类型 (Assays)
- [CUT&Tag](entities/cut-tag.md) - 靶点切割与标签化技术
- [ATAC-seq](entities/atac-seq.md) - 染色质可及性测序
- [scRNA-seq](entities/scrna-seq.md) - 单细胞转录组测序
- [Hi-C](entities/hi-c.md) - 染色体构象捕获

### 分析工具 (Tools)
- [Bowtie2](entities/bowtie2.md) - 短序列比对工具
- [MACS2](entities/macs2.md) - Peak calling 工具
- [Seurat](entities/seurat.md) - 单细胞分析 R 包
- [Cell Ranger](entities/cellranger.md) - 10x Genomics 流程

### 关键概念 (Concepts)
- [FDR](entities/fdr.md) - 错误发现率
- [Fragment Size](entities/fragment-size.md) - 片段大小
- [UMAP](entities/umap.md) - 非线性降维算法

### 分析步骤 (Steps)
- [Quality Control](entities/quality-control.md) - 质量控制
- [Alignment](entities/alignment.md) - 序列比对
- [Peak Calling](entities/peak-calling.md) - Peak 检测

## 统计

- 总实体数: 27
- 最后更新: 2026-04-07
- 来源文件数: 68
```

#### wiki/log.md (变更日志)

```markdown
# 知识图谱变更日志

## [2026-04-07] ingest | 新增单细胞分析内容
- 添加 Seurat 工具页面
- 添加 Cell Ranger 工具页面
- 新增 scRNA-seq 分析步骤
- 更新索引

## [2026-04-06] ingest | 新增 ATAC-seq 流程
- 添加 Bowtie2 工具详情
- 添加 MACS2 peak calling 步骤
- 新增质量控制概念

## [2026-04-05] lint | 健康检查
- 发现 3 个孤立页面，添加交叉引用
- 更新过时链接
- 添加缺失的概念定义
```

#### wiki/synthesis.md (综合总结)

```markdown
# 多组学分析流程综合

## 概述

本项目涵盖四种主要组学技术，从"结合-开放-状态-空间"四个维度解析基因调控。

## 技术对比

| 技术 | 维度 | 核心问题 | 主要工具 |
|------|------|---------|---------|
| CUT&Tag | 结合 | 转录因子结合位置 | Bowtie2, MACS2 |
| ATAC-seq | 开放 | 染色质可及性区域 | Bowtie2, MACS2 |
| scRNA-seq | 状态 | 细胞类型与基因表达 | Cell Ranger, Seurat |
| Hi-C | 空间 | 三维基因组结构 | HiC-Pro, Juicebox |

## 交叉引用

- CUT&Tag + ATAC-seq → 识别活跃调控元件
- scRNA-seq + ATAC-seq → 单细胞多组学整合
- Hi-C + 其他 → 远端调控关系验证

## 待深入研究

- [ ] 单细胞 CUT&Tag 技术
- [ ] 多组学数据整合算法
- [ ] 空间转录组技术
```

### 3. 更新 AGENTS.md (Schema)

```markdown
# OMICKnowledge Wiki 维护指南

你是多组学知识图谱的维护助手。

## 目录结构

```
knowledge_graph/
├── content/          # 原始 YAML 源文件
├── wiki/             # LLM 可读的 Markdown wiki
│   ├── entities/     # 实体页面
│   ├── concepts/     # 概念页面
│   ├── index.md      # 目录索引
│   ├── log.md        # 变更日志
│   └── synthesis.md  # 综合总结
└── memory_store/     # 向量存储
```

## 工作流程

### 1. Ingest (摄取新内容)

当用户添加新的 YAML 文件时：

1. 读取 YAML 内容
2. 创建对应的 wiki/entities/*.md 页面
3. 更新 wiki/index.md 目录
4. 更新相关概念页面的交叉引用
5. 在 wiki/log.md 记录变更
6. 检查是否需要更新 synthesis.md

**页面格式模板：**

```markdown
# {实体名称}

## 基本信息
- **类型**: {assay|tool|concept|step}
- **难度**: {beginner|intermediate|advanced}
- **标签**: {tag1, tag2}

## 描述
{详细描述}

## 相关实体
- [{相关实体}]({link})

## 来源
- 原始文件: content/{path}.yaml
- 最后更新: {date}
```

### 2. Query (查询)

当用户询问问题时：

1. 首先读取 wiki/index.md 找到相关页面
2. 深入读取相关实体页面
3. 综合信息生成回答
4. 引用来源页面
5. (可选) 将回答保存为新 wiki 页面

### 3. Lint (健康检查)

定期检查 wiki：

- [ ] 孤立页面（无入站链接）
- [ ] 死链接
- [ ] 缺失的概念定义
- [ ] 过时的综合总结
- [ ] 交叉引用完整性

## 约定

1. **中文为主**：所有 wiki 页面使用中文
2. **交叉引用**：使用相对链接 `[文本](path/to/page.md)`
3. **YAML Frontmatter**：可选添加元数据
4. **渐进披露**：详细内容折叠在 Details 部分
```

### 4. 导出脚本

创建脚本将 YAML 自动导出为 Markdown wiki：

```python
#!/usr/bin/env python3
"""
yaml_to_wiki.py - 将 YAML 内容导出为 Markdown wiki

遵循 llm-wiki 模式：
- 保持 YAML 为原始源文件
- 生成 Markdown 便于 LLM 阅读和交叉引用
- 维护 index.md 和 log.md
"""

import yaml
from pathlib import Path
from datetime import datetime


def export_entity_to_wiki(entity_file: Path, output_dir: Path):
    """将单个 YAML 实体导出为 Markdown wiki 页面."""
    
    with open(entity_file) as f:
        data = yaml.safe_load(f)
    
    entity_type = entity_file.parent.name
    entity_id = data.get('id', entity_file.stem)
    
    # 构建 Markdown 内容
    md_content = f"""# {data.get('name', entity_id)}

## 基本信息
- **类型**: {entity_type}
- **ID**: `{entity_id}`
- **难度**: {data.get('difficulty', 'unknown')}
- **标签**: {', '.join(data.get('tags', []))}

## 描述
{data.get('description', '暂无描述')}

## 详细说明
{data.get('detailed_explanation', '暂无详细说明')}

## 来源
- 原始文件: `{entity_file}`
- 最后导出: {datetime.now().strftime('%Y-%m-%d')}

---
*本页面由 LLM 从 YAML 源文件自动生成，保持同步更新*
"""
    
    # 写入文件
    output_file = output_dir / f"{entity_id}.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(md_content)
    
    return output_file


def update_index(wiki_dir: Path, entities: list):
    """更新 wiki/index.md 目录索引."""
    
    index_content = f"""# 多组学知识图谱索引

*最后更新: {datetime.now().strftime('%Y-%m-%d')}*

## 实体列表

"""
    
    # 按类型分组
    by_type = {}
    for entity in entities:
        etype = entity.get('type', 'unknown')
        by_type.setdefault(etype, []).append(entity)
    
    # 生成目录
    for etype, items in sorted(by_type.items()):
        index_content += f"### {etype}\n\n"
        for item in sorted(items, key=lambda x: x.get('name', '')):
            name = item.get('name', item.get('id'))
            entity_id = item.get('id')
            desc = item.get('description', '')[:50]
            index_content += f"- [{name}](entities/{entity_id}.md) - {desc}...\n"
        index_content += "\n"
    
    index_content += f"""## 统计

- 总实体数: {len(entities)}
- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 综合

- [综合总结](synthesis.md)
- [变更日志](log.md)
"""
    
    (wiki_dir / "index.md").write_text(index_content)


def main():
    """主函数: 导出所有 YAML 到 wiki."""
    content_dir = Path("content")
    wiki_dir = Path("wiki")
    
    # 收集所有实体
    entities = []
    
    for yaml_file in content_dir.rglob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if data:
            entities.append(data)
            export_entity_to_wiki(yaml_file, wiki_dir / "entities")
    
    # 更新索引
    update_index(wiki_dir, entities)
    
    print(f"✅ 导出完成: {len(entities)} 个实体到 wiki/")


if __name__ == "__main__":
    main()
```

## 实施优先级

### 高优先级 (立即实施)

1. **创建 wiki/ 目录结构**
2. **编写 yaml_to_wiki.py 导出脚本**
3. **更新 AGENTS.md 添加 wiki 维护指南**
4. **创建 index.md 和 synthesis.md**

### 中优先级 (近期实施)

5. **添加 log.md 和变更追踪**
6. **集成到 CI/CD 自动导出**
7. **添加交叉引用生成**
8. **创建 lint 检查脚本**

### 低优先级 (未来扩展)

9. **集成 Obsidian 插件支持**
10. **添加 qmd 搜索工具**
11. **创建 MCP server 集成**
12. **添加 Marp 幻灯片导出**

## 预期效果

实施 llm-wiki 模式后：

1. **LLM 可读性提升**: Markdown 比 YAML 更适合 LLM 理解和引用
2. **交叉引用增强**: 自动链接相关实体，构建知识网络
3. **维护自动化**: 监听 YAML 变更自动更新 wiki
4. **人机协作优化**: 人类编辑 YAML，LLM 维护 wiki 叙事
5. **Obsidian 集成**: 可直接在 Obsidian 中浏览和编辑

## 参考实现

- Karpathy llm-wiki: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- llm-wiki-kit MCP server: https://github.com/iamsashank09/llm-wiki-kit
