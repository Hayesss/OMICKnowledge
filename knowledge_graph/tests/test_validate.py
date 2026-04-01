import os
import sys
import tempfile
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from validate import load_schema, load_entities, validate_entities, validate_edges


def test_load_schema():
    schema = load_schema('knowledge_graph/schema/schema.yaml')
    assert 'entity_types' in schema
    assert 'tool' in schema['entity_types']


def test_validate_entities_valid():
    schema = {
        'entity_types': {
            'tool': {
                'required_properties': ['id', 'name', 'type', 'description'],
                'optional_properties': ['version']
            }
        }
    }
    entities = {
        'macs2': {
            'id': 'macs2',
            'name': 'MACS2',
            'type': 'tool',
            'description': 'peak caller'
        }
    }
    errors = validate_entities(entities, schema)
    assert len(errors) == 0


def test_validate_entities_missing_required():
    schema = {
        'entity_types': {
            'tool': {
                'required_properties': ['id', 'name', 'type', 'description'],
                'optional_properties': []
            }
        }
    }
    entities = {
        'macs2': {
            'id': 'macs2',
            'name': 'MACS2',
            'type': 'tool'
        }
    }
    errors = validate_entities(entities, schema)
    assert len(errors) == 1
    assert 'description' in errors[0]


def test_validate_edges_missing_node():
    entities = {'macs2': {'id': 'macs2'}}
    edges = [{'source': 'macs2', 'relation': 'applies_to', 'target': 'atac-seq'}]
    errors = validate_edges(edges, entities)
    assert len(errors) == 1
    assert 'atac-seq' in errors[0]
