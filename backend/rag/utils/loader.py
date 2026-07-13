from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)


class DocumentLoader:

    def __init__(self):
        self.documents_path = (
            Path(__file__).resolve().parent.parent / "documents"
        )

    def load_documents(self):

        documents = []

        if not self.documents_path.exists():
            print("Documents folder not found.")
            return documents

        for file in self.documents_path.iterdir():

            print(f"Checking: {file.name}")

            if file.stat().st_size == 0:
                print(f"Skipping empty file: {file.name}")
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