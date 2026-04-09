#!/usr/bin/env python3
"""服务器初始化脚本 - 构建必要的存储文件"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def setup_kb(kb_id='omics'):
    """Setup knowledge base with memory store."""
    from kb_manager import KnowledgeBaseManager
    from memory_core.memory_store import MemoryStore
    
    kb_manager = KnowledgeBaseManager()
    
    # Create KB if not exists
    if not kb_manager.get_kb(kb_id):
        print(f"Creating KB: {kb_id}")
        kb_manager.create_kb(
            kb_id=kb_id,
            name="多组学分析",
            description="多组学数据分析知识库",
            color="#3b82f6"
        )
    
    # Build memory store from content
    content_dir = kb_manager.get_kb_content_dir(kb_id)
    memory_dir = kb_manager.get_kb_memory_dir(kb_id)
    
    if content_dir.exists():
        print(f"Building memory store from {content_dir}")
        try:
            from scripts.yaml_to_memory import build_memory_store
            build_memory_store(content_dir, memory_dir)
            print(f"✓ Memory store built at {memory_dir}")
        except Exception as e:
            print(f"Error building memory store: {e}")
            # Create empty store
            store = MemoryStore(embedding_dim=384)
            store.save(memory_dir)
            print(f"✓ Empty memory store created at {memory_dir}")
    else:
        print(f"Content directory not found: {content_dir}")

if __name__ == '__main__':
    setup_kb()
