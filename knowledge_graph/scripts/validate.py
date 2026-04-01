#!/usr/bin/env python3
import os
import sys
import yaml


def load_schema(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_entities(content_dir):
    entities = {}
    for subdir in os.listdir(content_dir):
        subdir_path = os.path.join(content_dir, subdir)
        if not os.path.isdir(subdir_path):
            continue
        for filename in os.listdir(subdir_path):
            if not filename.endswith('.yaml'):
                continue
            filepath = os.path.join(subdir_path, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data is None:
                continue
            entity_id = data.get('id')
            if entity_id is None:
                continue
            if entity_id in entities:
                raise ValueError(f"Duplicate entity id: {entity_id}")
            entities[entity_id] = data
    return entities


def validate_entities(entities, schema):
    errors = []
    for entity_id, entity in entities.items():
        entity_type = entity.get('type')
        if entity_type not in schema.get('entity_types', {}):
            errors.append(f"Entity '{entity_id}': unknown type '{entity_type}'")
            continue
        type_schema = schema['entity_types'][entity_type]
        required = set(type_schema.get('required_properties', []))
        for prop in required:
            if prop not in entity:
                errors.append(f"Entity '{entity_id}': missing required property '{prop}'")
    return errors


def validate_edges(edges, entities):
    errors = []
    entity_ids = set(entities.keys())
    for i, edge in enumerate(edges):
        src = edge.get('source')
        tgt = edge.get('target')
        rel = edge.get('relation')
        if src not in entity_ids:
            errors.append(f"Edge {i}: source '{src}' not found")
        if tgt not in entity_ids:
            errors.append(f"Edge {i}: target '{tgt}' not found")
        if not rel:
            errors.append(f"Edge {i}: missing relation")
    return errors


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, 'schema', 'schema.yaml')
    content_dir = os.path.join(base_dir, 'content')
    edges_path = os.path.join(base_dir, 'edges', 'edges.yaml')

    schema = load_schema(schema_path)
    entities = load_entities(content_dir)

    print(f"Loaded {len(entities)} entities")

    entity_errors = validate_entities(entities, schema)
    if entity_errors:
        print("Entity validation errors:")
        for err in entity_errors:
            print(f"  - {err}")
    else:
        print("All entities valid.")

    with open(edges_path, 'r', encoding='utf-8') as f:
        edges_data = yaml.safe_load(f) or {}
    edges = edges_data.get('edges', [])

    edge_errors = validate_edges(edges, entities)
    if edge_errors:
        print("Edge validation errors:")
        for err in edge_errors:
            print(f"  - {err}")
    else:
        print("All edges valid.")

    if entity_errors or edge_errors:
        sys.exit(1)
    print("Validation passed.")


if __name__ == '__main__':
    main()
