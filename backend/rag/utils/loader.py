from pathlib import Path
from typing import Iterable

from langchain_community.document_loaders import PyPDFLoader, TextLoader


class DocumentLoader:

    def __init__(self):
        self.documents_path = (
            Path(__file__).resolve().parent.parent / "documents"
        )

    def load_paths(self, file_paths: Iterable[Path | str]):

        documents = []

        for file_path in file_paths:
            file = Path(file_path)

            if not file.exists() or file.stat().st_size == 0:
                continue

            try:

                if file.suffix.lower() == ".pdf":

                    loader = PyPDFLoader(str(file))
                    documents.extend(loader.load())

                elif file.suffix.lower() in [".txt", ".md"]:

                    loader = TextLoader(str(file), encoding="utf-8")
                    documents.extend(loader.load())

            except Exception as e:
                print(f"Failed to load {file.name}: {e}")

        return documents

    def load_documents(self):

        if not self.documents_path.exists():
            print("Documents folder not found.")
            return []

        return self.load_paths(self.documents_path.iterdir())


if __name__ == "__main__":

    print("=" * 50)
    print("Starting Document Loader...")
    print("=" * 50)

    loader = DocumentLoader()

    docs = loader.load_documents()

    print(f"\nLoaded {len(docs)} document(s).\n")

    for i, doc in enumerate(docs):

        print(f"Document {i + 1}")
        print(doc.metadata)
        print(doc.page_content[:200])
        print("-" * 50)