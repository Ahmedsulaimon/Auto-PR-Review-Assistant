import os
print("DEBUG OpenAI key prefix:", os.getenv("OPENAI_API_KEY", "test8")[:8])
