import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from build_graph import build_graph


def test_build_graph_basic():
    entities = {
        'atac-seq': {
            'id': 'atac-seq',
            'name': 'ATAC-seq',
            'type': 'assay',
            'description': 'test',
            'difficulty': 'beginner',
            'tags': [],
            'source': 'manual',
            'last_updated': '2026-04-01'
        },
        'preprocessing': {
            'id': 'preprocessing',
            'name': 'Preprocessing',
            'type': 'stage',
            'description': 'test',
            'difficulty': 'beginner',
            'tags': [],
            'source': 'manual',
            'last_updated': '2026-04-01'
        }
    }
    edges = [
        {'source': 'atac-seq', 'relation': 'has_stage', 'target': 'preprocessing'}
    ]
    graph = build_graph(entities, edges)
    assert len(graph['nodes']) == 2
    assert len(graph['edges']) == 1
    assert graph['nodes'][0]['id'] == 'atac-seq'
    assert graph['edges'][0]['relation'] == 'has_stage'


def test_build_graph_output_file():
    entities = {
        'macs2': {
            'id': 'macs2',
            'name': 'MACS2',
            'type': 'tool',
            'description': 'test',
            'difficulty': 'beginner',
            'tags': [],
            'source': 'manual',
            'last_updated': '2026-04-01'
        }
    }
    edges = []
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    build_graph(entities, edges, output_path)
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data['nodes']) == 1
    assert data['nodes'][0]['name'] == 'MACS2'
    os.unlink(output_path)
