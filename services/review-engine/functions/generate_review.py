import json
import traceback
from openai import OpenAI
import os

llm_client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=os.environ["OPENAI_API_KEY"]
)

async def generate_review(pr_title, chunks):
    prompt = f"Review the following PR: {pr_title}\n\n"
    for chunk in chunks:
        prompt += f"File: {chunk['path']}\n{chunk['hunk']}\n\n"
    prompt += "Provide feedback in a JSON list with: file, comment, and line_number."

    response = llm_client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def parse_review_json(review_output):
                try:
                    return json.loads(review_output)
                except Exception as e:
                    print(f"❌ Failed to parse review output as JSON: {e}")
                    traceback.print_exc()
                    return []
                    
