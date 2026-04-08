#!/usr/bin/env python3
"""
PDF Import Record Manager - 管理 PDF 导入记录

记录每个导入的 PDF 文件及其提取的实体，用于文献管理页面展示
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


@dataclass
class PDFImportRecord:
    """PDF 导入记录"""
    id: str                      # 唯一标识 (时间戳+随机数)
    filename: str                # 原始文件名
    kb_id: str                   # 目标知识库 ID
    imported_at: str             # 导入时间 ISO 格式
    entity_count: int            # 提取实体数量
    entities: List[Dict]         # 提取的实体列表 (简化信息)
    status: str                  # 状态: processing, completed, failed
    error_message: Optional[str] = None  # 错误信息


class PDFImportRecordManager:
    """PDF 导入记录管理器"""
    
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).parent.parent
        self.records_dir = self.root_dir / "kb" / ".import_records"
        self.records_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_record_file(self, kb_id: str) -> Path:
        """获取知识库的导入记录文件路径"""
        return self.records_dir / f"{kb_id}_imports.json"
    
    def add_record(self, record: PDFImportRecord) -> None:
        """添加新的导入记录"""
        records = self.get_records(record.kb_id)
        records.insert(0, record)  # 新记录在前
        self._save_records(record.kb_id, records)
    
    def update_record(self, kb_id: str, record_id: str, updates: Dict) -> Optional[PDFImportRecord]:
        """更新导入记录"""
        records = self.get_records(kb_id)
        for i, record in enumerate(records):
            if record.id == record_id:
                # 更新字段
                for key, value in updates.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                records[i] = record
                self._save_records(kb_id, records)
                return record
        return None
    
    def get_records(self, kb_id: str, limit: Optional[int] = None) -> List[PDFImportRecord]:
        """获取知识库的导入记录"""
        record_file = self._get_record_file(kb_id)
        if not record_file.exists():
            return []
        
        try:
            data = json.loads(record_file.read_text(encoding='utf-8'))
            records = [PDFImportRecord(**item) for item in data]
            if limit:
                records = records[:limit]
            return records
        except Exception as e:
            print(f"Error loading records: {e}")
            return []
    
    def get_record(self, kb_id: str, record_id: str) -> Optional[PDFImportRecord]:
        """获取单个导入记录"""
        records = self.get_records(kb_id)
        for record in records:
            if record.id == record_id:
                return record
        return None
    
    def delete_record(self, kb_id: str, record_id: str) -> bool:
        """删除导入记录"""
        records = self.get_records(kb_id)
        filtered = [r for r in records if r.id != record_id]
        if len(filtered) < len(records):
            self._save_records(kb_id, filtered)
            return True
        return False
    
    def _save_records(self, kb_id: str, records: List[PDFImportRecord]) -> None:
        """保存记录到文件"""
        record_file = self._get_record_file(kb_id)
        data = [asdict(r) for r in records]
        record_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def get_stats(self, kb_id: str) -> Dict[str, int]:
        """获取导入统计信息"""
        records = self.get_records(kb_id)
        return {
            'total_papers': len(records),
            'total_entities': sum(r.entity_count for r in records),
            'completed': len([r for r in records if r.status == 'completed']),
            'failed': len([r for r in records if r.status == 'failed'])
        }


def create_import_record(filename: str, kb_id: str, entities: List[Dict]) -> PDFImportRecord:
    """创建导入记录"""
    import uuid
    
    return PDFImportRecord(
        id=f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}",
        filename=filename,
        kb_id=kb_id,
        imported_at=datetime.now().isoformat(),
        entity_count=len(entities),
        entities=[{
            'id': e.get('id', ''),
            'name': e.get('name', ''),
            'type': e.get('type', 'unknown')
        } for e in entities],
        status='completed'
    )


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF Import Record Manager')
    parser.add_argument('command', choices=['list', 'stats', 'clear'])
    parser.add_argument('--kb', default='omics', help='Knowledge base ID')
    
    args = parser.parse_args()
    
    manager = PDFImportRecordManager()
    
    if args.command == 'list':
        records = manager.get_records(args.kb)
        print(f"Import records for KB '{args.kb}':")
        for r in records:
            print(f"  - {r.filename}: {r.entity_count} entities ({r.status})")
    
    elif args.command == 'stats':
        stats = manager.get_stats(args.kb)
        print(f"Stats for KB '{args.kb}':")
        print(f"  Total papers: {stats['total_papers']}")
        print(f"  Total entities: {stats['total_entities']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Failed: {stats['failed']}")
    
    elif args.command == 'clear':
        record_file = manager._get_record_file(args.kb)
        if record_file.exists():
            record_file.unlink()
            print(f"Cleared records for KB '{args.kb}'")
