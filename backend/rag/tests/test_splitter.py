from rag.utils.loader import DocumentLoader
from rag.utils.splitter import DocumentSplitter


loader = DocumentLoader()

documents = loader.load_documents()

splitter = DocumentSplitter()

chunks = splitter.split_documents(documents)

for i, chunk in enumerate(chunks):

    print(f"\nChunk {i+1}")

    print("-"*50)

    print(chunk.page_content[:300])

    print(chunk.metadata)