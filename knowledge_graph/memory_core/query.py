#!/usr/bin/env python3
"""
Query interface for memory store.
Simple CLI for semantic search.
"""

import sys
import json
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_core.memory_store import MemoryStore
from memory_core.embedder import Embedder


class MemoryQuery:
    """High-level query interface for memory store."""
    
    def __init__(self, store_dir: Path, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize query interface.
        
        Args:
            store_dir: Directory containing saved memory store
            model_name: Model name for query embedding
        """
        self.store = MemoryStore.load(store_dir)
        self.embedder = Embedder(model_name)
        print(f"Loaded memory store with {len(self.store)} items")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        entity_type: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[dict]:
        """Search memory store by text query.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            entity_type: Filter by entity type (e.g., 'tool', 'concept')
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of result dictionaries
        """
        # Build filter function
        filter_fn = None
        if entity_type:
            filter_fn = lambda item: item.metadata.get('entity_type') == entity_type
        
        # Query
        results = self.store.query_by_text(
            self.embedder,
            query,
            top_k=top_k * 2,  # Get more for filtering
            filter_fn=filter_fn
        )
        
        # Format results
        formatted = []
        for item, score in results:
            if score >= min_score:
                formatted.append({
                    'id': item.id,
                    'name': item.metadata.get('name', item.id),
                    'entity_type': item.metadata.get('entity_type'),
                    'score': round(score, 4),
                    'text': item.text[:500] + '...' if len(item.text) > 500 else item.text,
                    'tags': item.metadata.get('tags', []),
                    'difficulty': item.metadata.get('difficulty')
                })
        
        return formatted[:top_k]
    
    def get(self, entity_id: str) -> Optional[dict]:
        """Get entity by ID."""
        item = self.store.get(entity_id)
        if not item:
            return None
        
        return {
            'id': item.id,
            'name': item.metadata.get('name', item.id),
            'entity_type': item.metadata.get('entity_type'),
            'text': item.text,
            'tags': item.metadata.get('tags', []),
            'difficulty': item.metadata.get('difficulty'),
            'metadata': item.metadata
        }
    
    def get_related(self, entity_id: str, top_k: int = 5) -> List[dict]:
        """Find entities related to given entity by semantic similarity."""
        item = self.store.get(entity_id)
        if not item or item.embedding is None:
            return []
        
        # Query excluding self
        results = self.store.query(item.embedding, top_k=top_k + 1)
        return [
            {
                'id': r.id,
                'name': r.metadata.get('name', r.id),
                'entity_type': r.metadata.get('entity_type'),
                'score': round(score, 4)
            }
            for r, score in results 
            if r.id != entity_id
        ][:top_k]


def interactive_search(query_interface: MemoryQuery):
    """Run interactive search loop."""
    print("\n" + "="*60)
    print("Knowledge Graph Memory Search")
    print("="*60)
    print("Type your query to search, or 'quit' to exit")
    print("Special commands:")
    print("  :type <type>    - Filter by entity type (tool, concept, etc.)")
    print("  :get <id>       - Get entity by ID")
    print("  :related <id>   - Find related entities")
    print("  :help           - Show this help")
    print("="*60 + "\n")
    
    current_filter = None
    
    while True:
        try:
            query = input(f"\n[filter: {current_filter or 'none'}] > ").strip()
            
            if not query:
                continue
            
            if query.lower() == 'quit':
                break
            
            if query.lower() == ':help':
                print("Special commands:")
                print("  :type <type>    - Filter by entity type")
                print("  :get <id>       - Get entity by ID")
                print("  :related <id>   - Find related entities")
                continue
            
            if query.startswith(':type '):
                current_filter = query[6:].strip() or None
                print(f"Filter set to: {current_filter}")
                continue
            
            if query.startswith(':get '):
                entity_id = query[5:].strip()
                result = query_interface.get(entity_id)
                if result:
                    print(f"\n[{result['id']}] {result['name']}")
                    print(f"Type: {result['entity_type']}")
                    print(f"Tags: {', '.join(result['tags'])}")
                    print(f"\n{result['text']}")
                else:
                    print(f"Entity '{entity_id}' not found")
                continue
            
            if query.startswith(':related '):
                entity_id = query[9:].strip()
                related = query_interface.get_related(entity_id)
                print(f"\nEntities related to '{entity_id}':")
                for r in related:
                    print(f"  [{r['score']:.3f}] {r['name']} ({r['entity_type']})")
                continue
            
            # Regular search
            results = query_interface.search(query, entity_type=current_filter)
            
            if not results:
                print("No results found")
                continue
            
            print(f"\nTop {len(results)} results for: '{query}'")
            print("-" * 60)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. [{r['score']:.3f}] {r['name']} ({r['entity_type']})")
                print(f"   ID: {r['id']}")
                if r['tags']:
                    print(f"   Tags: {', '.join(r['tags'])}")
                print(f"   {r['text'][:200]}...")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Query memory store')
    parser.add_argument('--store', type=Path, default=Path('memory_store'),
                       help='Memory store directory (default: memory_store)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                       help='Sentence transformer model')
    parser.add_argument('--query', '-q', type=str,
                       help='Single query (if not provided, enters interactive mode)')
    parser.add_argument('--type', type=str,
                       help='Filter by entity type')
    parser.add_argument('-k', type=int, default=5,
                       help='Number of results (default: 5)')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    if args.store == Path('memory_store'):
        args.store = project_root / 'memory_store'
    
    if not args.store.exists():
        print(f"Error: Memory store not found at {args.store}")
        print("Run 'python -m memory_core.memory_builder' first")
        sys.exit(1)
    
    query_interface = MemoryQuery(args.store, args.model)
    
    if args.query:
        # Single query mode
        results = query_interface.search(args.query, top_k=args.k, entity_type=args.type)
        
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\nQuery: '{args.query}'")
            if args.type:
                print(f"Filter: type={args.type}")
            print("-" * 60)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. [{r['score']:.3f}] {r['name']} ({r['entity_type']})")
                print(f"   ID: {r['id']}")
                print(f"   {r['text'][:300]}...")
    else:
        # Interactive mode
        interactive_search(query_interface)


if __name__ == '__main__':
    main()
