### Boilerplate: `services/webhook-listener/README.md`


# Webhook Listener Service

## Description
Handles incoming GitHub webhook events.

## Setup
1. `cd services/webhook-listener`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `GITHUB_SECRET`, `REDIS_URL`

## Running
```bash
uvicorn main:app --host 0.0.0.0 --port 8000