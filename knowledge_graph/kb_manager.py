#!/usr/bin/env python3
"""
Knowledge Base Manager - 多知识库管理器

支持创建、切换、管理多个独立的知识库
"""

import json
import shutil
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


@dataclass
class KnowledgeBase:
    """知识库定义"""
    id: str                          # 唯一标识
    name: str                        # 显示名称
    description: str                 # 描述
    created_at: str                  # 创建时间
    updated_at: str                  # 更新时间
    entity_count: int = 0            # 实体数量
    icon: str = "📚"                 # 图标 (可自定义)
    color: str = "#3b82f6"           # 主题色
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeBase':
        return cls(**data)


class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).parent
        self.kb_root = self.root_dir / "kb"
        self.kb_root.mkdir(exist_ok=True)
        
        # 全局配置文件
        self.global_config_file = self.root_dir / ".kb_config.json"
        
        # 初始化默认知识库（多组学）
        self._init_default_kb()
    
    def _init_default_kb(self):
        """初始化默认知识库"""
        if not self.get_kb("omics"):
            self.create_kb(
                kb_id="omics",
                name="多组学分析",
                description="多组学数据分析知识库（CUT&Tag、ATAC-seq、scRNA-seq、Hi-C 等）",
                color="#3b82f6"
            )
            # 迁移旧数据到 omics 知识库
            self._migrate_legacy_data()
    
    def _migrate_legacy_data(self):
        """迁移旧数据到默认知识库"""
        omics_dir = self.kb_root / "omics"
        
        # 需要迁移的目录
        legacy_dirs = {
            "content": self.root_dir / "content",
            "wiki": self.root_dir / "wiki",
            "memory_store": self.root_dir / "memory_store",
        }
        
        for name, src_path in legacy_dirs.items():
            if src_path.exists() and any(src_path.iterdir()):
                dst_path = omics_dir / name
                if not dst_path.exists():
                    print(f"Migrating {name} to omics knowledge base...")
                    shutil.copytree(src_path, dst_path)
    
    def get_kb_dir(self, kb_id: str) -> Path:
        """获取知识库目录"""
        return self.kb_root / kb_id
    
    def get_kb_config_file(self, kb_id: str) -> Path:
        """获取知识库配置文件路径"""
        return self.get_kb_dir(kb_id) / "config.yaml"
    
    def create_kb(self, kb_id: str, name: str, description: str = "", 
                  icon: str = "📚", color: str = "#3b82f6") -> KnowledgeBase:
        """创建新知识库"""
        # 验证 ID
        if not self._validate_kb_id(kb_id):
            raise ValueError(f"Invalid knowledge base ID: {kb_id}. Use lowercase letters, numbers, and hyphens only.")
        
        kb_dir = self.get_kb_dir(kb_id)
        if kb_dir.exists():
            raise ValueError(f"Knowledge base '{kb_id}' already exists")
        
        # 创建目录结构
        now = datetime.now().isoformat()
        kb = KnowledgeBase(
            id=kb_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            icon=icon,
            color=color
        )
        
        # 创建子目录
        (kb_dir / "content").mkdir(parents=True)
        (kb_dir / "content" / "assays").mkdir()
        (kb_dir / "content" / "tools").mkdir()
        (kb_dir / "content" / "steps").mkdir()
        (kb_dir / "content" / "concepts").mkdir()
        (kb_dir / "content" / "stages").mkdir()
        (kb_dir / "content" / "issues").mkdir()
        (kb_dir / "content" / "resources").mkdir()
        (kb_dir / "wiki").mkdir()
        (kb_dir / "memory_store").mkdir()
        (kb_dir / "web" / "data").mkdir(parents=True)
        
        # 保存配置
        self._save_kb_config(kb)
        
        # 创建默认 edges.yaml
        edges_file = kb_dir / "content" / "edges.yaml"
        edges_file.write_text("edges: []\n", encoding='utf-8')
        
        return kb
    
    def delete_kb(self, kb_id: str) -> bool:
        """删除知识库"""
        if kb_id == "omics":
            raise ValueError("Cannot delete default 'omics' knowledge base")
        
        kb_dir = self.get_kb_dir(kb_id)
        if kb_dir.exists():
            shutil.rmtree(kb_dir)
            
            # 如果删除的是当前选中的知识库，重置为默认
            current = self.get_current_kb()
            if current and current.id == kb_id:
                self.set_current_kb("omics")
            
            return True
        return False
    
    def list_kbs(self) -> List[KnowledgeBase]:
        """列出所有知识库"""
        kbs = []
        for kb_dir in self.kb_root.iterdir():
            if kb_dir.is_dir():
                config_file = kb_dir / "config.yaml"
                if config_file.exists():
                    try:
                        kb = self._load_kb_config(kb_dir.name)
                        # 更新实体数量
                        kb.entity_count = self._count_entities(kb.id)
                        kbs.append(kb)
                    except Exception as e:
                        print(f"Error loading KB {kb_dir.name}: {e}")
        
        # 按创建时间排序
        kbs.sort(key=lambda x: x.created_at)
        return kbs
    
    def get_kb(self, kb_id: str) -> Optional[KnowledgeBase]:
        """获取知识库信息"""
        kb_dir = self.get_kb_dir(kb_id)
        if not kb_dir.exists():
            return None
        
        try:
            kb = self._load_kb_config(kb_id)
            kb.entity_count = self._count_entities(kb.id)
            return kb
        except Exception:
            return None
    
    def update_kb(self, kb_id: str, **kwargs) -> KnowledgeBase:
        """更新知识库信息"""
        kb = self.get_kb(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base '{kb_id}' not found")
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(kb, key) and key != 'id':
                setattr(kb, key, value)
        
        kb.updated_at = datetime.now().isoformat()
        self._save_kb_config(kb)
        
        return kb
    
    def get_current_kb(self) -> Optional[KnowledgeBase]:
        """获取当前选中的知识库"""
        try:
            if self.global_config_file.exists():
                config = json.loads(self.global_config_file.read_text())
                kb_id = config.get('current_kb', 'omics')
                return self.get_kb(kb_id)
        except Exception:
            pass
        return self.get_kb('omics')
    
    def set_current_kb(self, kb_id: str):
        """设置当前知识库"""
        kb = self.get_kb(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base '{kb_id}' not found")
        
        config = {'current_kb': kb_id}
        self.global_config_file.write_text(json.dumps(config, indent=2))
    
    def get_kb_content_dir(self, kb_id: str) -> Path:
        """获取知识库 content 目录"""
        return self.get_kb_dir(kb_id) / "content"
    
    def get_kb_wiki_dir(self, kb_id: str) -> Path:
        """获取知识库 wiki 目录"""
        return self.get_kb_dir(kb_id) / "wiki"
    
    def get_kb_memory_dir(self, kb_id: str) -> Path:
        """获取知识库 memory_store 目录"""
        return self.get_kb_dir(kb_id) / "memory_store"
    
    def get_kb_web_data_dir(self, kb_id: str) -> Path:
        """获取知识库 web/data 目录"""
        return self.get_kb_dir(kb_id) / "web" / "data"
    
    def export_kb_data(self, kb_id: str) -> Dict[str, Any]:
        """导出知识库数据（用于前端）"""
        kb = self.get_kb(kb_id)
        if not kb:
            return {}
        
        return {
            'kb': kb.to_dict(),
            'paths': {
                'content': str(self.get_kb_content_dir(kb_id)),
                'wiki': str(self.get_kb_wiki_dir(kb_id)),
                'memory': str(self.get_kb_memory_dir(kb_id)),
                'web_data': str(self.get_kb_web_data_dir(kb_id)),
            }
        }
    
    def _validate_kb_id(self, kb_id: str) -> bool:
        """验证知识库 ID"""
        import re
        return bool(re.match(r'^[a-z][a-z0-9-]*$', kb_id))
    
    def _load_kb_config(self, kb_id: str) -> KnowledgeBase:
        """加载知识库配置"""
        config_file = self.get_kb_config_file(kb_id)
        data = yaml.safe_load(config_file.read_text())
        return KnowledgeBase.from_dict(data)
    
    def _save_kb_config(self, kb: KnowledgeBase):
        """保存知识库配置"""
        config_file = self.get_kb_config_file(kb.id)
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(kb.to_dict(), f, allow_unicode=True, sort_keys=False)
    
    def _count_entities(self, kb_id: str) -> int:
        """统计知识库实体数量"""
        content_dir = self.get_kb_content_dir(kb_id)
        if not content_dir.exists():
            return 0
        
        count = 0
        for yaml_file in content_dir.rglob("*.yaml"):
            if yaml_file.name != "edges.yaml":
                count += 1
        return count


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Base Manager")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new knowledge base')
    create_parser.add_argument('id', help='Knowledge base ID (lowercase, numbers, hyphens)')
    create_parser.add_argument('name', help='Knowledge base name')
    create_parser.add_argument('--description', '-d', default='', help='Description')
    create_parser.add_argument('--color', '-c', default='#3b82f6', help='Theme color')
    
    # List command
    subparsers.add_parser('list', help='List all knowledge bases')
    
    # Switch command
    switch_parser = subparsers.add_parser('switch', help='Switch current knowledge base')
    switch_parser.add_argument('id', help='Knowledge base ID')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a knowledge base')
    delete_parser.add_argument('id', help='Knowledge base ID')
    
    # Current command
    subparsers.add_parser('current', help='Show current knowledge base')
    
    args = parser.parse_args()
    
    manager = KnowledgeBaseManager()
    
    if args.command == 'create':
        try:
            kb = manager.create_kb(args.id, args.name, args.description, color=args.color)
            print(f"Created knowledge base: {kb.name} ({kb.id})")
            print(f"Location: {manager.get_kb_dir(kb.id)}")
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    
    elif args.command == 'list':
        kbs = manager.list_kbs()
        current = manager.get_current_kb()
        
        print(f"{'ID':<15} {'Name':<20} {'Entities':<10} {'Description'}")
        print("-" * 80)
        for kb in kbs:
            marker = "* " if current and kb.id == current.id else "  "
            print(f"{marker}{kb.id:<13} {kb.name:<20} {kb.entity_count:<10} {kb.description[:40]}...")
        print("\n* = current knowledge base")
    
    elif args.command == 'switch':
        try:
            manager.set_current_kb(args.id)
            kb = manager.get_current_kb()
            print(f"Switched to: {kb.name} ({kb.id})")
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    
    elif args.command == 'delete':
        try:
            if input(f"Are you sure you want to delete '{args.id}'? This cannot be undone. [y/N] ").lower() == 'y':
                if manager.delete_kb(args.id):
                    print(f"Deleted knowledge base: {args.id}")
                else:
                    print(f"Knowledge base not found: {args.id}")
            else:
                print("Cancelled")
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    
    elif args.command == 'current':
        kb = manager.get_current_kb()
        if kb:
            print(f"Current knowledge base: {kb.name} ({kb.id})")
            print(f"Location: {manager.get_kb_dir(kb.id)}")
            print(f"Entities: {kb.entity_count}")
        else:
            print("No knowledge base selected")
    
    else:
        parser.print_help()
    
    return 0


if __name__ == '__main__':
    exit(main())
