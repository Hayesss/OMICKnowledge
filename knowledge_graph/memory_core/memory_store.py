#!/usr/bin/env python3
"""
Karpathy-style Vector Memory Store

Core design principles (from Karpathy's llm.c and teachings):
1. Simple: Just numpy arrays, no complex database
2. Fast: Vectorized cosine similarity
3. Efficient: Normalize on insert, dot product for retrieval
"""

import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


@dataclass
class MemoryItem:
    """A single memory item with metadata."""
    id: str
    text: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (embedding stored separately)."""
        return {
            'id': self.id,
            'text': self.text,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], embedding: Optional[np.ndarray] = None):
        """Create from dictionary."""
        return cls(
            id=data['id'],
            text=data['text'],
            metadata=data.get('metadata', {}),
            embedding=embedding
        )


class MemoryStore:
    """Simple vector memory store using numpy.
    
    Inspired by Karpathy's minimal, efficient approach:
    - embeddings: (n_items, dim) numpy array
    - items: list of MemoryItem (without embeddings to save memory)
    - retrieval: dot product (since vectors are normalized)
    """
    
    def __init__(self, embedding_dim: int = 384):
        """Initialize empty memory store.
        
        Args:
            embedding_dim: Dimension of embedding vectors.
                          Default 384 for all-MiniLM-L6-v2.
        """
        self.embedding_dim = embedding_dim
        self.embeddings = np.zeros((0, embedding_dim), dtype=np.float32)
        self.items: List[MemoryItem] = []
        self.id_to_index: Dict[str, int] = {}
    
    def add(self, item: MemoryItem) -> int:
        """Add a memory item.
        
        Args:
            item: MemoryItem with embedding already computed.
            
        Returns:
            Index of the added item.
        """
        if item.id in self.id_to_index:
            raise ValueError(f"Item with id '{item.id}' already exists")
        
        if item.embedding is None:
            raise ValueError(f"Item must have embedding before adding")
        
        idx = len(self.items)
        self.items.append(item)
        self.id_to_index[item.id] = idx
        
        # Append embedding
        embedding = item.embedding.reshape(1, -1)
        if self.embeddings.shape[0] == 0:
            self.embeddings = embedding
        else:
            self.embeddings = np.vstack([self.embeddings, embedding])
        
        return idx
    
    def add_batch(self, items: List[MemoryItem]):
        """Add multiple items efficiently."""
        for item in items:
            self.add(item)
    
    def get(self, id: str) -> Optional[MemoryItem]:
        """Get item by id."""
        idx = self.id_to_index.get(id)
        if idx is None:
            return None
        item = self.items[idx]
        item.embedding = self.embeddings[idx]
        return item
    
    def query(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5,
        filter_fn: Optional[callable] = None
    ) -> List[Tuple[MemoryItem, float]]:
        """Query memories by similarity.
        
        Args:
            query_embedding: Query vector (normalized).
            top_k: Number of results to return.
            filter_fn: Optional filter function (item -> bool).
            
        Returns:
            List of (item, score) tuples, sorted by score descending.
        """
        if self.embeddings.shape[0] == 0:
            return []
        
        # Cosine similarity via dot product (vectors are normalized)
        scores = self.embeddings @ query_embedding
        
        # Apply filter if provided
        if filter_fn:
            valid_indices = [i for i in range(len(self.items)) if filter_fn(self.items[i])]
            if not valid_indices:
                return []
            valid_scores = scores[valid_indices]
            top_local_indices = np.argsort(valid_scores)[::-1][:top_k]
            top_indices = [valid_indices[i] for i in top_local_indices]
        else:
            top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            item = self.items[idx]
            item.embedding = self.embeddings[idx]
            results.append((item, float(scores[idx])))
        
        return results
    
    def query_by_text(
        self,
        embedder,
        query_text: str,
        top_k: int = 5,
        filter_fn: Optional[callable] = None
    ) -> List[Tuple[MemoryItem, float]]:
        """Query by text (auto-embeds the query)."""
        query_embedding = embedder.embed(query_text)
        return self.query(query_embedding, top_k, filter_fn)
    
    def save(self, directory: Path):
        """Save memory store to disk.
        
        Saves:
        - embeddings.npy: numpy array of embeddings
        - items.jsonl: JSON lines of items (without embeddings)
        - config.json: store configuration
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings
        np.save(directory / 'embeddings.npy', self.embeddings)
        
        # Save items
        with open(directory / 'items.jsonl', 'w', encoding='utf-8') as f:
            for item in self.items:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + '\n')
        
        # Save config
        config = {
            'embedding_dim': self.embedding_dim,
            'n_items': len(self.items)
        }
        with open(directory / 'config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"Memory store saved: {len(self.items)} items to {directory}")
    
    @classmethod
    def load(cls, directory: Path) -> 'MemoryStore':
        """Load memory store from disk."""
        directory = Path(directory)
        
        # Load config
        with open(directory / 'config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        store = cls(embedding_dim=config['embedding_dim'])
        
        # Load embeddings
        store.embeddings = np.load(directory / 'embeddings.npy')
        
        # Load items
        with open(directory / 'items.jsonl', 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                data = json.loads(line.strip())
                item = MemoryItem.from_dict(data, embedding=store.embeddings[idx])
                store.items.append(item)
                store.id_to_index[item.id] = idx
        
        print(f"Memory store loaded: {len(store.items)} items from {directory}")
        return store
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __iter__(self):
        return iter(self.items)
