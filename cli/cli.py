import argparse
import asyncio
import httpx
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

async def list_prs(limit: int):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_URL}/prs", params={"limit": limit})
        prs = resp.json()
        if not prs:
            print("⚠️ No PRs found in history.")
            return
        print(f"📋 Last {len(prs)} PRs analyzed:")
        for pr in prs:
            print(f"- #{pr['pr_number']} | {pr['repo']} | status={pr.get('status','done')}")

async def show_pr(pr_number: int):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_URL}/prs/{pr_number}")
        if resp.status_code == 404:
            print(f"❌ No record for PR #{pr_number}")
            return
        pr = resp.json()
        print(f"🔍 PR #{pr['pr_number']} in {pr['repo']}")
        print(f"Title: {pr.get('title','N/A')}")
        print(f"Status: {pr.get('status','done')}")
        comments = pr.get("comments", [])
        print(f"💬 {len(comments)} comments")
        for c in comments:
            print(f" - {c.get('path')}:{c.get('line')} → {c.get('body')}")

async def recheck_pr(pr_number: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_URL}/prs/{pr_number}/recheck")
        if resp.status_code == 404:
            print(f"❌ Could not find repo for PR #{pr_number}")
            return
        data = resp.json()
        print(f"♻️ Requeued PR #{pr_number} ({data['repo']}) for re-review.")

def main():
    parser = argparse.ArgumentParser(description="PR Review Assistant CLI Dashboard")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list-prs")
    list_parser.add_argument("--limit", type=int, default=10)

    show_parser = subparsers.add_parser("show-pr")
    show_parser.add_argument("pr_number", type=int)

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
