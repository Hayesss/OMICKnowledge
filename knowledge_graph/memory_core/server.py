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
        
        # PDF Import Records API
        if path == '/api/papers':
            try:
                kb_id = params.get('kb', [''])[0]
                if not kb_id:
                    kb_manager = self._get_kb_manager()
                    current = kb_manager.get_current_kb()
                    kb_id = current.id if current else 'omics'
                
                sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
                from pdf_import_record import PDFImportRecordManager
                
                record_manager = PDFImportRecordManager()
                records = record_manager.get_records(kb_id)
                stats = record_manager.get_stats(kb_id)
                
                self._send_json({
                    'success': True,
                    'papers': [
                        {
                            'id': r.id,
                            'filename': r.filename,
                            'imported_at': r.imported_at,
                            'entity_count': r.entity_count,
                            'entities': r.entities,
                            'status': r.status
                        }
                        for r in records
                    ],
                    'stats': stats,
                    'kb_id': kb_id
                })
            except Exception as e:
                self._send_error(f'Failed to get papers: {str(e)}')
            return
        
        # 404
        self._send_error('Not found', 404)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Process PDF - handle multipart/form-data (must be before JSON parsing)
        if path == '/api/process-pdf':
            self._handle_process_pdf(content_length)
            return
        
        # For other endpoints, parse JSON body
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
    
    def _handle_process_pdf(self, content_length: int):
        """Handle PDF upload and processing."""
        try:
            import tempfile
            import os
            from multipart import MultipartParser
            
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self._send_error('Expected multipart/form-data')
                return
            
            # Extract boundary
            boundary = None
            for part in content_type.split(';'):
                part = part.strip()
                if part.startswith('boundary='):
                    boundary = part[9:].strip('"')
                    break
            
            if not boundary:
                self._send_error('No boundary in Content-Type')
                return
            
            # Read raw body
            body = self.rfile.read(content_length)
            
            # Parse multipart using python-multipart
            from io import BytesIO
            from multipart.multipart import parse_options_header
            
            # Simple multipart parser
            parts = self._parse_multipart(body, boundary)
            
            # Get uploaded PDF
            if 'pdf' not in parts:
                self._send_error('No PDF file provided')
                return
            
            pdf_data = parts['pdf']['data']
            if not pdf_data:
                self._send_error('Empty PDF file')
                return
            
            # Get API settings from form
            api_base = parts.get('apiBase', {}).get('data', b'https://api.openai-proxy.org').decode('utf-8')
            api_key = parts.get('apiKey', {}).get('data', b'').decode('utf-8')
            model = parts.get('model', {}).get('data', b'gpt-4.1-mini').decode('utf-8')
            
            if not api_key:
                self._send_error('API Key is required')
                return
            
            # Save PDF to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(pdf_data)
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
                
                # Save entities to current KB's content directory
                kb_manager = self._get_kb_manager()
                current_kb = kb_manager.get_current_kb()
                if current_kb:
                    output_dir = kb_manager.get_kb_content_dir(current_kb.id)
                else:
                    output_dir = Path('content')
                
                processor.save_entities_to_yaml(result, str(output_dir))
                
                # Record import history
                sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
                from pdf_import_record import PDFImportRecordManager, create_import_record
                
                record_manager = PDFImportRecordManager()
                import_record = create_import_record(
                    filename=parts['pdf'].get('filename', 'unknown.pdf'),
                    kb_id=current_kb.id if current_kb else 'default',
                    entities=result['entities']
                )
                record_manager.add_record(import_record)
                
                # Auto-build: export wiki and rebuild memory store
                build_result = self._auto_build_kb(kb_manager, current_kb)
                
                # Prepare entity details with file paths
                entity_details = []
                for e in result['entities']:
                    entity_details.append({
                        'id': e['id'],
                        'name': e['name'],
                        'type': e['type'],
                        'description': e['description'][:100] + '...' if len(e['description']) > 100 else e['description'],
                        'file_path': f"kb/{current_kb.id if current_kb else 'content'}/content/{e['type']}/{e['id']}.yaml",
                        'url': f"/editor/index.html?type={e['type']}&id={e['id']}"
                    })
                
                self._send_json({
                    'success': True,
                    'message': f'PDF processed successfully',
                    'filename': result['filename'],
                    'entity_count': result['entity_count'],
                    'entities': entity_details,
                    'kb_id': current_kb.id if current_kb else None,
                    'build': build_result
                })
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            import traceback
            self._send_error(f'PDF processing failed: {str(e)}\n{traceback.format_exc()}')
    
    def _auto_build_kb(self, kb_manager, current_kb) -> dict:
        """Auto-build wiki and memory store for current KB."""
        import subprocess
        import threading
        
        result = {'status': 'pending', 'wiki': None, 'memory': None}
        
        if not current_kb:
            return {**result, 'status': 'skipped', 'error': 'No current KB'}
        
        kb_id = current_kb.id
        kb_dir = kb_manager.get_kb_dir(kb_id)
        
        def run_build():
            try:
                # Run export-wiki
                wiki_result = subprocess.run(
                    ['pixi', 'run', 'python', '-m', 'scripts.yaml_to_wiki', str(kb_dir / 'content'), str(kb_dir / 'wiki')],
                    cwd=Path(__file__).parent.parent,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                result['wiki'] = {'success': wiki_result.returncode == 0, 'output': wiki_result.stdout[-500:] if wiki_result.stdout else ''}
                
                # Run build-memory
                memory_result = subprocess.run(
                    ['pixi', 'run', 'python', '-m', 'scripts.yaml_to_memory', str(kb_dir / 'content'), str(kb_dir / 'memory_store')],
                    cwd=Path(__file__).parent.parent,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                result['memory'] = {'success': memory_result.returncode == 0, 'output': memory_result.stdout[-500:] if memory_result.stdout else ''}
                
                result['status'] = 'completed'
                
                # Reload memory store after build
                if result['memory']['success']:
                    new_store = MemoryStore.load(kb_dir / 'memory_store')
                    MemoryAPIHandler.store = new_store
                    
            except Exception as e:
                result['status'] = 'error'
                result['error'] = str(e)
        
        # Run build in background thread
        thread = threading.Thread(target=run_build)
        thread.daemon = True
        thread.start()
        
        return result
    
    def _parse_multipart(self, body: bytes, boundary: str) -> dict:
        """Simple multipart/form-data parser."""
        parts = {}
        boundary_bytes = ('--' + boundary).encode('utf-8')
        
        # Split by boundary
        sections = body.split(boundary_bytes)
        
        for section in sections:
            section = section.strip()
            if not section or section == b'--':
                continue
            
            # Parse headers and data
            if b'\r\n\r\n' in section:
                header_part, data = section.split(b'\r\n\r\n', 1)
                data = data.rstrip(b'\r\n')
                
                # Parse Content-Disposition header
                headers = header_part.decode('utf-8', errors='replace')
                name = None
                filename = None
                
                for line in headers.split('\r\n'):
                    if line.lower().startswith('content-disposition:'):
                        # Extract name
                        if 'name="' in line:
                            start = line.index('name="') + 6
                            end = line.index('"', start)
                            name = line[start:end]
                        # Extract filename
                        if 'filename="' in line:
                            start = line.index('filename="') + 10
                            end = line.index('"', start)
                            filename = line[start:end]
                
                if name:
                    parts[name] = {
                        'data': data,
                        'filename': filename
                    }
        
        return parts


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
