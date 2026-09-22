import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.rag.loader")


class DocumentLoader:
    """
    DocumentLoader reads and extracts text from multiple document formats:
    - Text/Docs: Markdown (.md), Plain Text (.txt), PDF (.pdf), Word Document (.docx)
    - Data/Configs: JSON (.json), YAML (.yaml, .yml)
    - Code Files: Python (.py), JavaScript (.js), TypeScript (.ts), SQL (.sql), HTML (.html), CSS (.css)
    """

    SUPPORTED_EXTENSIONS = {
        ".md", ".txt", ".pdf", ".docx", ".json",
        ".py", ".js", ".ts", ".sql", ".html", ".css", ".yaml", ".yml"
    }

    BINARY_EXTENSIONS = {
        ".exe", ".dll", ".so", ".zip", ".tar", ".gz", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bin"
    }

    def load_file(self, filepath: str) -> str:
        """Loads and extracts text content from a single file path."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        ext = path.suffix.lower()
        if ext in self.BINARY_EXTENSIONS:
            raise ValueError(f"Binary file format '{ext}' is unsupported for RAG text indexing.")

        if ext in (".md", ".txt", ".py", ".js", ".ts", ".sql", ".html", ".css", ".yaml", ".yml"):
            return path.read_text(encoding="utf-8", errors="ignore")

        elif ext == ".json":
            content = path.read_text(encoding="utf-8", errors="ignore")
            try:
                # Format JSON for clean readable text indexing
                parsed = json.loads(content)
                return json.dumps(parsed, indent=2)
            except Exception:
                return content

        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(path))
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
                return text
            except Exception as e:
                logger.warning(f"Could not parse PDF using pypdf for {filepath}: {e}")
                content = path.read_bytes()
                text_content = "".join(chr(b) for b in content if 32 <= b <= 126 or b in (10, 13))
                return text_content[:5000]

        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(str(path))
                return "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                logger.warning(f"Could not parse DOCX for {filepath}: {e}")
                return path.read_text(encoding="utf-8", errors="ignore")

        elif ext in self.SUPPORTED_EXTENSIONS:
            return path.read_text(encoding="utf-8", errors="ignore")
        else:
            raise ValueError(f"Unsupported file format '{ext}'.")

    def load_directory(self, dir_path: str) -> Dict[str, str]:
        """Loads all supported documents from a target directory into a filename -> text mapping."""
        folder = Path(dir_path)
        documents = {}

        if not folder.exists():
            logger.warning(f"Target document directory does not exist: {dir_path}")
            return documents

        for root, _, files in os.walk(folder):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    full_path = Path(root) / file
                    try:
                        text = self.load_file(str(full_path))
                        if text and text.strip():
                            rel_name = str(full_path.relative_to(folder)).replace("\\", "/")
                            documents[rel_name] = text
                    except Exception as e:
                        logger.error(f"Error loading {file}: {e}")

        logger.info(f"Loaded {len(documents)} document(s) from '{dir_path}'")
        return documents


global_document_loader = DocumentLoader()
