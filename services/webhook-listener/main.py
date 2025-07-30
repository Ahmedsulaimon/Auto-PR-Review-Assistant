from fastapi import FastAPI, Header, HTTPException, Request

from dotenv import load_dotenv
load_dotenv()

import hmac, hashlib, os

app = FastAPI()

# @app.post("/webhook")
# async def handle_webhook(request: Request):
#     payload = await request.json()
#     print("🔔 Webhook received!")
#     print(payload)  # optional: see full data
#     return {"status": "ok"}

@app.post("/webhook")
async def handle_webhook(request: Request, x_hub_signature: str = Header(...)):
   secret = os.getenv("GITHUB_SECRET").encode()
   body = await request.body()
   x_hub_signature = request.headers.get("x-hub-signature-256")

   expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

   if not hmac.compare_digest(expected_signature, x_hub_signature):
    raise HTTPException(401, "Invalid signature")

   payload = await request.json()
    # TODO: enqueue payload['pull_request'] event

   print("🔔 Webhook received!")
   print(payload)  # optional: see full data
   return {"status": "ok"}
#C:\Users\pc\AppData\Local/ngrok/ngrok.yml
#uvicorn main:app --host 0.0.0.0 --port 8000