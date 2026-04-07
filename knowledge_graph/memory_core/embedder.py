#!/usr/bin/env python3
"""
Text embedding using sentence-transformers.
Karpathy-style: simple, efficient, works locally.
"""

import numpy as np
from typing import List, Union


class Embedder:
    """Simple wrapper for sentence embedding model."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedder with a sentence-transformer model.
        
        Args:
            model_name: Name of the sentence-transformers model.
                       Default is all-MiniLM-L6-v2 (fast, good quality, 384-dim)
        """
        self.model_name = model_name
        self._model = None
        self._embedding_dim = None
    
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._embedding_dim = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pixi add sentence-transformers"
                )
        return self._model
    
    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        if self._embedding_dim is None:
            _ = self.model  # Trigger lazy loading
        return self._embedding_dim
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Embed text(s) into vector(s).
        
        Args:
            texts: Single text or list of texts to embed.
            
        Returns:
            Numpy array of shape (dim,) for single text or (n, dim) for list.
        """
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False
        
        # Encode and normalize (for cosine similarity)
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        if single:
            return embeddings[0]
        return embeddings
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Embed texts in batches for memory efficiency.
        
        Args:
            texts: List of texts to embed.
            batch_size: Batch size for encoding.
            
        Returns:
            Numpy array of shape (n, dim).
        """
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.embed(batch)
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)
