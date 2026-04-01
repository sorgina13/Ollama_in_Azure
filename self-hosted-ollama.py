import os
import openai

# 1. Point the client to your Docker container
# 'host.docker.internal' is used if your code is also in a container
# 'localhost' is used if your code is running directly on the Mac
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" # Required by SDK, but ignored by Ollama
)

# 2. Call the Mixbread model
response = client.embeddings.create(
    model="mxbai-embed-large",
    input="How do I deploy local models to Foundry?"
)

print(f"Vector Length: {len(response.data[0].embedding)}")    