from rag.utils.loader import DocumentLoader
from rag.utils.splitter import DocumentSplitter
from rag.utils.vector_store import VectorStore


loader = DocumentLoader()
documents = loader.load_documents()

splitter = DocumentSplitter()
chunks = splitter.split_documents(documents)

vector_store = VectorStore()

vector_store.add_documents(chunks)

print("\nDatabase Created Successfully")

print("\nSearching...\n")

results = vector_store.similarity_search(
    "What programming languages does Shashank know?"
)

for i, doc in enumerate(results):

    print("=" * 60)
    print(f"Result {i + 1}")
    print(doc.page_content)
    print(doc.metadata)