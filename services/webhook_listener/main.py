from fastapi import FastAPI, Header, HTTPException, Request
import json
from redis.asyncio import from_url
import hmac, hashlib, os
import sys

   
app = FastAPI()


@app.post("/webhook")
async def handle_webhook(request: Request):
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
        print(f"Connecting to Redis at {redis_url}", flush=True)

        redis = await from_url(redis_url, decode_responses=True)
        await redis.ping()# Test connection
        job = {
                "repo": payload["repository"]["full_name"],
                "pr_number": pr["number"],
                "action": payload["action"]  # e.g. "opened", "synchronize"
            }
        push_result = await redis.lpush("pr-review-queue", json.dumps(job))
        print(f"LPUSH result: {push_result}", flush=True)

        await redis.close()
        print(f" Enqueued PR job: {job}", file=sys.stdout, flush=True)

        return {"enqueued": job}
#docker compose build --no-cache
#docker compose up
