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
    key = history_key(installation_id)
    prs = await redis.lrange(key, -limit, -1)
    
    if not prs:
        return []  # Return empty list, not None
    
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
    repo, stored_installation_id = None, None
    for entry in prs:
        pr = json.loads(entry)
        if pr["pr_number"] == pr_number:
            repo = pr["repo"]
            stored_installation_id = pr["installation_id"]
            break
    if not repo:
        return None

    job = {
        "repo": repo,
        "pr_number": pr_number,
        "action": "reopened",
        "installation_id": stored_installation_id,
    }
    await redis.lpush(queue_key(stored_installation_id), json.dumps(job))
    return {"status": "requeued", "pr_number": pr_number, "repo": repo}


# === Routes ===

from fastapi import APIRouter
router = APIRouter()

@router.get("/prs")
async def list_prs(installation_id: int, limit: int = 10, redis=Depends(get_redis)):
    prs = await list_prs_internal(redis, installation_id, limit)
    # Return empty list instead of letting it fail
    return prs if prs else []

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
