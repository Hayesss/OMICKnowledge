#!/usr/bin/env python3
"""Tests for memory store functionality."""

import sys
import pytest
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_core.memory_store import MemoryStore, MemoryItem
from memory_core.embedder import Embedder


class TestMemoryItem:
    """Test MemoryItem dataclass."""
    
    def test_creation(self):
        item = MemoryItem(
            id="test-1",
            text="Test memory",
            embedding=np.array([1.0, 0.0, 0.0]),
            metadata={"key": "value"}
        )
        assert item.id == "test-1"
        assert item.text == "Test memory"
        assert item.metadata == {"key": "value"}
    
    def test_to_dict(self):
        item = MemoryItem(id="test-1", text="Test")
        d = item.to_dict()
        assert d["id"] == "test-1"
        assert d["text"] == "Test"
        assert "embedding" not in d


class TestMemoryStore:
    """Test MemoryStore functionality."""
    
    @pytest.fixture
    def store(self):
        return MemoryStore(embedding_dim=3)
    
    def test_empty_store(self, store):
        assert len(store) == 0
        assert store.embedding_dim == 3
    
    def test_add_item(self, store):
        item = MemoryItem(
            id="test-1",
            text="Test",
            embedding=np.array([1.0, 0.0, 0.0])
        )
        idx = store.add(item)
        assert idx == 0
        assert len(store) == 1
    
    def test_duplicate_id_raises(self, store):
        item = MemoryItem(id="test-1", text="Test", embedding=np.array([1.0, 0.0, 0.0]))
        store.add(item)
        
        with pytest.raises(ValueError, match="already exists"):
            store.add(item)
    
    def test_get_item(self, store):
        item = MemoryItem(id="test-1", text="Test", embedding=np.array([1.0, 0.0, 0.0]))
        store.add(item)
        
        retrieved = store.get("test-1")
        assert retrieved is not None
        assert retrieved.id == "test-1"
    
    def test_get_nonexistent(self, store):
        assert store.get("nonexistent") is None
    
    def test_query(self, store):
        # Add some items
        store.add(MemoryItem(id="a", text="Apple", embedding=np.array([1.0, 0.0, 0.0])))
        store.add(MemoryItem(id="b", text="Banana", embedding=np.array([0.0, 1.0, 0.0])))
        store.add(MemoryItem(id="c", text="Cherry", embedding=np.array([0.0, 0.0, 1.0])))
        
        # Query for something similar to Apple
        query = np.array([0.9, 0.1, 0.0])
        query = query / np.linalg.norm(query)
        
        results = store.query(query, top_k=2)
        assert len(results) == 2
        assert results[0][0].id == "a"  # Apple should be first
        assert results[0][1] > 0.8  # High similarity


class TestEmbedder:
    """Test Embedder functionality."""
    
    def test_embed_single(self):
        embedder = Embedder()
        embedding = embedder.embed("Test text")
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (embedder.embedding_dim,)
        # Check normalized
        assert abs(np.linalg.norm(embedding) - 1.0) < 1e-5
    
    def test_embed_batch(self):
        embedder = Embedder()
        texts = ["First text", "Second text", "Third text"]
        embeddings = embedder.embed(texts)
        
        assert embeddings.shape == (3, embedder.embedding_dim)
        # All should be normalized
        norms = np.linalg.norm(embeddings, axis=1)
        assert np.allclose(norms, 1.0)
    
    def test_similarity(self):
        embedder = Embedder()
        
        # Similar texts should have high similarity
        emb1 = embedder.embed("machine learning")
        emb2 = embedder.embed("deep learning")
        emb3 = embedder.embed("apple pie")
        
        sim_1_2 = np.dot(emb1, emb2)
        sim_1_3 = np.dot(emb1, emb3)
        
        # Similar topics should be more similar
        assert sim_1_2 > sim_1_3


def test_end_to_end(tmp_path):
    """Test full workflow."""
    # Create store
    store = MemoryStore(embedding_dim=384)
    embedder = Embedder()
    
    # Add items
    texts = [
        ("cut-tag", "CUT&Tag is a method for profiling histone modifications and transcription factor binding."),
        ("atac-seq", "ATAC-seq assays chromatin accessibility across the genome."),
        ("chip-seq", "ChIP-seq identifies protein-DNA binding sites.")
    ]
    
    for id_, text in texts:
        embedding = embedder.embed(text)
        item = MemoryItem(id=id_, text=text, embedding=embedding)
        store.add(item)
    
    # Save and reload
    store.save(tmp_path / "test_store")
    loaded = MemoryStore.load(tmp_path / "test_store")
    
    assert len(loaded) == 3
    
    # Query
    results = loaded.query_by_text(embedder, "how to study protein binding", top_k=2)
    assert len(results) == 2
    # Should find ChIP-seq or CUT&Tag
    ids = [r[0].id for r in results]
    assert "chip-seq" in ids or "cut-tag" in ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
