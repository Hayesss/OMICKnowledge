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
        
        if path == '/api/process-text':
            self._handle_process_text(content_length)
            return
        
        if path == '/api/extract-for-review':
            self._handle_extract_for_review(content_length)
            return
        
        if path == '/api/save-deep-import':
            self._handle_save_deep_import(content_length)
            return
        
        if path == '/api/discuss':
            self._handle_discuss(content_length)
            return
        
        if path == '/api/cross-reference':
            self._handle_cross_reference(content_length)
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
                    'import_id': import_record.id,
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
    
    def _handle_process_text(self, content_length: int):
        """Handle text/notes upload and entity extraction."""
        try:
            import json
            
            # Read and parse JSON body
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            text = data.get('text', '')
            filename = data.get('filename', 'notes.txt')
            api_base = data.get('apiBase', 'https://api.openai-proxy.org')
            api_key = data.get('apiKey', '')
            model = data.get('model', 'gpt-4.1-mini')
            
            if not text:
                self._send_error('No text content provided')
                return
            
            if not api_key:
                self._send_error('API Key is required')
                return
            
            if len(text) > 50000:
                text = text[:50000] + "\n\n[Content truncated due to length]"
            
            # Extract entities using GPT
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from pdf_processor import PDFProcessor
            
            processor = PDFProcessor(
                api_base=api_base,
                api_key=api_key,
                model=model
            )
            
            # Use text extraction method
            result = self._extract_entities_from_text(processor, text, filename)
            
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
                filename=filename,
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
                'message': f'Text processed successfully',
                'filename': filename,
                'entity_count': result['entity_count'],
                'entities': entity_details,
                'import_id': import_record.id,
                'kb_id': current_kb.id if current_kb else None,
                'build': build_result
            })
            
        except Exception as e:
            import traceback
            self._send_error(f'Text processing failed: {str(e)}\n{traceback.format_exc()}')
    
    def _extract_entities_from_text(self, processor: 'PDFProcessor', text: str, filename: str) -> dict:
        """Extract entities from text using GPT."""
        import tempfile
        import os
        
        # Create a temporary markdown file to hold the text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(f"# {filename}\n\n")
            tmp.write(text)
            tmp_path = tmp.name
        
        try:
            # Read the file and process with GPT
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use the processor's GPT to extract entities
            # We'll create a custom prompt for text/note extraction
            prompt = self._create_text_extraction_prompt(content, filename)
            
            # Call GPT API
            import requests
            
            headers = {
                'Authorization': f'Bearer {processor.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': processor.model,
                'messages': [
                    {'role': 'system', 'content': 'You are a knowledge extraction assistant. Extract structured entities from academic notes and literature.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.2
            }
            
            response = requests.post(
                f'{processor.api_base}/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result_data = response.json()
            raw_content = result_data['choices'][0]['message']['content']
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
            else:
                extracted = json.loads(raw_content)
            
            # Generate unique IDs
            import uuid
            base_id = f"note{uuid.uuid4().hex[:8]}"
            
            entities = []
            
            # Add paper/resource entity
            entities.append({
                'id': f'{base_id}-paper',
                'type': 'resources',
                'name': extracted.get('title', filename),
                'description': extracted.get('summary', text[:200]),
                'detailed_explanation': text[:3000],
                'tags': ['笔记', '文献'] + extracted.get('tags', [])
            })
            
            # Add method entities
            for i, method in enumerate(extracted.get('methods', [])):
                entities.append({
                    'id': f'{base_id}-method-{i}',
                    'type': 'steps',
                    'name': method.get('name', f'Method {i+1}'),
                    'description': method.get('description', ''),
                    'detailed_explanation': method.get('details', ''),
                    'tags': ['方法', 'protocol'] + method.get('tags', [])
                })
            
            # Add tool entities
            for i, tool in enumerate(extracted.get('tools', [])):
                entities.append({
                    'id': f'{base_id}-tool-{i}',
                    'type': 'tools',
                    'name': tool.get('name', f'Tool {i+1}'),
                    'description': tool.get('description', ''),
                    'detailed_explanation': tool.get('details', ''),
                    'tags': ['工具', 'software'] + tool.get('tags', [])
                })
            
            # Add concept entities
            for i, concept in enumerate(extracted.get('concepts', [])):
                entities.append({
                    'id': f'{base_id}-concept-{i}',
                    'type': 'concepts',
                    'name': concept.get('name', f'Concept {i+1}'),
                    'description': concept.get('description', ''),
                    'detailed_explanation': concept.get('explanation', ''),
                    'tags': ['概念', '知识'] + concept.get('tags', [])
                })
            
            return {
                'filename': filename,
                'entity_count': len(entities),
                'entities': entities
            }
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _handle_discuss(self, content_length: int):
        """Handle discussion about document content."""
        try:
            import json
            
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            text = data.get('text', '')
            filename = data.get('filename', '')
            question = data.get('question', '')
            history = data.get('history', [])
            api_base = data.get('apiBase', 'https://api.openai-proxy.org')
            api_key = data.get('apiKey', '')
            model = data.get('model', 'gpt-4.1-mini')
            
            if not api_key:
                self._send_error('API Key is required')
                return
            
            import requests
            
            # Build conversation history
            messages = [
                {'role': 'system', 'content': f'''You are a knowledgeable research assistant helping analyze academic documents.
You are discussing the document: "{filename}"

Your role is to:
1. Answer questions about the document content
2. Highlight key contributions and novel aspects
3. Connect ideas to broader context when relevant
4. Suggest what entities (tools, methods, concepts) might be worth extracting
5. Be concise but informative

If the user seems ready to proceed (says things like "confirm", "proceed", "extract", "continue"), 
encourage them to type "确认" to move to the extraction phase.'''},
                {'role': 'user', 'content': f'Document content (first 5000 chars):\n\n{text[:5000]}'}
            ]
            
            # Add conversation history
            for msg in history[-6:]:  # Keep last 6 messages for context
                role = 'assistant' if msg['role'] == 'ai' else 'user'
                messages.append({'role': role, 'content': msg['text']})
            
            # Add current question
            messages.append({'role': 'user', 'content': question})
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model,
                'messages': messages,
                'temperature': 0.7
            }
            
            response = requests.post(
                f'{api_base}/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result_data = response.json()
            reply = result_data['choices'][0]['message']['content']
            
            self._send_json({
                'success': True,
                'reply': reply
            })
            
        except Exception as e:
            import traceback
            self._send_error(f'Discussion failed: {str(e)}\n{traceback.format_exc()}')
    
    def _handle_cross_reference(self, content_length: int):
        """Check for similar entities in existing knowledge base."""
        try:
            import json
            
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            entity_names = data.get('entity_names', [])
            descriptions = data.get('descriptions', [])
            
            if not entity_names:
                self._send_json({'similarities': []})
                return
            
            # Get all existing entities
            kb_manager = self._get_kb_manager()
            current_kb = kb_manager.get_current_kb()
            
            if not current_kb:
                self._send_json({'similarities': []})
                return
            
            # Load existing entities from content directory
            content_dir = kb_manager.get_kb_content_dir(current_kb.id)
            existing_entities = []
            
            for yaml_file in content_dir.rglob('*.yaml'):
                if yaml_file.name == 'edges.yaml':
                    continue
                try:
                    import yaml
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        entity = yaml.safe_load(f)
                        if entity and isinstance(entity, dict):
                            existing_entities.append({
                                'id': entity.get('id', ''),
                                'name': entity.get('name', ''),
                                'type': entity.get('type', ''),
                                'description': entity.get('description', '')
                            })
                except Exception:
                    pass
            
            # Calculate simple similarity (name overlap)
            similarities = []
            for i, new_name in enumerate(entity_names):
                new_desc = descriptions[i] if i < len(descriptions) else ''
                new_words = set(new_name.lower().split() + new_desc.lower().split()[:10])
                
                for existing in existing_entities:
                    existing_words = set(
                        existing['name'].lower().split() + 
                        existing['description'].lower().split()[:10]
                    )
                    
                    # Jaccard similarity
                    intersection = len(new_words & existing_words)
                    union = len(new_words | existing_words)
                    score = intersection / union if union > 0 else 0
                    
                    if score > 0.3:  # Threshold
                        similarities.append({
                            'new_entity': new_name,
                            'existing_entity': existing['name'],
                            'existing_id': existing['id'],
                            'existing_type': existing['type'],
                            'score': round(score, 2)
                        })
            
            # Sort by score
            similarities.sort(key=lambda x: x['score'], reverse=True)
            
            self._send_json({
                'success': True,
                'similarities': similarities[:10]  # Return top 10
            })
            
        except Exception as e:
            import traceback
            self._send_error(f'Cross-reference failed: {str(e)}\n{traceback.format_exc()}')
    
    def _create_text_extraction_prompt(self, content: str, filename: str) -> str:
        """Create extraction prompt for text content."""
        return f"""Please analyze the following academic notes/literature and extract structured information.

Source: {filename}

Content:
```
{content[:8000]}
```

Please extract the following information in JSON format:
{{
    "title": "The title or main topic of this content",
    "summary": "A 2-3 sentence summary of the content",
    "tags": ["tag1", "tag2", "tag3"],
    "methods": [
        {{
            "name": "Method name",
            "description": "Brief description",
            "details": "Detailed explanation",
            "tags": ["method-tag"]
        }}
    ],
    "tools": [
        {{
            "name": "Tool/software name",
            "description": "What it does",
            "details": "Usage details",
            "tags": ["tool-tag"]
        }}
    ],
    "concepts": [
        {{
            "name": "Key concept/term",
            "description": "Brief definition",
            "explanation": "Detailed explanation",
            "tags": ["concept-tag"]
        }}
    ]
}}

Extract as many relevant entities as possible. If a category has no items, return an empty array."""

    def _handle_extract_for_review(self, content_length: int):
        """Extract entities for review (deep import mode) - llm-wiki style."""
        try:
            import json
            
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            text = data.get('text', '')
            filename = data.get('filename', 'notes.txt')
            api_base = data.get('apiBase', 'https://api.openai-proxy.org')
            api_key = data.get('apiKey', '')
            model = data.get('model', 'gpt-4.1-mini')
            
            if not text:
                self._send_error('No text content provided')
                return
            
            if not api_key:
                self._send_error('API Key is required')
                return
            
            # Call GPT to extract structured information
            import requests
            
            prompt = f"""Please analyze the following academic content and extract key information for a knowledge base.

Source: {filename}

Content:
```
{text[:8000]}
```

Please extract and return in JSON format:
{{
    "summary": "A comprehensive 3-5 sentence summary of the main points",
    "entities": [
        {{
            "type": "resources",
            "name": "Paper/Resource title",
            "description": "Brief description"
        }},
        {{
            "type": "tools",
            "name": "Tool/software name",
            "description": "What it does and key features"
        }},
        {{
            "type": "steps",
            "name": "Method name",
            "description": "What the method does"
        }},
        {{
            "type": "concepts",
            "name": "Key concept",
            "description": "Definition and explanation"
        }}
    ]
}}

Guidelines:
1. Include 1 resource entity for the main content
2. Extract 2-5 tool entities if software/tools are mentioned
3. Extract 2-5 step/method entities for procedures described
4. Extract 2-5 concept entities for key terms and ideas
5. Be specific and accurate - these will be reviewed by a human before saving

Return ONLY the JSON, no other text."""

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': 'You are a precise knowledge extraction assistant. Extract accurate, well-structured entities for academic knowledge bases.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.2
            }
            
            response = requests.post(
                f'{api_base}/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result_data = response.json()
            raw_content = result_data['choices'][0]['message']['content']
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
            else:
                extracted = json.loads(raw_content)
            
            self._send_json({
                'success': True,
                'summary': extracted.get('summary', ''),
                'entities': extracted.get('entities', [])
            })
            
        except Exception as e:
            import traceback
            self._send_error(f'Extraction failed: {str(e)}\n{traceback.format_exc()}')
    
    def _handle_save_deep_import(self, content_length: int):
        """Save deep import results after human review - llm-wiki style."""
        try:
            import json
            import uuid
            
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            filename = data.get('filename', 'import.txt')
            summary = data.get('summary', '')
            entities = data.get('entities', [])
            
            if not entities:
                self._send_error('No entities to save')
                return
            
            # Get current KB
            kb_manager = self._get_kb_manager()
            current_kb = kb_manager.get_current_kb()
            if current_kb:
                output_dir = kb_manager.get_kb_content_dir(current_kb.id)
            else:
                output_dir = Path('content')
            
            # Generate base ID
            base_id = f"deep{uuid.uuid4().hex[:8]}"
            
            # Save entities as YAML
            saved_entities = []
            for i, entity in enumerate(entities):
                entity_id = entity.get('id') or f"{base_id}-{i}"
                entity_type = entity.get('type', 'concepts')
                name = entity.get('name', '')
                description = entity.get('description', '')
                
                # Ensure type directory exists
                type_dir = output_dir / entity_type
                type_dir.mkdir(parents=True, exist_ok=True)
                
                yaml_content = f"""# {name}
id: {entity_id}
name: {name}
type: {entity_type}
description: >
  {description}
tags:
  - deep-import
  - from-{filename.replace('.', '-').replace(' ', '-')}
source: "{filename}"
"""
                
                file_path = type_dir / f"{entity_id}.yaml"
                file_path.write_text(yaml_content, encoding='utf-8')
                
                saved_entities.append({
                    'id': entity_id,
                    'name': name,
                    'type': entity_type,
                    'file_path': str(file_path)
                })
            
            # Record import history
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from pdf_import_record import PDFImportRecordManager, create_import_record
            
            record_manager = PDFImportRecordManager()
            import_record = create_import_record(
                filename=filename,
                kb_id=current_kb.id if current_kb else 'default',
                entities=saved_entities
            )
            record_manager.add_record(import_record)
            
            # Create/update a summary page in wiki
            kb_dir = kb_manager.get_kb_dir(current_kb.id if current_kb else 'default')
            summary_dir = kb_dir / 'wiki' / 'sources'
            summary_dir.mkdir(parents=True, exist_ok=True)
            
            safe_filename = filename.replace(' ', '_').replace('.', '_')
            summary_path = summary_dir / f"{safe_filename}.md"
            summary_md = f"""# {filename}

## 摘要

{summary}

## 提取的实体

"""
            for entity in saved_entities:
                summary_md += f"- [[{entity['id']}|{entity['name']}]] ({entity['type']})\n"
            
            summary_md += f"""
## 元数据

- 导入时间: {import_record.imported_at}
- 实体数量: {len(saved_entities)}
- 模式: 深度导入 (人工审核)
"""
            summary_path.write_text(summary_md, encoding='utf-8')
            
            # Update log.md - llm-wiki style logging
            log_path = kb_dir / 'wiki' / 'log.md'
            from datetime import datetime
            
            log_entry = f"""
## [{datetime.now().strftime('%Y-%m-%d')}] ingest | 深度导入: {filename}

- 模式: 人工审核式深度导入
- 实体数量: {len(saved_entities)}
- 来源: {filename}
- Wiki页面: [[sources/{safe_filename}]]
"""
            
            if log_path.exists():
                existing_log = log_path.read_text(encoding='utf-8')
                # Insert after the header section
                lines = existing_log.split('\n')
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('## '):
                        insert_idx = i
                        break
                lines.insert(insert_idx, log_entry)
                log_path.write_text('\n'.join(lines), encoding='utf-8')
            else:
                log_path.write_text(f"""# 知识图谱变更日志

*遵循 llm-wiki 模式，记录知识库的演进历史*

## 格式说明

每行记录格式: `## [YYYY-MM-DD] action | description`

- **ingest**: 新增/更新内容
- **query**: 查询/分析产生的新见解
- **lint**: 健康检查/维护

---
{log_entry}
""", encoding='utf-8')
            
            # Auto-build
            build_result = self._auto_build_kb(kb_manager, current_kb)
            
            # Collect wiki paths for Obsidian integration
            wiki_paths = [str(summary_path)]
            
            self._send_json({
                'success': True,
                'message': f'Saved {len(saved_entities)} entities after review',
                'entity_count': len(saved_entities),
                'entities': saved_entities,
                'import_id': import_record.id,
                'build': build_result,
                'wiki_paths': wiki_paths
            })
            
        except Exception as e:
            import traceback
            self._send_error(f'Save failed: {str(e)}\n{traceback.format_exc()}')

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
                    ['pixi', 'run', 'python', '-m', 'scripts.yaml_to_wiki', '--content-dir', str(kb_dir / 'content'), '--wiki-dir', str(kb_dir / 'wiki')],
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
