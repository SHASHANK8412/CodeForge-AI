from backend.agents.rag_agent import RAGAgent

agent = RAGAgent()

questions = [
    "What programming languages does Shashank know?",
    "What databases are mentioned?",
    "What AI frameworks are listed?",
    "Tell me about the certifications.",
    "Which frontend technologies are mentioned?"
]

for question in questions:
    print("=" * 70)
    print("Question:", question)
    print()

    answer = agent.run(question)

    print("Answer:")
    print(answer)
    print()