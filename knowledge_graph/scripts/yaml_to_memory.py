#!/usr/bin/env python3
"""
yaml_to_memory.py - 将 YAML 内容构建为向量记忆存储

Usage:
    python scripts/yaml_to_memory.py [content_dir] [memory_dir]
    python scripts/yaml_to_memory.py                      # 使用默认目录
    python scripts/yaml_to_memory.py ./content ./memory_store
"""

import sys
import yaml
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_core.memory_store import MemoryStore, MemoryItem
from memory_core.embedder import Embedder


def load_yaml_entities(content_dir: Path) -> List[Dict[str, Any]]:
    """加载所有 YAML 实体."""
    entities = []
    
    if not content_dir.exists():
        print(f"❌ 内容目录不存在: {content_dir}")
        return entities
    
    for yaml_file in content_dir.rglob("*.yaml"):
        if yaml_file.name == "edges.yaml":
            continue
            
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and isinstance(data, dict):
                    data['_source_file'] = str(yaml_file.relative_to(content_dir))
                    entities.append(data)
        except Exception as e:
            print(f"⚠️  跳过 {yaml_file}: {e}")
    
    return entities


def build_memory_store(content_dir: Path, memory_dir: Path, model_name: str = "all-MiniLM-L6-v2"):
    """构建向量记忆存储."""
    print(f"📂 加载实体 from {content_dir}...")
    entities = load_yaml_entities(content_dir)
    print(f"✓ 加载了 {len(entities)} 个实体")
    
    if not entities:
        print("⚠️  没有实体需要处理")
        # 创建空的 memory store
        store = MemoryStore(embedding_dim=384)
        store.save(memory_dir)
        return
    
    print(f"🧠 初始化 embedder ({model_name})...")
    embedder = Embedder(model_name)
    
    print("📊 准备文本和元数据...")
    texts = []
    metadata_list = []
    entity_ids = []
    
    for i, entity in enumerate(entities, 1):
        entity_id = entity.get('id', f'entity_{i}')
        entity_type = entity.get('type', 'unknown')
        name = entity.get('name', entity_id)
        description = entity.get('description', '')
        detailed = entity.get('detailed_explanation', '')
        
        # 组合文本用于嵌入
        text_parts = [f"{name}", f"类型: {entity_type}"]
        if description:
            text_parts.append(description)
        if detailed:
            text_parts.append(detailed[:2000])  # 限制长度
        
        text = '\n\n'.join(text_parts)
        
        # 准备元数据
        metadata = {
            'name': name,
            'entity_type': entity_type,
            'tags': entity.get('tags', []),
            'difficulty': entity.get('difficulty', 'unknown'),
            'source_file': entity.get('_source_file', ''),
            'original_data': {k: v for k, v in entity.items() if not k.startswith('_')}
        }
        
        texts.append(text)
        metadata_list.append(metadata)
        entity_ids.append(entity_id)
        
        if i % 10 == 0:
            print(f"  已准备 {i}/{len(entities)}...")
    
    print(f"🔢 生成向量嵌入 ({len(texts)} 个实体)...")
    embeddings = embedder.embed_batch(texts)
    
    print("📦 创建 memory store...")
    store = MemoryStore(embedding_dim=embedder.embedding_dim)
    
    # 创建 MemoryItem 并添加到 store
    for i, (entity_id, text, metadata, embedding) in enumerate(zip(entity_ids, texts, metadata_list, embeddings)):
        item = MemoryItem(
            id=entity_id,
            text=text,
            embedding=embedding,
            metadata=metadata
        )
        store.add(item)
        
        if (i + 1) % 10 == 0:
            print(f"  已添加 {i + 1}/{len(texts)}...")
    
    print(f"💾 保存到 {memory_dir}...")
    store.save(memory_dir)
    
    print(f"✅ 完成！共 {len(store)} 个实体，维度 {store.embedding_dim}")


def main():
    """命令行入口."""
    import argparse
    
    parser = argparse.ArgumentParser(description='构建 YAML 到向量记忆存储')
    parser.add_argument('content_dir', nargs='?', default='content', help='YAML 内容目录 (默认: content)')
    parser.add_argument('memory_dir', nargs='?', default='memory_store', help='记忆存储目录 (默认: memory_store)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2', help='嵌入模型名称')
    
    args = parser.parse_args()
    
    content_dir = Path(args.content_dir)
    memory_dir = Path(args.memory_dir)
    
    build_memory_store(content_dir, memory_dir, args.model)


if __name__ == '__main__':
    main()
