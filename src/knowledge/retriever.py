"""RAG semantic retrieval over a FAISS-backed KnowledgeBase. Reused unchanged from Bootcamp 1 - provided, complete infrastructure."""
from typing import List, Dict, Any
import numpy as np
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.embeddings import EmbeddingGenerator


class Retriever:
    """Semantic retrieval using FAISS."""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.embedding_generator = EmbeddingGenerator()

    def retrieve(self, query: str, top_k: int = 5, threshold: float = 0.4) -> List[Dict[str, Any]]:
        """Retrieve the documents most relevant to `query`."""
        if not self.kb.index:
            return []

        query_embedding = self.embedding_generator.generate_embedding(query)
        query_vector = np.array([query_embedding]).astype("float32")

        distances, indices = self.kb.index.search(query_vector, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.kb.documents):
                doc = self.kb.documents[idx]
                score = 1 / (1 + dist)

                if score >= threshold:
                    results.append({
                        "content": doc["content"],
                        "source": doc["source"],
                        "category": doc["category"],
                        "score": float(score),
                    })

        return results
