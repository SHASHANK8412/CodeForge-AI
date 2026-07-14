from langchain_core.documents import Document

from backend.rag.utils.splitter import DocumentSplitter


def test_splitter_creates_chunks_with_metadata():
    splitter = DocumentSplitter(chunk_size=40, chunk_overlap=0)
    documents = [Document(page_content="alpha beta gamma delta epsilon zeta", metadata={"source": "sample.txt"})]

    chunks = splitter.split_documents(documents)

    assert chunks
    assert chunks[0].metadata["source"] == "sample.txt"
    assert "alpha" in chunks[0].page_content