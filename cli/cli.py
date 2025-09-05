# cli.py
import argparse
import asyncio
import json
import os
import redis.asyncio as aioredis


REDIS_URL = os.getenv("REDIS_URL_HOST", "redis://localhost:6379")

QUEUE_NAME = "pr-review-queue"
HISTORY_KEY = "pr-review-history"  # store processed PRs here


async def list_prs(limit: int):
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    prs = await redis.lrange(HISTORY_KEY, -limit, -1)  # latest N
    if not prs:
        print("⚠️ No PRs found in history.")
        return
    print(f"📋 Last {len(prs)} PRs analyzed:")
    for entry in prs:
        pr = json.loads(entry)
        print(f"- #{pr['pr_number']} | {pr['repo']} | status={pr.get('status','done')}")
    await redis.close()


async def show_pr(pr_number: int):
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    prs = await redis.lrange(HISTORY_KEY, 0, -1)
    for entry in prs:
        pr = json.loads(entry)
        if pr["pr_number"] == pr_number:
            print(f"🔍 PR #{pr['pr_number']} in {pr['repo']}")
            print(f"Title: {pr.get('title','N/A')}")
            print(f"Status: {pr.get('status','done')}")
            comments = pr.get("comments", [])
            print(f"💬 {len(comments)} comments")
            for c in comments:
                print(f" - {c.get('path')}:{c.get('line')} → {c.get('body')}")
            break
    else:
        print(f"❌ No record for PR #{pr_number}")
    await redis.close()


async def recheck_pr(pr_number: int):
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)

    # Look up repo from history
    prs = await redis.lrange(HISTORY_KEY, 0, -1)
    repo = None
    for entry in prs:
        pr = json.loads(entry)
        if pr["pr_number"] == pr_number:
            repo = pr["repo"]
            break

    if not repo:
        print(f"❌ Could not find repo for PR #{pr_number} in history.")
        await redis.close()
        return

    job = {"repo": repo, "pr_number": pr_number, "action": "reopened"}
    await redis.lpush(QUEUE_NAME, json.dumps(job))
    print(f"♻️ Requeued PR #{pr_number} ({repo}) for re-review.")
    await redis.close()



def main():
    parser = argparse.ArgumentParser(description="PR Review Assistant CLI Dashboard")
    subparsers = parser.add_subparsers(dest="command")

    # list-prs
    list_parser = subparsers.add_parser("list-prs")
    list_parser.add_argument("--limit", type=int, default=10)

    # show-pr
    show_parser = subparsers.add_parser("show-pr")
    show_parser.add_argument("pr_number", type=int)

    # recheck-pr
    recheck_parser = subparsers.add_parser("recheck-pr")
    recheck_parser.add_argument("pr_number", type=int)

    args = parser.parse_args()

    if args.command == "list-prs":
        asyncio.run(list_prs(args.limit))
    elif args.command == "show-pr":
        asyncio.run(show_pr(args.pr_number))
    elif args.command == "recheck-pr":
        asyncio.run(recheck_pr(args.pr_number))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
#python cli/cli.py list-prs --limit 5
#python cli/cli.py show-pr 1
#python cli/cli.py recheck-pr 1