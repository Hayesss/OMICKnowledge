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
    kb_manager = None  # Knowledge base manager
    
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
    
    def _get_kb_manager(self):
        """Get or create knowledge base manager."""
        if self.kb_manager is None:
            from kb_manager import KnowledgeBaseManager
            self.kb_manager = KnowledgeBaseManager()
        return self.kb_manager
    
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
        
        # Knowledge Base API
        if path == '/api/kb/list':
            try:
                kb_manager = self._get_kb_manager()
                kbs = kb_manager.list_kbs()
                current = kb_manager.get_current_kb()
                
                self._send_json({
                    'success': True,
                    'knowledge_bases': [kb.to_dict() for kb in kbs],
                    'current': current.to_dict() if current else None
                })
            except Exception as e:
                self._send_error(f'Failed to list knowledge bases: {str(e)}')
            return
        
        if path == '/api/kb/current':
            try:
                kb_manager = self._get_kb_manager()
                current = kb_manager.get_current_kb()
                
                self._send_json({
                    'success': True,
                    'knowledge_base': current.to_dict() if current else None
                })
            except Exception as e:
                self._send_error(f'Failed to get current knowledge base: {str(e)}')
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
        
        # Save YAML entity (for web editor)
        if path == '/api/save':
            try:
                yaml_content = data.get('yaml', '')
                entity_type = data.get('entityType', '')
                entity_id = data.get('entityId', '')
                
                if not yaml_content or not entity_type or not entity_id:
                    self._send_error('Missing required fields: yaml, entityType, entityId')
                    return
                
                # Validate YAML
                import yaml
                try:
                    parsed = yaml.safe_load(yaml_content)
                    if not parsed or not isinstance(parsed, dict):
                        self._send_error('Invalid YAML format')
                        return
                except yaml.YAMLError as e:
                    self._send_error(f'YAML parse error: {str(e)}')
                    return
                
                # Determine file path
                project_root = Path(__file__).parent.parent
                content_dir = project_root / 'content'
                type_dir = content_dir / entity_type
                
                # Create directory if not exists
                type_dir.mkdir(parents=True, exist_ok=True)
                
                # Write YAML file
                file_path = type_dir / f"{entity_id}.yaml"
                file_path.write_text(yaml_content, encoding='utf-8')
                
                # Trigger background rebuild (optional)
                # This could be done via subprocess or queue
                
                self._send_json({
                    'success': True,
                    'message': f'Entity saved to {file_path}',
                    'path': str(file_path),
                    'entityId': entity_id
                })
                return
                
            except Exception as e:
                self._send_error(f'Save failed: {str(e)}')
                return
        
        # Trigger rebuild (for web editor)
        if path == '/api/rebuild':
            try:
                import subprocess
                result = subprocess.run(
                    ['pixi', 'run', 'export-wiki'],
                    cwd=Path(__file__).parent.parent,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self._send_json({
                        'success': True,
                        'message': 'Wiki exported successfully',
                        'output': result.stdout
                    })
                else:
                    self._send_error(f'Export failed: {result.stderr}')
                    
            except Exception as e:
                self._send_error(f'Rebuild failed: {str(e)}')
            return
        
        # Process PDF and extract entities
        if path == '/api/process-pdf':
            try:
                import cgi
                import tempfile
                import os
                
                # Parse multipart form data
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' not in content_type:
                    self._send_error('Expected multipart/form-data')
                    return
                
                # Create form parser
                environ = {
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                    'CONTENT_LENGTH': str(content_length)
                }
                
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ=environ
                )
                
                # Get uploaded PDF
                if 'pdf' not in form:
                    self._send_error('No PDF file provided')
                    return
                
                pdf_field = form['pdf']
                if not pdf_field.filename:
                    self._send_error('Empty PDF file')
                    return
                
                # Get API settings from form
                api_base = form.getvalue('apiBase', 'https://api.openai-proxy.org')
                api_key = form.getvalue('apiKey', '')
                model = form.getvalue('model', 'gpt-4.1-mini')
                
                if not api_key:
                    self._send_error('API Key is required')
                    return
                
                # Save PDF to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(pdf_field.file.read())
                    tmp_path = tmp.name
                
                try:
                    # Import and run PDF processor
                    sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
                    from pdf_processor import PDFProcessor
                    
                    processor = PDFProcessor(
                        api_base=api_base,
                        api_key=api_key,
                        model=model
                    )
                    
                    result = processor.process_pdf(tmp_path, extract_figures=False)
                    
                    # Save entities to content directory
                    processor.save_entities_to_yaml(result)
                    
                    self._send_json({
                        'success': True,
                        'message': f'PDF processed successfully',
                        'filename': result['filename'],
                        'entity_count': result['entity_count'],
                        'entities': [e['id'] for e in result['entities']]
                    })
                    
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        
            except Exception as e:
                import traceback
                self._send_error(f'PDF processing failed: {str(e)}\n{traceback.format_exc()}')
            return
        
        # Knowledge Base API - Create
        if path == '/api/kb/create':
            try:
                kb_manager = self._get_kb_manager()
                kb = kb_manager.create_kb(
                    kb_id=data.get('id'),
                    name=data.get('name'),
                    description=data.get('description', ''),
                    color=data.get('color', '#3b82f6')
                )
                
                self._send_json({
                    'success': True,
                    'knowledge_base': kb.to_dict()
                })
            except Exception as e:
                self._send_error(f'Failed to create knowledge base: {str(e)}')
            return
        
        # Knowledge Base API - Switch
        if path == '/api/kb/switch':
            try:
                kb_id = data.get('id')
                kb_manager = self._get_kb_manager()
                kb_manager.set_current_kb(kb_id)
                
                # Reload store for new KB
                kb = kb_manager.get_kb(kb_id)
                memory_dir = kb_manager.get_kb_memory_dir(kb_id)
                MemoryAPIHandler.store = MemoryStore.load(memory_dir)
                
                self._send_json({
                    'success': True,
                    'knowledge_base': kb.to_dict()
                })
            except Exception as e:
                self._send_error(f'Failed to switch knowledge base: {str(e)}')
            return
        
        self._send_error('Not found', 404)
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # Knowledge Base API - Delete
        if path == '/api/kb/delete':
            try:
                kb_id = params.get('id', [''])[0]
                if not kb_id:
                    self._send_error('Missing parameter: id')
                    return
                
                kb_manager = self._get_kb_manager()
                success = kb_manager.delete_kb(kb_id)
                
                self._send_json({
                    'success': success,
                    'message': f'Knowledge base {kb_id} deleted' if success else 'Not found'
                })
            except Exception as e:
                self._send_error(f'Failed to delete knowledge base: {str(e)}')
            return
        
        self._send_error('Not found', 404)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


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
    print(f"  POST /api/save         - Save YAML entity (web editor)")
    print(f"  POST /api/rebuild      - Trigger wiki rebuild")
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
