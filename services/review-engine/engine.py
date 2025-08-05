import asyncio, json, re, os
from aioredis import from_url
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import httpx

async def review_worker():
    print(" Starting review worker...")
    redis_url = os.getenv("REDIS_URL_DOCKER")
    github_token = os.getenv('GITHUB_TOKEN')

    print(f"📋 Environment check:")
    print(f"  - Redis URL: {' Set' if redis_url else ' Missing'}")
    print(f"  - GitHub Token: {' Set' if github_token else ' Missing'}")

    if not redis_url:
        print("ERROR: REDIS_URL_DOCKER environment variable is not set!")
        return
    if not github_token:
        print("ERROR: GITHUB_TOKEN environment variable is not set!")
        return
    print(" Attempting to connect to Redis...")
    try:
        redis = await from_url(redis_url.strip())
        # Test the connection
        await redis.ping()
        print(f" Connected to Redis at: {redis_url}")
    except Exception as e:
        print(f" Failed to connect to Redis: {e}")
        import traceback
        traceback.print_exc()
        return
    print(" Setting up GitHub GraphQL client...")
    # Setup GraphQL client
   
    if not github_token:
        print("ERROR: GITHUB_TOKEN environment variable is not set!")
        return
    try:
        # Setup GraphQL client        
        graphql_transport = AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {github_token}"},
            ssl=False  # Disable SSL warning
        )
        graphql_client = Client(transport=graphql_transport, fetch_schema_from_transport=True)
        print(" GitHub GraphQL client configured")
    except Exception as e:
        print(f" Failed to setup GraphQL client: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Setup REST headers
    rest_headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    print(" Review worker is running and waiting for jobs...")

    while True:
      try:
        print("⏳ Waiting for job from Redis...")
        _, payload = await redis.brpop("pr-review-queue")
        job = json.loads(payload)
        print(f" Got job from Redis: {job}")

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
        print(f"\n Reviewing PR #{pr_number}: {pr_title} ({pr_url})")

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
            # split by diff hunk header (e.g., @@ -1,2 +1,2 @@)
            parts = re.split(r"(^@@.*@@\n)", patch, flags=re.MULTILINE)
            for i in range(1, len(parts), 2):
                header = parts[i]
                body = parts[i+1]
                chunks.append({
                    "path": f["filename"],
                    "hunk": header + body
                })

        print(f" Prepared {len(chunks)} hunks for PR #{pr_number}")

        # === 4) TODO: Call LLM and post comments here ===
      except Exception as e:
              print(f" Error processing job: {e}")
              import traceback
              traceback.print_exc()
asyncio.run(review_worker())
