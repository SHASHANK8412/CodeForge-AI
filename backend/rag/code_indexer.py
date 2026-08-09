import os
import logging
from pathlib import Path
from typing import Dict, Any, List

from backend.rag.splitter import global_text_splitter
from backend.rag.embedding_service import global_embedding_service
from backend.rag.vector_store import global_vector_store
from backend.rag.models import DocumentType, RetrievalDomain

logger = logging.getLogger("aiforge.rag.code_indexer")


class GeneratedCodeIndexer:
    """
    Indexes generated source code files into the project vector store after assembly.
    Preserves code-aware metadata (path, language, symbol, line range).
    """

    def index_generated_code(
        self,
        project_id: str,
        files_map: Dict[str, str]
    ) -> int:
        """
        Indexes a map of relative_filepath -> source_code_content into project vector store.
        """
        if not files_map:
            return 0

        chunks_to_index = []
        embeddings_to_index = []

        for rel_path, content in files_map.items():
            if not content or not content.strip():
                continue

            ext = rel_path.rsplit(".", 1)[-1].lower() if "." in rel_path else ""
            if ext not in ("py", "js", "ts", "jsx", "tsx", "sql", "html", "css", "json", "md"):
                continue

            struct_chunks = global_text_splitter.split_code(content, rel_path) if ext in ("py", "js", "ts", "sql", "jsx", "tsx") else global_text_splitter.split_markdown(content, rel_path)

            for idx, c_dict in enumerate(struct_chunks):
                chunk_id = f"{project_id}_code_{rel_path.replace('/', '_')}_{idx}"
                text = c_dict.get("text", "")
                emb = global_embedding_service.embed_document(text)

                doc_meta = {
                    "id": chunk_id,
                    "source": rel_path,
                    "project_id": project_id,
                    "domain": RetrievalDomain.REPOSITORY.value,
                    "document_type": DocumentType.CODE.value,
                    "text": text,
                    "chunk_index": idx,
                    "path": rel_path,
                    "symbol": c_dict.get("symbol", "module"),
                    "language": c_dict.get("language", ext),
                    "line_start": c_dict.get("line_start"),
                    "line_end": c_dict.get("line_end"),
                    "version": "1.0",
                }
                chunks_to_index.append(doc_meta)
                embeddings_to_index.append(emb)

        if chunks_to_index:
            global_vector_store.add_documents(chunks_to_index, embeddings_to_index, project_id=project_id)

        logger.info(f"GeneratedCodeIndexer indexed {len(chunks_to_index)} code chunk(s) for project '{project_id}'")
        return len(chunks_to_index)


global_code_indexer = GeneratedCodeIndexer()


def index_generated_code(project_id: str, files_map: Dict[str, str]) -> int:
    return global_code_indexer.index_generated_code(project_id, files_map)
