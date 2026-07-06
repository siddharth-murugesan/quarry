from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "How do I cancel my subscription?",
    "I want to end my subscription please",
    "What's the weather in Tokyo?",
]

embeddings = model.encode(sentences)
print(f"Shape: {embeddings.shape}")
print(f"First vector, first 5 dims: {embeddings[0][:5]}")
