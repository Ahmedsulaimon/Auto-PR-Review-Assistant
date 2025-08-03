from fastapi import FastAPI, Header, HTTPException, Request
import json
from aioredis import from_url
from dotenv import load_dotenv
import hmac, hashlib, os
from pathlib import Path

# Explicitly point to root .env
# env_path = Path(__file__).resolve().parents[1] / ".env"
# load_dotenv(dotenv_path=env_path)



app = FastAPI()


@app.post("/webhook")
async def handle_webhook(request: Request, x_hub_signature: str = Header(...)):
        secret = os.getenv("GITHUB_SECRET").encode()
        body = await request.body()
        x_hub_signature = request.headers.get("x-hub-signature-256")

        expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_signature, x_hub_signature):
            raise HTTPException(401, "Invalid signature")

        payload = await request.json()
        pr = payload.get("pull_request")
        if not pr:
            return {"ignored": True}
        redis_url = os.getenv("REDIS_URL_DOCKER")
        print(f"Raw Redis URL: '{redis_url}'")
        redis = await from_url(os.getenv("REDIS_URL_DOCKER"))
        job = {
                "repo": payload["repository"]["full_name"],
                "pr_number": pr["number"],
                "action": payload["action"]  # e.g. "opened", "synchronize"
            }
        await redis.lpush("pr-review-queue", json.dumps(job))
        return {"enqueued": job}
#docker compose build --no-cache
#docker compose up
