from rag.rag_pipeline import RAGPipeline


rag = RAGPipeline()

question = "What programming languages does Shashank know?"

answer = rag.ask(question)

print("\n" + "=" * 70)
print("FINAL ANSWER")
print("=" * 70)
print(answer)