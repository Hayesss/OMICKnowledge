#!/usr/bin/env python3
import os
import sys
import json
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import load_entities


def merge_tool_auto_data(entities, content_dir):
    """Merge automatically fetched tool info into existing tool entities."""
    tools_auto_dir = os.path.join(content_dir, 'tools_auto')
    if not os.path.isdir(tools_auto_dir):
        return
    for filename in os.listdir(tools_auto_dir):
        if not filename.endswith('.yaml'):
            continue
        filepath = os.path.join(tools_auto_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        tool_id = data.get('tool_id')
        if tool_id and tool_id in entities:
            entities[tool_id]['auto_fetched'] = {
                'latest_version': data.get('data', {}).get('latest_version'),
                'release_url': data.get('data', {}).get('release_url'),
                'published_at': data.get('data', {}).get('published_at'),
                'fetched_at': data.get('fetched_at'),
            }


def build_graph(entities, edges, output_path=None):
    """Build a graph structure from entities and edges.
    
    Args:
        entities: Dict mapping entity_id -> entity dict
        edges: List of edge dicts with source, target, relation, optional properties
        output_path: Optional path to write JSON output
    
    Returns:
        Dict with 'nodes' and 'edges' lists
    """
    nodes = []
    for entity_id, entity in entities.items():
        node = dict(entity)
        node['id'] = entity_id
        nodes.append(node)

    edge_list = []
    for edge in edges:
        edge_list.append({
            'source': edge['source'],
            'target': edge['target'],
            'relation': edge['relation'],
            'properties': edge.get('properties', {})
        })

    graph = {'nodes': nodes, 'edges': edge_list}

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

    return graph


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    content_dir = os.path.join(base_dir, 'content')
    edges_path = os.path.join(base_dir, 'edges', 'edges.yaml')
    output_path = os.path.join(base_dir, 'web', 'data', 'graph.json')

    entities = load_entities(content_dir)
    merge_tool_auto_data(entities, content_dir)

    with open(edges_path, 'r', encoding='utf-8') as f:
        edges_data = yaml.safe_load(f) or {}
    edges = edges_data.get('edges', [])

    build_graph(entities, edges, output_path)
    print(f"Graph built with {len(entities)} nodes and {len(edges)} edges.")
    print(f"Output: {output_path}")


if __name__ == '__main__':
    main()
