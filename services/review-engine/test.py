from openai import OpenAI
import os

client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=os.environ["OPENAI_API_KEY"]
)

models = client.models.list()
for m in models.data:
    print(m.id)
