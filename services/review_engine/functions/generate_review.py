# import json
# import traceback
# from openai import OpenAI
# import os

# llm_client = OpenAI(
#     base_url="https://models.github.ai/inference",
#     api_key=os.environ["OPENAI_API_KEY"]
# )

# def get_client():
#     api_key = os.environ.get("OPENAI_API_KEY", "fake-key-for-tests")
#     return OpenAI(api_key=api_key)

# async def generate_review(pr_title, chunks):
#     client = get_client()
#     prompt = f"Review the following PR: {pr_title}\n\n"
#     for chunk in chunks:
#         prompt += f"File: {chunk['path']}\n{chunk['hunk']}\n\n"
#     prompt += """
#         Return ONLY valid JSON (no explanations, no text outside JSON).
#         Format:
#         [
#         { "file": "filename.ext", "comment": "your feedback here", "line_number": 42 }
#         ]
#         """
#     response = llm_client.chat.completions.create(
#         model="gpt-4.1",
#         messages=[{"role": "user", "content": prompt}],
#     )

#     return response.choices[0].message.content.strip()

# def parse_review_json(review_output):
#     try:
#         data = json.loads(review_output)
#         if isinstance(data, dict) and "output" in data:
#             data = data["output"]

#         if isinstance(data, list):
#             normalized = []
#             for c in data:
#                 normalized.append({
#                     "body": c.get("body") or c.get("comment") or "(no text)",
#                     "path": c.get("path") or c.get("file") or "UnknownFile",
#                     "line": c.get("line") or c.get("line_number"),
#                 })
#             return normalized

#         print("⚠️ Unexpected JSON shape:", data)
#         return []
#     except Exception as e:
#         print(f"❌ Invalid JSON from LLM: {e}")
#         print(f"⚠️ Raw output was:\n{review_output}")
#         traceback.print_exc()
#         return []

import os
import httpx
import json
import traceback

GITHUB_MODELS_URL = "https://models.github.ai/inference/v1/chat/completions"

async def generate_review(pr_title, chunks):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    prompt = f"Review the following PR: {pr_title}\n\n"
    for chunk in chunks:
        prompt += f"File: {chunk['path']}\n{chunk['hunk']}\n\n"
    prompt += """
        Return ONLY valid JSON (no explanations, no text outside JSON).
        Format:
        [
        { "file": "filename.ext", "comment": "your feedback here", "line_number": 42 }
        ]
        """

    headers = {
        "Authorization": f"token {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": "gpt-4.1",
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(GITHUB_MODELS_URL, headers=headers, json=body)

        if resp.status_code != 200:
            raise RuntimeError(f"GitHub Models error {resp.status_code}: {resp.text}")

        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


def parse_review_json(review_output):
    try:
        data = json.loads(review_output)
        if isinstance(data, dict) and "output" in data:
            data = data["output"]

        if isinstance(data, list):
            normalized = []
            for c in data:
                normalized.append({
                    "body": c.get("body") or c.get("comment") or "(no text)",
                    "path": c.get("path") or c.get("file") or "UnknownFile",
                    "line": c.get("line") or c.get("line_number"),
                })
            return normalized

        print("⚠️ Unexpected JSON shape:", data)
        return []
    except Exception as e:
        print(f"❌ Invalid JSON from LLM: {e}")
        print(f"⚠️ Raw output was:\n{review_output}")
        traceback.print_exc()
        return []

#debugging openAI key
                    
