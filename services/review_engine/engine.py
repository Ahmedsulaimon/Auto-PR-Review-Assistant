import json, re, os, traceback, difflib, signal, asyncio
from redis.asyncio import from_url
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from fastapi import FastAPI
import httpx

from services.review_engine.functions.post_comments import post_pr_comments
from services.review_engine.functions.generate_review import generate_review, parse_review_json
from services.review_engine.auth import get_installation_token

app = FastAPI()
_worker_task: asyncio.Task | None = None
async def review_worker():
    try:
        print("🚀 Starting review worker...")
        redis_url = os.getenv("REDIS_URL_DOCKER")
        openai_key = os.getenv("OPENAI_API_KEY")

        if not redis_url:
            print("❌ REDIS_URL_DOCKER not set")
            return
        if not openai_key:
            print("❌ OPENAI_API_KEY not set")
            return

        # Connect to Redis with retries
        redis = None
        max_retries, retry_delay = 10, 1
        for attempt in range(max_retries):
            try:
                redis = await from_url(redis_url.strip(), decode_responses=True)
                await redis.ping()
                print(f"✅ Connected to Redis at: {redis_url}")
                break
            except Exception as e:
                if redis:
                    await redis.close()
                    redis = None
                if attempt < max_retries - 1:
                    print(f"⚠️ Redis attempt {attempt+1} failed, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)
                else:
                    print(f"❌ Could not connect to Redis: {e}")
                    traceback.print_exc()
                    return

        print("👂 Listening for jobs...")

        while True:
            try:

                # 🔑 Instead of hardcoding, block on ANY pr-review-queue
                # Use pattern with BRPOP for all installations
                keys = [key async for key in redis.scan_iter("pr-review-queue:*")]
                if not keys:
                    await asyncio.sleep(1)
                    continue

                response = await redis.brpop(*keys)

                if not response or len(response) != 2:
                    print(f"⚠️ Invalid response from queue: {response}")
                    continue

                queue_name, payload = response
                try:
                    job = json.loads(payload)
                except Exception:
                    print("❌ Failed to parse job JSON")
                    traceback.print_exc()
                    continue

                action = job.get("action", "").lower().strip()
                valid_actions = ["opened", "synchronize", "reopened", "edited"]
                if action not in valid_actions:
                    continue

                repo, pr_number = job["repo"], job["pr_number"]
                owner, name = repo.split("/")
                
                installation_id = job.get("installation_id")
                if not installation_id:
                    print("❌ No installation_id in job payload")
                    continue


                # === fetch fresh GitHub installation token ===
                github_token = await get_installation_token(installation_id)

                async def run_github_query():
                    graphql_transport = AIOHTTPTransport(
                        url="https://api.github.com/graphql",
                        headers={"Authorization": f"Bearer {github_token}"}
                    )
                    graphql_client = Client(
                        transport=graphql_transport,
                        fetch_schema_from_transport=True,
                    )
                    query = gql(
                        """
                        query($owner: String!, $name: String!, $number: Int!) {
                          repository(owner: $owner, name: $name) {
                            pullRequest(number: $number) {
                              id
                              title
                              url
                            }
                          }
                        }
                        """
                    )
                    return await graphql_client.execute_async(
                        query, variable_values={"owner": owner, "name": name, "number": pr_number}
                    )

                # === retry once on 401 ===
                try:
                    result = await run_github_query()
                except Exception as e:
                    if "401" in str(e):
                        print("⚠️ GitHub token expired, refreshing...")
                        github_token = await get_installation_token(installation_id)
                        result = await run_github_query()
                    else:
                        raise

                pr_title = result["repository"]["pullRequest"]["title"]
                pr_url = result["repository"]["pullRequest"]["url"]

                # === changed files via REST ===
                rest_headers = {
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/files",
                        headers=rest_headers,
                    )
                    if resp.status_code == 401:
                        print("⚠️ REST token expired, refreshing...")
                        github_token = await get_installation_token(installation_id)
                        rest_headers["Authorization"] = f"Bearer {github_token}"
                        resp = await client.get(
                            f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/files",
                            headers=rest_headers,
                        )
                    files = resp.json()

                # === parse patches ===
                chunks = []
                for f in files:
                    patch = f.get("patch")
                    if not patch:
                        continue
                    parts = re.split(r"(^@@.*@@\n)", patch, flags=re.MULTILINE)
                    if len(parts) <= 1:
                        chunks.append({"path": f["filename"], "hunk": patch})
                    else:
                        for i in range(1, len(parts), 2):
                            chunks.append({"path": f["filename"], "hunk": parts[i] + parts[i + 1]})

                # === generate & post review ===
                review_output = await generate_review(pr_title, chunks)
                comments = parse_review_json(review_output)
                await post_pr_comments(owner, name, pr_number, comments, github_token, installation_id)

                 # 🔑 Store into history namespace
                history_key = f"pr-review-history:{installation_id}"
                history_entry = {
                    "repo": repo,
                    "pr_number": pr_number,
                    "title": pr_title,
                    "url": pr_url,
                    "status": "done",
                    "comments": comments,
                }
                await redis.rpush(history_key, json.dumps(history_entry))
                await redis.ltrim(history_key, -100, -1)

                print(f"✅ Processed PR #{pr_number} for installation {installation_id}")
                     

            except Exception as e:
                print(f"💥 Error in job loop: {e}")
                traceback.print_exc()
    except asyncio.CancelledError:
        print("🔹 Review worker stopped gracefully.")



@app.on_event("startup")
async def startup_event():
    global _worker_task
    loop = asyncio.get_event_loop()
    _worker_task = loop.create_task(review_worker())
    print("✅ Worker task started")


@app.on_event("shutdown")
async def shutdown_event():
    global _worker_task
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            print("Worker cancelled on shutdown")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.review_engine.engine:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=1,
    )
