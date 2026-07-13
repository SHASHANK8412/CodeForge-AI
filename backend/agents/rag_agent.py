from rag.rag_pipeline import RAGPipeline


class RAGAgent:

    def __init__(self):
        self.rag = RAGPipeline()

    def run(self, query):

        return self.rag.ask(query)