import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    """
    In-memory vector store using FAISS (or simple cosine similarity fallback if FAISS not installed).
    Uses sentence-transformers/all-MiniLM-L6-v2 for embeddings.
    """
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2", index_path: str = "./faiss_index"):
        self.embedding_model_name = embedding_model_name
        self.index_path = index_path
        self.documents = []  # List of dicts: {"id", "text", "metadata"}
        self.embeddings = None  # numpy array of embeddings
        self.model = None
        self.initialized = False
        
        logger.info("Initializing FAISSVectorStore...")
        self.load_embedding_model()
        self.load_index()

    def load_embedding_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.model = SentenceTransformer(self.embedding_model_name)
            self.initialized = True
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). RAG semantic search will use simple keyword matching fallback.")
            self.initialized = False

    def create_index(self, dimension: int):
        pass

    def load_index(self) -> None:
        """Load index from path if exists."""
        if os.path.exists(self.index_path) and os.path.isdir(self.index_path):
            try:
                import json
                doc_path = os.path.join(self.index_path, "documents.json")
                if os.path.exists(doc_path):
                    with open(doc_path, "r", encoding="utf-8") as f:
                        self.documents = json.load(f)
                
                import numpy as np
                emb_path = os.path.join(self.index_path, "embeddings.npy")
                if os.path.exists(emb_path):
                    self.embeddings = np.load(emb_path)
                logger.info(f"Loaded index from {self.index_path} with {len(self.documents)} documents.")
            except Exception as e:
                logger.error(f"Error loading index: {e}")

    def save_index(self) -> None:
        """Save documents and embeddings to disk."""
        os.makedirs(self.index_path, exist_ok=True)
        try:
            import json
            doc_path = os.path.join(self.index_path, "documents.json")
            with open(doc_path, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2)
            
            if self.embeddings is not None:
                import numpy as np
                emb_path = os.path.join(self.index_path, "embeddings.npy")
                np.save(emb_path, self.embeddings)
            logger.info(f"Saved index to {self.index_path} with {len(self.documents)} documents.")
        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add a list of documents. Each document is a dict with 'text' and optional 'metadata'."""
        if not documents:
            return
        
        texts = [doc["text"] for doc in documents]
        
        new_embeddings = None
        if self.initialized and self.model is not None:
            try:
                new_embeddings = self.model.encode(texts)
            except Exception as e:
                logger.error(f"Error encoding texts: {e}")
        
        # Append to documents list
        start_idx = len(self.documents)
        for i, doc in enumerate(documents):
            self.documents.append({
                "id": doc.get("id", f"doc_{start_idx + i}"),
                "text": doc["text"],
                "metadata": doc.get("metadata", {})
            })
        
        # Append to embeddings numpy array
        if new_embeddings is not None:
            import numpy as np
            if self.embeddings is None:
                self.embeddings = np.array(new_embeddings)
            else:
                self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        self.save_index()

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search top-k documents matching the query."""
        if not self.documents:
            return []
        
        k = min(k, len(self.documents))
        
        # If embeddings and model are initialized, do cosine similarity
        if self.initialized and self.model is not None and self.embeddings is not None:
            try:
                import numpy as np
                query_emb = self.model.encode([query])[0]
                # Normalize embeddings for cosine similarity
                norm_query = query_emb / (np.linalg.norm(query_emb) + 1e-10)
                norm_embeddings = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-10)
                
                scores = np.dot(norm_embeddings, norm_query)
                top_indices = np.argsort(scores)[::-1][:k]
                
                results = []
                for idx in top_indices:
                    results.append({
                        "document": self.documents[idx],
                        "score": float(scores[idx])
                    })
                return results
            except Exception as e:
                logger.error(f"Error in vector search: {e}")
        
        # Fallback to simple keyword search
        logger.info("Using keyword search fallback.")
        query_words = query.lower().split()
        scores = []
        for doc in self.documents:
            text = doc["text"].lower()
            score = sum(1 for word in query_words if word in text)
            scores.append(score)
            
        import numpy as np
        top_indices = np.argsort(scores)[::-1][:k]
        results = []
        for idx in top_indices:
            results.append({
                "document": self.documents[idx],
                "score": float(scores[idx])
            })
        return results

    def delete_document(self, doc_id: str) -> None:
        """Delete document by ID."""
        import numpy as np
        idx_to_remove = -1
        for idx, doc in enumerate(self.documents):
            if doc["id"] == doc_id:
                idx_to_remove = idx
                break
        
        if idx_to_remove != -1:
            self.documents.pop(idx_to_remove)
            if self.embeddings is not None:
                self.embeddings = np.delete(self.embeddings, idx_to_remove, axis=0)
            self.save_index()

    def clear_index(self) -> None:
        """Clear all indexed documents."""
        self.documents = []
        self.embeddings = None
        self.save_index()

    def get_index_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.documents),
            "initialized": self.initialized,
            "dimension": self.embeddings.shape[1] if self.embeddings is not None else 0
        }
