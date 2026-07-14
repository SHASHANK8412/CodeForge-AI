from types import SimpleNamespace

from backend.rag.utils.vector_store import VectorStore


class FakeDB:
    def __init__(self):
        self.added = None
        self.search_query = None
        self.search_k = None

    def add_documents(self, chunks, ids=None):
        self.added = (chunks, ids)

    def similarity_search(self, query, k=3):
        self.search_query = query
        self.search_k = k
        return [SimpleNamespace(page_content="alpha", metadata={"source": "doc.txt"})]


def test_vector_store_adds_documents_and_searches(monkeypatch):
    store = VectorStore()
    fake_db = FakeDB()
    monkeypatch.setattr(store, "db", fake_db)

    chunks = [SimpleNamespace(page_content="alpha", metadata={"source": "doc.txt", "page": 1})]

    store.add_documents(chunks)
    results = store.similarity_search("alpha", k=2)

    assert fake_db.added is not None
    assert fake_db.search_query == "alpha"
    assert fake_db.search_k == 2
    assert results[0].metadata["source"] == "doc.txt"