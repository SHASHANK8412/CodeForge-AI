from backend.services.ollama_service import OllamaService

service = OllamaService()

response = service.generate("Hello")

print(response)