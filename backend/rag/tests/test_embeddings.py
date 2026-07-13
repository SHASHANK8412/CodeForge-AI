from rag.utils.loader import DocumentLoader
from rag.utils.splitter import DocumentSplitter
from rag.utils.embeddings import EmbeddingGenerator


loader = DocumentLoader()
documents = loader.load_documents()

splitter = DocumentSplitter()
chunks = splitter.split_documents(documents)

embedding_generator = EmbeddingGenerator()

embeddings = embedding_generator.embed_documents(chunks)
print("=" * 60)
print("Embedding Dimension:", len(embeddings[0]))
print("=" * 60)

print("\nFirst 10 Values:\n")

for value in embeddings[0][:10]:
    print(value)