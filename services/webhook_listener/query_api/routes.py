# query_api/routes.py
from fastapi import Request, HTTPException, Depends
import redis.asyncio as aioredis
import os, json

REDIS_URL = os.getenv("REDIS_URL_DOCKER")

async def get_redis():
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()

def history_key(installation_id: int) -> str:
    return f"pr-review-history:{installation_id}"

def queue_key(installation_id: int) -> str:
    return f"pr-review-queue:{installation_id}"

# 📝 List PRs for an installation
async def list_prs_internal(redis, installation_id: int, limit: int = 10):
    prs = await redis.lrange(history_key(installation_id), -limit, -1)
    return [json.loads(pr) for pr in prs]

# 📝 Show a specific PR
async def show_pr_internal(redis, installation_id: int, pr_number: int):
    prs = await redis.lrange(history_key(installation_id), 0, -1)
    for entry in prs:
        pr = json.loads(entry)
        if pr["pr_number"] == pr_number:
            return pr
    return None

# 📝 Recheck a PR
async def recheck_pr_internal(redis, installation_id: int, pr_number: int):
    prs = await redis.lrange(history_key(installation_id), 0, -1)
    repo = None
    for entry in prs:
        pr = json.loads(entry)
        if pr["pr_number"] == pr_number:
            repo = pr["repo"]
            break
    if not repo:
        return None

    job = {"repo": repo, "pr_number": pr_number, "action": "reopened", "installation_id": installation_id}
    await redis.lpush(queue_key(installation_id), json.dumps(job))
    return {"status": "requeued", "pr_number": pr_number, "repo": repo}


# === Routes ===

from fastapi import APIRouter
router = APIRouter()

@router.get("/prs")
async def list_prs(installation_id: int, limit: int = 10, redis=Depends(get_redis)):
    return await list_prs_internal(redis, installation_id, limit)

@router.get("/prs/{pr_number}")
async def show_pr(pr_number: int, installation_id: int, redis=Depends(get_redis)):
    pr = await show_pr_internal(redis, installation_id, pr_number)
    if not pr:
        raise HTTPException(status_code=404, detail=f"PR #{pr_number} not found")
    return pr

@router.post("/prs/{pr_number}/recheck")
async def recheck_pr(pr_number: int, installation_id: int, redis=Depends(get_redis)):
    result = await recheck_pr_internal(redis, installation_id, pr_number)
    if not result:
        raise HTTPException(status_code=404, detail=f"Repo for PR #{pr_number} not found")
    return result
