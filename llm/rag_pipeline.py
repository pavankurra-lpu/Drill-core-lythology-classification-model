import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from llm.vector_store import FAISSVectorStore
from llm.assistant import GeologicalAssistant

logger = logging.getLogger(__name__)

@dataclass
class RAGResponse:
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float

class RAGPipeline:
    def __init__(self, vector_store: FAISSVectorStore, assistant: GeologicalAssistant):
        self.vector_store = vector_store
        self.assistant = assistant

    def process_pdf(self, file_path: str, metadata: dict) -> int:
        """Extract text from PDF, chunk it, and add to the vector store."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return 0
        
        extracted_text = ""
        
        # Try PyMuPDF / fitz
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            for page in doc:
                extracted_text += page.get_text() + "\n"
            logger.info("Extracted text using PyMuPDF.")
        except ImportError:
            # Try pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            extracted_text += text + "\n"
                logger.info("Extracted text using pdfplumber.")
            except ImportError:
                # Try PyPDF2
                try:
                    import PyPDF2
                    with open(file_path, "rb") as f:
                        pdf = PyPDF2.PdfReader(f)
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                extracted_text += text + "\n"
                    logger.info("Extracted text using PyPDF2.")
                except Exception as e:
                    logger.warning(f"Could not load PDF libraries. Reading as plain text. Error: {e}")
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            extracted_text = f.read()
                    except Exception as ex:
                        logger.error(f"Failed to read file: {ex}")
                        return 0

        if not extracted_text.strip():
            logger.warning(f"No text extracted from PDF: {file_path}")
            return 0

        # Chunk the text (e.g. 1000 characters with 200 character overlap)
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        i = 0
        while i < len(extracted_text):
            chunk = extracted_text[i:i + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
            i += (chunk_size - overlap)

        # Prepare document dicts
        documents_to_add = []
        for idx, chunk in enumerate(chunks):
            doc_meta = metadata.copy()
            doc_meta["chunk_id"] = idx
            doc_meta["source_file"] = os.path.basename(file_path)
            documents_to_add.append({
                "text": chunk,
                "metadata": doc_meta
            })

        logger.info(f"Adding {len(documents_to_add)} chunks from {file_path} to vector store.")
        self.vector_store.add_documents(documents_to_add)
        return len(documents_to_add)

    def query(self, question: str, k: int = 5) -> RAGResponse:
        """Retrieve relevant context, generate answer, and return results."""
        results = self.vector_store.search(question, k=k)
        
        context_parts = []
        sources = []
        
        for res in results:
            doc = res["document"]
            context_parts.append(doc["text"])
            sources.append({
                "source": doc["metadata"].get("source_file", "Unknown"),
                "snippet": doc["text"][:200] + "...",
                "score": res["score"]
            })
            
        context = "\n---\n".join(context_parts)
        
        # Call the LLM assistant
        try:
            answer = self.assistant.answer_question(question, context=context)
        except Exception as e:
            logger.error(f"Error in LLM assistant query: {e}")
            answer = f"Error generating answer: {str(e)}"
            
        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=float(results[0]["score"]) if results else 0.0
        )

    def semantic_search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        results = self.vector_store.search(query, k=k)
        formatted_results = []
        for res in results:
            doc = res["document"]
            formatted_results.append({
                "id": doc.get("id"),
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": res["score"]
            })
        return formatted_results

    def clear_index(self) -> None:
        self.vector_store.clear_index()
