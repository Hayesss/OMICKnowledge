#!/usr/bin/env python3
"""
Build memory store from YAML knowledge graph.
Converts structured YAML content into vectorized memories.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_core.memory_store import MemoryStore, MemoryItem
from memory_core.embedder import Embedder


def load_yaml_entities(content_dir: Path) -> Dict[str, dict]:
    """Load all YAML entities from content directory."""
    entities = {}
    
    for subdir in content_dir.iterdir():
        if not subdir.is_dir():
            continue
        entity_type = subdir.name
        
        for yaml_file in subdir.glob('*.yaml'):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data and 'id' in data:
                entity_id = data['id']
                data['_entity_type'] = entity_type
                data['_source_file'] = str(yaml_file.relative_to(content_dir))
                entities[entity_id] = data
    
    return entities


def entity_to_text(entity: dict) -> str:
    """Convert entity to searchable text representation."""
    parts = []
    
    # Title/Name
    name = entity.get('name', entity.get('id', ''))
    parts.append(f"Name: {name}")
    
    # Type
    entity_type = entity.get('_entity_type', 'unknown')
    parts.append(f"Type: {entity_type}")
    
    # Description
    if 'description' in entity:
        parts.append(f"Description: {entity['description']}")
    
    # Tags
    if 'tags' in entity and entity['tags']:
        parts.append(f"Tags: {', '.join(entity['tags'])}")
    
    # Difficulty
    if 'difficulty' in entity:
        parts.append(f"Difficulty: {entity['difficulty']}")
    
    # Key params (for steps/tools)
    if 'key_params' in entity and entity['key_params']:
        params_text = ', '.join(str(p) for p in entity['key_params'])
        parts.append(f"Key Parameters: {params_text}")
    
    # Input/Output (for steps)
    if 'input' in entity:
        parts.append(f"Input: {entity['input']}")
    if 'output' in entity:
        parts.append(f"Output: {entity['output']}")
    
    # Solution (for issues)
    if 'solution' in entity:
        parts.append(f"Solution: {entity['solution']}")
    
    # Detailed explanation (for concepts)
    if 'detailed_explanation' in entity:
        parts.append(f"Details: {entity['detailed_explanation']}")
    
    return '\n'.join(parts)


def load_edges(edges_file: Path) -> List[dict]:
    """Load edges from YAML file."""
    with open(edges_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('edges', []) if data else []


def build_memory_store(
    content_dir: Path,
    edges_file: Path,
    output_dir: Path,
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32
) -> MemoryStore:
    """Build memory store from knowledge graph.
    
    Args:
        content_dir: Directory containing YAML content files
        edges_file: Path to edges.yaml
        output_dir: Directory to save memory store
        model_name: Sentence transformer model name
        batch_size: Batch size for embedding
        
    Returns:
        Built MemoryStore
    """
    print("Loading entities...")
    entities = load_yaml_entities(content_dir)
    print(f"Loaded {len(entities)} entities")
    
    print("Loading edges...")
    edges = load_edges(edges_file)
    print(f"Loaded {len(edges)} edges")
    
    # Build relationship lookup
    print("Building relationship index...")
    entity_relations: Dict[str, List[dict]] = {eid: [] for eid in entities}
    for edge in edges:
        source = edge.get('source')
        if source in entity_relations:
            entity_relations[source].append(edge)
    
    # Initialize embedder
    print(f"Initializing embedder with model: {model_name}")
    embedder = Embedder(model_name)
    print(f"Embedding dimension: {embedder.embedding_dim}")
    
    # Create memory store
    store = MemoryStore(embedding_dim=embedder.embedding_dim)
    
    # Prepare all texts
    print("Preparing entity texts...")
    items_to_add = []
    texts_to_embed = []
    
    for entity_id, entity in entities.items():
        # Build rich text representation
        text = entity_to_text(entity)
        
        # Add relationship context
        relations = entity_relations.get(entity_id, [])
        if relations:
            rel_texts = []
            for rel in relations[:10]:  # Limit to first 10 relations
                target_id = rel.get('target', '')
                relation_type = rel.get('relation', '')
                if target_id in entities:
                    target_name = entities[target_id].get('name', target_id)
                    rel_texts.append(f"{relation_type} {target_name}")
            if rel_texts:
                text += "\n\nRelationships:\n" + "\n".join(f"- {r}" for r in rel_texts)
        
        # Build metadata
        metadata = {
            'entity_type': entity.get('_entity_type'),
            'source_file': entity.get('_source_file'),
            'name': entity.get('name', entity_id),
            'tags': entity.get('tags', []),
            'difficulty': entity.get('difficulty'),
            'n_relations': len(relations),
            'original_data': {k: v for k, v in entity.items() 
                           if not k.startswith('_') and k != 'description'}
        }
        
        items_to_add.append((entity_id, text, metadata))
        texts_to_embed.append(text)
    
    # Embed in batches
    print(f"Embedding {len(texts_to_embed)} entities...")
    embeddings = embedder.embed_batch(texts_to_embed, batch_size=batch_size)
    
    # Add to store
    print("Adding to memory store...")
    for i, (entity_id, text, metadata) in enumerate(tqdm(items_to_add)):
        item = MemoryItem(
            id=entity_id,
            text=text,
            embedding=embeddings[i],
            metadata=metadata
        )
        store.add(item)
    
    # Save
    print(f"Saving memory store to {output_dir}")
    store.save(output_dir)
    
    return store


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build memory store from knowledge graph')
    parser.add_argument('--content', type=Path, default=Path('content'),
                       help='Content directory (default: content)')
    parser.add_argument('--edges', type=Path, default=Path('edges/edges.yaml'),
                       help='Edges YAML file (default: edges/edges.yaml)')
    parser.add_argument('--output', type=Path, default=Path('memory_store'),
                       help='Output directory (default: memory_store)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                       help='Sentence transformer model')
    
    args = parser.parse_args()
    
    # Change to project root if running from elsewhere
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    store = build_memory_store(
        content_dir=args.content,
        edges_file=args.edges,
        output_dir=args.output,
        model_name=args.model
    )
    
    print(f"\nBuild complete! Memory store has {len(store)} items.")
    print(f"You can now query it with: python -m memory_core.query")


if __name__ == '__main__':
    main()
