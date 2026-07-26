import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.rag.splitter")


class TextSplitter:
    """
    TextSplitter divides long documents into overlapping text chunks for embedding generation.
    - Default chunk size: 1000 characters
    - Default overlap: 200 characters
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_text(self, text: str) -> List[str]:
        """Splits a raw text string into chunks of size chunk_size with overlap."""
        if not text or not text.strip():
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end == text_len:
                break

            start += self.chunk_size - self.overlap

        return chunks

    def split_documents(self, documents: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Splits a map of filename -> text content into structured document chunk dicts
        with metadata (source, chunk_index, text).
        """
        all_chunks = []
        for filename, content in documents.items():
            raw_chunks = self.split_text(content)
            for idx, chunk in enumerate(raw_chunks):
                all_chunks.append({
                    "id": f"{filename}_chunk_{idx}",
                    "source": filename,
                    "chunk_index": idx,
                    "text": chunk
                })

        logger.info(f"Split {len(documents)} document(s) into {len(all_chunks)} chunk(s)")
        return all_chunks
