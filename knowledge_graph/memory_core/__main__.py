#!/usr/bin/env python3
"""
Main entry point for memory_core module.
Usage: python -m memory_core [command]
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(
        description='Knowledge Graph Memory Store',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  build     Build memory store from YAML content
  query     Interactive query interface
  server    Start API server
  stats     Show memory store statistics

Examples:
  python -m memory_core build
  python -m memory_core query
  python -m memory_core server --port 8000
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build memory store')
    build_parser.add_argument('--content', type=Path, default=Path('content'))
    build_parser.add_argument('--edges', type=Path, default=Path('edges/edges.yaml'))
    build_parser.add_argument('--output', type=Path, default=Path('memory_store'))
    build_parser.add_argument('--model', default='all-MiniLM-L6-v2')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Interactive query')
    query_parser.add_argument('--store', type=Path, default=Path('memory_store'))
    query_parser.add_argument('--model', default='all-MiniLM-L6-v2')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start API server')
    server_parser.add_argument('--store', type=Path, default=Path('memory_store'))
    server_parser.add_argument('--port', '-p', type=int, default=8000)
    server_parser.add_argument('--model', default='all-MiniLM-L6-v2')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('--store', type=Path, default=Path('memory_store'))
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    if args.command == 'build':
        from memory_core.memory_builder import build_memory_store
        store = build_memory_store(
            content_dir=args.content,
            edges_file=args.edges,
            output_dir=args.output,
            model_name=args.model
        )
        print(f"\n✅ Build complete! {len(store)} items in memory store.")
    
    elif args.command == 'query':
        from memory_core.query import MemoryQuery, interactive_search
        if not args.store.exists():
            print(f"❌ Memory store not found at {args.store}")
            print("Run: python -m memory_core build")
            sys.exit(1)
        query_interface = MemoryQuery(args.store, args.model)
        interactive_search(query_interface)
    
    elif args.command == 'server':
        from memory_core.server import run_server
        if not args.store.exists():
            print(f"❌ Memory store not found at {args.store}")
            print("Run: python -m memory_core build")
            sys.exit(1)
        run_server(args.store, args.port, args.model)
    
    elif args.command == 'stats':
        from memory_core.memory_store import MemoryStore
        if not args.store.exists():
            print(f"❌ Memory store not found at {args.store}")
            sys.exit(1)
        store = MemoryStore.load(args.store)
        
        # Count by type
        type_counts = {}
        for item in store:
            et = item.metadata.get('entity_type', 'unknown')
            type_counts[et] = type_counts.get(et, 0) + 1
        
        print("\n📊 Memory Store Statistics")
        print("=" * 40)
        print(f"Total items: {len(store)}")
        print(f"Embedding dim: {store.embedding_dim}")
        print("\nBy entity type:")
        for et, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {et:12s}: {count:4d}")
        print()


if __name__ == '__main__':
    main()
