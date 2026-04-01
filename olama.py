import os

import numpy as np
from openai import OpenAI  # Use the standard OpenAI library

# 1. Setup the client to point to the deployed Ollama endpoint
client = OpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    api_key="ollama"  # Required by the SDK, but ignored by Ollama
)

# 2. Your local docs
documents = [
    "Mixbread AI is a research lab based in Germany.",
    "The mxbai-embed-large model has 335 million parameters.",
    "Ollama allows you to run LLMs and embedding models locally.",
    "Agentic workflows require high-precision retrieval layers."
]

def get_embedding(text, is_query=False):
    # Mixbread's recommended prefix for queries
    prefix = "Represent this sentence for searching relevant passages:\n" if is_query else ""

    # Use the OpenAI-style embeddings.create method
    response = client.embeddings.create(
        model="mxbai-embed-large",
        input=prefix + text
    )
    # OpenAI format returns a list of objects; we take the first embedding
    return response.data[0].embedding

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# --- EXECUTION ---
print("🧠 Generating embeddings via OpenAI SDK (pointing to local Ollama)...")
doc_vectors = [get_embedding(doc) for doc in documents]

query = "Where is the lab located?"
query_vector = get_embedding(query, is_query=True)

# Calculate similarities
print(f"\n🔍 Query: {query}")
print("-" * 30)

results = []
for i, doc_vec in enumerate(doc_vectors):
    score = cosine_similarity(query_vector, doc_vec)
    results.append((score, documents[i]))

# Sort by highest score
results.sort(key=lambda x: x[0], reverse=True)

for score, text in results:
    print(f"[{score:.4f}] {text}")
    