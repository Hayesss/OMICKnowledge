#!/usr/bin/env python3
"""
yaml_to_wiki.py - 将 YAML 内容导出为 Markdown wiki

遵循 llm-wiki 模式 (Karpathy):
- 保持 YAML 为原始源文件 (Raw Sources)
- 生成 Markdown 便于 LLM 阅读和交叉引用 (The Wiki)
- 维护 index.md 和 log.md
- 支持增量更新

Usage:
    python scripts/yaml_to_wiki.py              # 导出所有实体
    python scripts/yaml_to_wiki.py --watch      # 监听变更自动更新
    python scripts/yaml_to_wiki.py --entity bowtie2  # 导出单个实体
"""

import yaml
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class Entity:
    """知识图谱实体."""
    id: str
    name: str
    entity_type: str
    description: str
    data: Dict
    source_file: Path
    
    @property
    def tags(self) -> List[str]:
        return self.data.get('tags', [])
    
    @property
    def difficulty(self) -> str:
        return self.data.get('difficulty', 'unknown')
    
    @property
    def detailed_explanation(self) -> str:
        return self.data.get('detailed_explanation', '')


class WikiExporter:
    """Wiki 导出器."""
    
    def __init__(self, content_dir: Path, wiki_dir: Path):
        self.content_dir = content_dir
        self.wiki_dir = wiki_dir
        self.entities: Dict[str, Entity] = {}
        self.edges: List[Dict] = []
        
    def load_entities(self) -> Dict[str, Entity]:
        """加载所有 YAML 实体."""
        entities = {}
        
        for yaml_file in self.content_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if not data or not isinstance(data, dict):
                    continue
                
                entity_id = data.get('id')
                if not entity_id:
                    continue
                
                entity_type = yaml_file.parent.name
                
                entity = Entity(
                    id=entity_id,
                    name=data.get('name', entity_id),
                    entity_type=entity_type,
                    description=data.get('description', ''),
                    data=data,
                    source_file=yaml_file
                )
                entities[entity_id] = entity
                
            except Exception as e:
                print(f"⚠️  加载失败 {yaml_file}: {e}")
        
        self.entities = entities
        return entities
    
    def load_edges(self) -> List[Dict]:
        """加载关系定义."""
        edges_file = self.content_dir.parent / "edges" / "edges.yaml"
        
        if not edges_file.exists():
            return []
        
        try:
            with open(edges_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            self.edges = data.get('edges', []) if data else []
            return self.edges
        except Exception as e:
            print(f"⚠️  加载 edges 失败: {e}")
            return []
    
    def get_related_entities(self, entity_id: str) -> List[Dict]:
        """获取与指定实体相关的其他实体."""
        related = []
        
        for edge in self.edges:
            if edge.get('source') == entity_id:
                target = edge.get('target')
                if target in self.entities:
                    related.append({
                        'entity': self.entities[target],
                        'relation': edge.get('relation', 'related'),
                        'direction': 'outgoing'
                    })
            elif edge.get('target') == entity_id:
                source = edge.get('source')
                if source in self.entities:
                    related.append({
                        'entity': self.entities[source],
                        'relation': edge.get('relation', 'related'),
                        'direction': 'incoming'
                    })
        
        return related
    
    def generate_entity_page(self, entity: Entity) -> str:
        """生成实体 Markdown 页面."""
        
        # 获取相关实体
        related = self.get_related_entities(entity.id)
        
        # 构建 Markdown
        md = f"""# {entity.name}

## 基本信息

- **ID**: `{entity.id}`
- **类型**: {entity.entity_type}
- **难度**: {entity.difficulty}
- **标签**: {', '.join(f'`{t}`' for t in entity.tags) if entity.tags else '无'}

## 描述

{entity.description}

"""
        
        # 添加详细说明
        if entity.detailed_explanation:
            md += f"""## 详细说明

{entity.detailed_explanation}

"""
        
        # 添加关键参数（工具/步骤特有）
        if 'key_params' in entity.data and entity.data['key_params']:
            md += """## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
"""
            for param in entity.data['key_params']:
                name = param.get('name', '')
                desc = param.get('description', '')
                default = param.get('default', '')
                md += f"| `{name}` | {desc} | {default} |\n"
            md += "\n"
        
        # 添加输入输出（步骤特有）
        if 'input' in entity.data:
            md += f"""## 输入输出

- **输入**: {entity.data['input']}
- **输出**: {entity.data['output']}

"""
        
        # 添加相关实体
        if related:
            md += """## 相关实体

"""
            # 按关系类型分组
            by_relation = {}
            for r in related:
                rel_type = r['relation']
                by_relation.setdefault(rel_type, []).append(r)
            
            for rel_type, items in sorted(by_relation.items()):
                md += f"### {rel_type}\n\n"
                for item in items:
                    ent = item['entity']
                    direction = "→" if item['direction'] == 'outgoing' else "←"
                    md += f"- {direction} [{ent.name}]({ent.id}.md) - {ent.description[:50]}...\n"
                md += "\n"
        
        # 添加元信息
        md += f"""## 元信息

- **来源文件**: `{entity.source_file}`
- **最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

*本页面由 llm-wiki 系统自动生成，保持与 YAML 源文件同步*
"""
        
        return md
    
    def export_entity(self, entity_id: str) -> Optional[Path]:
        """导出单个实体到 wiki."""
        if entity_id not in self.entities:
            print(f"⚠️  实体不存在: {entity_id}")
            return None
        
        entity = self.entities[entity_id]
        md_content = self.generate_entity_page(entity)
        
        # 确定输出目录
        output_dir = self.wiki_dir / entity.entity_type
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        output_file = output_dir / f"{entity.id}.md"
        output_file.write_text(md_content, encoding='utf-8')
        
        return output_file
    
    def export_all(self) -> int:
        """导出所有实体."""
        print("🔄 加载实体...")
        self.load_entities()
        print(f"✓ 加载了 {len(self.entities)} 个实体")
        
        print("🔄 加载关系...")
        self.load_edges()
        print(f"✓ 加载了 {len(self.edges)} 条关系")
        
        print("🔄 导出实体页面...")
        count = 0
        for entity_id in self.entities:
            output_file = self.export_entity(entity_id)
            if output_file:
                count += 1
        
        print(f"✓ 导出了 {count} 个实体页面")
        return count
    
    def update_index(self) -> Path:
        """更新 wiki/index.md 目录索引."""
        
        index_content = f"""# 多组学知识图谱索引

*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

本索引遵循 [llm-wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 构建，用于 LLM 快速定位和交叉引用知识实体。

## 概览

本项目涵盖四种组学技术（CUT&Tag、ATAC-seq、scRNA-seq、Hi-C）的分析流程、工具、概念和最佳实践。

## 实体列表

"""
        
        # 按类型分组统计
        by_type: Dict[str, List[Entity]] = {}
        for entity in self.entities.values():
            etype = entity.entity_type
            by_type.setdefault(etype, []).append(entity)
        
        # 生成各类别索引
        type_order = ['assays', 'tools', 'steps', 'concepts', 'stages', 'issues', 'resources']
        type_names = {
            'assays': '实验类型 (Assays)',
            'tools': '分析工具 (Tools)',
            'steps': '分析步骤 (Steps)',
            'concepts': '关键概念 (Concepts)',
            'stages': '分析阶段 (Stages)',
            'issues': '常见问题 (Issues)',
            'resources': '外部资源 (Resources)'
        }
        
        for etype in type_order:
            if etype not in by_type:
                continue
            
            items = sorted(by_type[etype], key=lambda x: x.name)
            type_name = type_names.get(etype, etype)
            
            index_content += f"### {type_name}\n\n"
            index_content += f"*{len(items)} 个实体*\n\n"
            
            for entity in items:
                desc = entity.description[:60] + "..." if len(entity.description) > 60 else entity.description
                index_content += f"- [{entity.name}]({etype}/{entity.id}.md) - {desc}\n"
            
            index_content += "\n"
        
        # 添加统计
        index_content += f"""## 统计

- 总实体数: {len(self.entities)}
- 关系数: {len(self.edges)}
- 最后导出: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 导航

- [综合总结](synthesis.md) - 跨实体知识综合
- [变更日志](log.md) - 知识库演进历史
- [项目 README](../README.md) - 项目概述

## 如何使用

作为 LLM，你可以：

1. **查询**: 先阅读此索引找到相关实体，再深入阅读实体页面
2. **关联**: 通过页面内的交叉引用发现相关知识
3. **综合**: 基于多个实体信息生成综合回答
4. **维护**: 协助更新 wiki 页面，保持与 YAML 源文件同步

---

*本索引由 llm-wiki 系统自动生成*
"""
        
        # 写入文件
        index_file = self.wiki_dir / "index.md"
        index_file.write_text(index_content, encoding='utf-8')
        
        print(f"✓ 更新索引: {index_file}")
        return index_file
    
    def init_log(self) -> Path:
        """初始化 wiki/log.md 变更日志."""
        
        log_content = f"""# 知识图谱变更日志

*遵循 llm-wiki 模式，记录知识库的演进历史*

## 格式说明

每行记录格式: `## [YYYY-MM-DD] action | description`

- **ingest**: 新增/更新内容
- **query**: 查询/分析产生的新见解
- **lint**: 健康检查/维护

---

## [2026-04-07] ingest | 初始化 llm-wiki 系统

- 创建 wiki 目录结构
- 导出 27 个实体页面
- 建立交叉引用系统
- 生成目录索引

---

*使用 `grep "^## \\[" wiki/log.md` 查看最新变更*
"""
        
        log_file = self.wiki_dir / "log.md"
        
        # 如果日志已存在，保留已有内容
        if log_file.exists():
            existing = log_file.read_text(encoding='utf-8')
            if "初始化 llm-wiki 系统" not in existing:
                # 在头部插入新条目
                lines = existing.split('\n')
                # 找到第一个 ## [ 位置
                for i, line in enumerate(lines):
                    if line.startswith('## ['):
                        lines.insert(i, log_content.split('---')[1].strip())
                        break
                log_file.write_text('\n'.join(lines), encoding='utf-8')
        else:
            log_file.write_text(log_content, encoding='utf-8')
        
        print(f"✓ 初始化日志: {log_file}")
        return log_file


def main():
    parser = argparse.ArgumentParser(description='导出 YAML 到 Markdown Wiki')
    parser.add_argument('--entity', help='导出单个实体')
    parser.add_argument('--watch', action='store_true', help='监听变更自动更新')
    parser.add_argument('--content-dir', default='content', help='YAML 内容目录')
    parser.add_argument('--wiki-dir', default='wiki', help='Wiki 输出目录')
    
    args = parser.parse_args()
    
    content_dir = Path(args.content_dir)
    wiki_dir = Path(args.wiki_dir)
    
    if not content_dir.exists():
        print(f"❌ 内容目录不存在: {content_dir}")
        return 1
    
    wiki_dir.mkdir(parents=True, exist_ok=True)
    
    exporter = WikiExporter(content_dir, wiki_dir)
    
    if args.entity:
        # 导出单个实体
        exporter.load_entities()
        exporter.load_edges()
        output_file = exporter.export_entity(args.entity)
        if output_file:
            print(f"✓ 导出完成: {output_file}")
            exporter.update_index()
    elif args.watch:
        # 监听模式
        print("👀 监听模式启动...")
        # TODO: 实现文件监听
        print("(监听模式暂未实现，请使用 --entity 或默认导出全部)")
    else:
        # 导出全部
        count = exporter.export_all()
        exporter.update_index()
        exporter.init_log()
        print(f"\n🎉 完成! 共导出 {count} 个实体页面到 {wiki_dir}/")
    
    return 0


if __name__ == '__main__':
    exit(main())
