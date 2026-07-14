from backend.agents.rag_agent import RAGAgent


class FakePipeline:
    def __init__(self):
        self.questions = []

    def ask(self, question):
        self.questions.append(question)
        return f"answer::{question}"


def test_rag_agent_delegates_to_pipeline():
    agent = RAGAgent()
    fake_pipeline = FakePipeline()
    agent.rag = fake_pipeline

    result = agent.run("What programming languages does Shashank know?")

    assert result == "answer::What programming languages does Shashank know?"
    assert fake_pipeline.questions == ["What programming languages does Shashank know?"]