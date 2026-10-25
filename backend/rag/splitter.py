import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.rag.splitter")


class TextSplitter:
    """
    Structure-aware TextSplitter for Markdown, Source Code, and Plain Text.
    - Preserves Markdown H1, H2, H3 headings and section titles
    - Preserves Python / JS / TS function, class, and method symbol boundaries
    - Default chunk size: 1000 characters with 200 overlap
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

    def split_markdown(self, text: str, filename: str = "doc.md") -> List[Dict[str, Any]]:
        """
        Structure-aware Markdown splitter. Splits along #, ##, ### section headings.
        """
        lines = text.splitlines()
        chunks = []
        current_heading = "Overview"
        current_lines: List[str] = []
        line_start = 1

        for idx, line in enumerate(lines, start=1):
            if re.match(r"^#{1,3}\s+", line):
                if current_lines:
                    chunk_text = "\n".join(current_lines).strip()
                    if chunk_text:
                        chunks.append({
                            "text": f"# {current_heading}\n{chunk_text}",
                            "heading": current_heading,
                            "section": current_heading,
                            "line_start": line_start,
                            "line_end": idx - 1,
                        })
                current_heading = re.sub(r"^#{1,3}\s+", "", line).strip()
                current_lines = []
                line_start = idx
            else:
                current_lines.append(line)

        if current_lines:
            chunk_text = "\n".join(current_lines).strip()
            if chunk_text:
                chunks.append({
                    "text": f"# {current_heading}\n{chunk_text}",
                    "heading": current_heading,
                    "section": current_heading,
                    "line_start": line_start,
                    "line_end": len(lines),
                })

        if not chunks:
            # Fallback to standard character split
            raw_chunks = self.split_text(text)
            return [{"text": c, "heading": "General", "section": "General"} for c in raw_chunks]

        return chunks

    def split_code(self, code_text: str, filename: str = "app.py") -> List[Dict[str, Any]]:
        """
        Structure-aware Code splitter. Identifies functions, classes, and top-level definitions.
        """
        lines = code_text.splitlines()
        chunks = []
        ext = filename.split(".")[-1].lower() if "." in filename else "py"
        language_map = {"py": "python", "js": "javascript", "ts": "typescript", "sql": "sql"}
        lang = language_map.get(ext, ext)

        current_symbol = "module"
        current_lines: List[str] = []
        line_start = 1

        symbol_pattern = (
            r"^(def\s+[A-Za-z0-9_]+|class\s+[A-Za-z0-9_]+|function\s+[A-Za-z0-9_]+|const\s+[A-Za-z0-9_]+\s*=\s*\([^)]*\)\s*=>)"
            if ext == "py"
            else r"^(function\s+[A-Za-z0-9_]+|class\s+[A-Za-z0-9_]+|export\s+(default\s+)?(function|class|const)\s+[A-Za-z0-9_]+)"
        )

        for idx, line in enumerate(lines, start=1):
            if re.match(symbol_pattern, line.strip()):
                if current_lines:
                    chunk_text = "\n".join(current_lines).strip()
                    if chunk_text:
                        chunks.append({
                            "text": chunk_text,
                            "symbol": current_symbol,
                            "language": lang,
                            "line_start": line_start,
                            "line_end": idx - 1,
                        })
                current_symbol = line.strip().split("(")[0].replace("def ", "").replace("class ", "").replace("function ", "").strip()
                current_lines = [line]
                line_start = idx
            else:
                current_lines.append(line)

        if current_lines:
            chunk_text = "\n".join(current_lines).strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "symbol": current_symbol,
                    "language": lang,
                    "line_start": line_start,
                    "line_end": len(lines),
                })

        if not chunks:
            raw_chunks = self.split_text(code_text)
            return [{"text": c, "symbol": "module", "language": lang} for c in raw_chunks]

        return chunks

    def split_documents(self, documents: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Splits a map of filename -> text content into structured document chunk dicts
        with metadata (source, chunk_index, text, heading, symbol).
        """
        all_chunks = []
        for filename, content in documents.items():
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext == "md":
                struct_chunks = self.split_markdown(content, filename)
            elif ext in ("py", "js", "ts", "sql"):
                struct_chunks = self.split_code(content, filename)
            else:
                raw_chunks = self.split_text(content)
                struct_chunks = [{"text": c} for c in raw_chunks]

            for idx, c_dict in enumerate(struct_chunks):
                all_chunks.append({
                    "id": f"{filename}_chunk_{idx}",
                    "source": filename,
                    "chunk_index": idx,
                    "text": c_dict.get("text", ""),
                    "heading": c_dict.get("heading", ""),
                    "section": c_dict.get("section", ""),
                    "symbol": c_dict.get("symbol", ""),
                    "language": c_dict.get("language", ""),
                    "line_start": c_dict.get("line_start"),
                    "line_end": c_dict.get("line_end"),
                })

        logger.info(f"Split {len(documents)} document(s) into {len(all_chunks)} structure-aware chunk(s)")
        return all_chunks


global_text_splitter = TextSplitter()
