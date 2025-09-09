import asyncio, json, re, os
from redis.asyncio import from_url
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from functions.post_comments import post_pr_comments
from functions.generate_review import generate_review, parse_review_json
import httpx
import traceback
import difflib

async def review_worker():
    print(" Starting review worker...")
    redis_url = os.getenv("REDIS_URL_DOCKER")
    github_token = os.getenv('GITHUB_TOKEN')

   
    if not redis_url:
        print("ERROR: REDIS_URL_DOCKER environment variable is not set!")
        return
    if not github_token:
        print("ERROR: GITHUB_TOKEN environment variable is not set!")
        return

    print(" Attempting to connect to Redis...")
    max_retries = 10
    retry_delay = 1

    redis = None
    for attempt in range(max_retries):
        try:
            redis = await from_url(redis_url.strip(), decode_responses=True)  # ✅ decode strings
            await redis.ping()
            print(f"✅ Connected to Redis at: {redis_url}")
            break
        except Exception as e:
            if redis is not None:
                await redis.close()
                redis = None
            if attempt < max_retries - 1:
                print(f"⚠️ Redis connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
            else:
                print(f"❌ Failed to connect to Redis after {max_retries} attempts: {e}")
                traceback.print_exc()
                return

    print(" Setting up GitHub GraphQL client...")
    try:
        graphql_transport = AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {github_token}"},
            ssl=False
        )
        graphql_client = Client(transport=graphql_transport, fetch_schema_from_transport=True)
        print(" GitHub GraphQL client configured")
    except Exception as e:
        print(f" Failed to setup GraphQL client: {e}")
        traceback.print_exc()
        return

    rest_headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    print(" Review worker is running and waiting for jobs...")
    print("   Listening on queue: pr-review-queue")

    while True:
        try:
            print("⏳ Waiting for job from Redis...")
            response = await redis.brpop("pr-review-queue")

            if not response or len(response) != 2:
                print(f"⚠️ Received invalid or empty response from Redis queue: {response}")
                continue

            queue_name, payload = response
            print(f"📦 Raw job from queue '{queue_name}': {payload}")

            try:
                job = json.loads(payload)
            except Exception as e:
                print(f"❌ Failed to parse job payload as JSON: {e}")
                traceback.print_exc()
                continue

            print(f"✅ Parsed job: {job}")

            # Only process certain PR actions
            valid_actions = ["opened", "synchronize", "reopened", "edited"]
            action = job.get("action", "").lower().strip()
            print(f"🔍 PR action received: '{action}'")

            
           
            if not action:
                print("⚠️ No action in job, skipping...")
                continue
            # Auto-correct to the closest valid action if slightly misspelled
            closest_match = difflib.get_close_matches(action, valid_actions, n=1, cutoff=0.8)
            if closest_match:
                if action != closest_match[0]:
                    print(f"✏️ Corrected action '{action}' → '{closest_match[0]}'")
                action = closest_match[0]

            # Skip closed PRs explicitly
            if action == "closed":
                print("⏭ Skipping closed PR")
                continue
            if action not in valid_actions:
                print(f"❌ Invalid action '{action}' — skipping job")
                continue

            print(f"✅ Normalized PR action: '{action}' — proceeding...")

            repo = job["repo"]
            pr_number = job["pr_number"]
            owner, name = repo.split("/")

            # === 1) Get PR metadata (GraphQL) ===
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
            graphql_variables = {"owner": owner, "name": name, "number": pr_number}
            result = await graphql_client.execute_async(query, variable_values=graphql_variables)

            pr_title = result["repository"]["pullRequest"]["title"]
            pr_url = result["repository"]["pullRequest"]["url"]
            print(f"\n🔍 Reviewing PR #{pr_number}: {pr_title} ({pr_url})")

            # === 2) Get file patches (REST) ===
            async with httpx.AsyncClient() as client:
                rest_url = f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/files"
                resp = await client.get(rest_url, headers=rest_headers)
                files = resp.json()

            # === 3) Parse patch hunks ===
            chunks = []
            for f in files:
                patch = f.get("patch")
                if not patch:
                    continue

                parts = re.split(r"(^@@.*@@\n)", patch, flags=re.MULTILINE)
                if len(parts) <= 1:  
                    # No hunk headers found → use whole patch
                    chunks.append({
                        "path": f["filename"],
                        "hunk": patch
                    })
                else:
            
                    for i in range(1, len(parts), 2):
                        header = parts[i]
                        body = parts[i + 1]
                        chunks.append({
                            "path": f["filename"],
                            "hunk": header + body

                        })
             
            # === 4)  Call LLM and post comments here ===
            review_output = await generate_review(pr_title, chunks)
            print(f"💬 Generated review output for PR #{pr_number}")
            # Parse GPT-4.1 output into comment objects
            comments = parse_review_json(review_output)
            print(f"💬 Generated {len(comments)} comments for PR #{pr_number}")
            # Post to GitHub
            await post_pr_comments(owner, name, pr_number, comments, github_token)
            print(f"✅ Posted {len(comments)} comments to PR #{pr_number}")

            history_entry = {
                "repo": repo,
                "pr_number": pr_number,
                "title": pr_title,
                "url": pr_url, 
                "status": "done",
                "comments": comments,  # raw parsed comments
            }
            await redis.rpush("pr-review-history", json.dumps(history_entry))
           
            await redis.ltrim("pr-review-history", -100, -1)
            print(f"📝 Saved PR #{pr_number} review to history.")
        except Exception as e:
            print(f"💥 Error processing job: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(review_worker())

 #docker exec -it infrastructure-review-engine-1 bash
 #python engine.py

 