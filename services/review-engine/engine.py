import asyncio, json
import re

from aioredis import from_url
from dotenv import load_dotenv
load_dotenv()
import os
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

async def review_worker():
    redis = await from_url(os.getenv("REDIS_URL"))
    # configure your GraphQL client
    transport = AIOHTTPTransport(url="https://api.github.com/graphql", headers={
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
    })
    client = Client(transport=transport, fetch_schema_from_transport=True)

    while True:
        _, payload = await redis.brpop("pr-review-queue")
        job = json.loads(payload)
        repo = job["repo"]
        pr_number = job["pr_number"]

        # 1) Fetch PR diff via GraphQL
        query = gql(
            """
            query($owner: String!, $name: String!, $number: Int!) {
              repository(owner: $owner, name: $name) {
                pullRequest(number: $number) {
                  id
                  title
                  files(first: 50) {
                    nodes {
                      path
                      additions
                      deletions
                      patch
                    }
                  }
                }
              }
            }
            """
        )
        owner, name = repo.split("/")
        variables = {"owner": owner, "name": name, "number": pr_number}
        result = await client.execute_async(query, variable_values=variables)

        # 2) Parse `patch` fields into text chunks
        files = result["repository"]["pullRequest"]["files"]["nodes"]
        chunks = []
        for f in files:
            patch = f.get("patch")
            if not patch:
                continue
            # split by hunk header (e.g. "@@ -1,3 +1,9 @@")
            parts = re.split(r"(^@@.*@@\n)", patch, flags=re.MULTILINE)
            # recombine header+body
            for i in range(1, len(parts), 2):
                header = parts[i]
                body = parts[i+1]
                chunks.append({"path": f["path"], "hunk": header + body})

        # now you have `chunks` ready to feed into your LLM
        print(f"Prepared {len(chunks)} hunks for PR #{pr_number}")

        # TODO: call OpenAI and post comments…

asyncio.run(review_worker())
