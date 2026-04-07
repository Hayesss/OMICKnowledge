#!/usr/bin/env python3
"""
Simple HTTP API server for memory store.
Lightweight, no heavy frameworks needed.
"""

import json
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_core.memory_store import MemoryStore
from memory_core.embedder import Embedder


class MemoryAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for memory API."""
    
    store: MemoryStore = None
    embedder: Embedder = None
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def _send_json(self, data, status=200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _send_error(self, message, status=400):
        """Send error response."""
        self._send_json({'error': message}, status)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # Health check
        if path == '/health':
            self._send_json({
                'status': 'ok',
                'items': len(self.store)
            })
            return
        
        # Search endpoint
        if path == '/search':
            query = params.get('q', [''])[0]
            top_k = int(params.get('k', ['5'])[0])
            entity_type = params.get('type', [None])[0]
            
            if not query:
                self._send_error('Missing query parameter: q')
                return
            
            # Build filter
            filter_fn = None
            if entity_type:
                filter_fn = lambda item: item.metadata.get('entity_type') == entity_type
            
            # Search
            results = self.store.query_by_text(
                self.embedder, query, top_k=top_k, filter_fn=filter_fn
            )
            
            response = {
                'query': query,
                'results': [
                    {
                        'id': item.id,
                        'name': item.metadata.get('name', item.id),
                        'entity_type': item.metadata.get('entity_type'),
                        'score': round(score, 4),
                        'text': item.text[:500] + '...' if len(item.text) > 500 else item.text,
                        'tags': item.metadata.get('tags', []),
                        'difficulty': item.metadata.get('difficulty')
                    }
                    for item, score in results
                ]
            }
            self._send_json(response)
            return
        
        # Get entity by ID
        if path == '/entity':
            entity_id = params.get('id', [''])[0]
            if not entity_id:
                self._send_error('Missing parameter: id')
                return
            
            item = self.store.get(entity_id)
            if not item:
                self._send_error(f'Entity not found: {entity_id}', 404)
                return
            
            self._send_json({
                'id': item.id,
                'name': item.metadata.get('name', item.id),
                'entity_type': item.metadata.get('entity_type'),
                'text': item.text,
                'tags': item.metadata.get('tags', []),
                'difficulty': item.metadata.get('difficulty'),
                'metadata': item.metadata.get('original_data', {})
            })
            return
        
        # Get related entities
        if path == '/related':
            entity_id = params.get('id', [''])[0]
            top_k = int(params.get('k', ['5'])[0])
            
            if not entity_id:
                self._send_error('Missing parameter: id')
                return
            
            item = self.store.get(entity_id)
            if not item or item.embedding is None:
                self._send_error(f'Entity not found: {entity_id}', 404)
                return
            
            results = self.store.query(item.embedding, top_k=top_k + 1)
            related = [
                {
                    'id': r.id,
                    'name': r.metadata.get('name', r.id),
                    'entity_type': r.metadata.get('entity_type'),
                    'score': round(score, 4)
                }
                for r, score in results
                if r.id != entity_id
            ][:top_k]
            
            self._send_json({
                'entity_id': entity_id,
                'related': related
            })
            return
        
        # Stats
        if path == '/stats':
            entity_types = {}
            for item in self.store:
                et = item.metadata.get('entity_type', 'unknown')
                entity_types[et] = entity_types.get(et, 0) + 1
            
            self._send_json({
                'total_items': len(self.store),
                'entity_types': entity_types,
                'embedding_dim': self.store.embedding_dim
            })
            return
        
        # 404
        self._send_error('Not found', 404)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_error('Invalid JSON')
            return
        
        # Similarity search with custom text
        if path == '/similar':
            text = data.get('text', '')
            top_k = data.get('k', 5)
            
            if not text:
                self._send_error('Missing field: text')
                return
            
            embedding = self.embedder.embed(text)
            results = self.store.query(embedding, top_k=top_k)
            
            self._send_json({
                'text': text,
                'results': [
                    {
                        'id': item.id,
                        'name': item.metadata.get('name', item.id),
                        'entity_type': item.metadata.get('entity_type'),
                        'score': round(score, 4)
                    }
                    for item, score in results
                ]
            })
            return
        
        self._send_error('Not found', 404)


def run_server(store_dir: Path, port: int = 8000, model_name: str = "all-MiniLM-L6-v2"):
    """Run the API server."""
    print(f"Loading memory store from {store_dir}...")
    MemoryAPIHandler.store = MemoryStore.load(store_dir)
    MemoryAPIHandler.embedder = Embedder(model_name)
    
    server = HTTPServer(('0.0.0.0', port), MemoryAPIHandler)
    print(f"Memory API server running at http://localhost:{port}")
    print(f"Endpoints:")
    print(f"  GET  /health           - Health check")
    print(f"  GET  /search?q=...     - Semantic search")
    print(f"  GET  /entity?id=...    - Get entity by ID")
    print(f"  GET  /related?id=...   - Find related entities")
    print(f"  GET  /stats            - Store statistics")
    print(f"  POST /similar          - Find similar to text")
    print(f"\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory store API server')
    parser.add_argument('--store', type=Path, default=Path('memory_store'),
                       help='Memory store directory')
    parser.add_argument('--port', '-p', type=int, default=8000,
                       help='Port to run on (default: 8000)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                       help='Sentence transformer model')
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    if args.store == Path('memory_store'):
        args.store = project_root / 'memory_store'
    
    if not args.store.exists():
        print(f"Error: Memory store not found at {args.store}")
        print("Run 'pixi run build-memory' first")
        sys.exit(1)
    
    run_server(args.store, args.port, args.model)


if __name__ == '__main__':
    main()
