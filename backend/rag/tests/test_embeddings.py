from types import SimpleNamespace

from backend.rag.utils.embeddings import EmbeddingGenerator


class DummyEmbeddingModel:
    def embed_documents(self, texts):
        return [[float(len(text)) for _ in range(4)] for text in texts]

    def embed_query(self, query):
        return [float(len(query)) for _ in range(4)]


def test_embedding_generator_returns_embeddings(monkeypatch):
    generator = EmbeddingGenerator()
    monkeypatch.setattr(generator, "embedding_model", DummyEmbeddingModel())

    chunks = [SimpleNamespace(page_content="alpha"), SimpleNamespace(page_content="beta")]

    embeddings = generator.embed_documents(chunks)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 4
    assert generator.embed_query("hello") == [5.0, 5.0, 5.0, 5.0]