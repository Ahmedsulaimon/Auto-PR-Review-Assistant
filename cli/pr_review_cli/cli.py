import argparse
import asyncio
import httpx
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 1️⃣ Load env from infrastructure/.env if it exists
env_path = Path(__file__).resolve().parents[2] / "infrastructure" / ".env"
if env_path.exists():
    load_dotenv(env_path)

CONFIG_FILE = Path.home() / ".pr-review" / "config.json"

def load_config():
    """Load API_URL and installation_id from env or config file."""
    api_url = os.getenv("API_URL")
    installation_id = os.getenv("INSTALLATION_ID")

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            api_url = api_url or data.get("API_URL")
            installation_id = installation_id or data.get("installation_id")

    if not api_url:
        raise RuntimeError(f"API_URL not found in environment or {CONFIG_FILE}")

    return api_url, installation_id

def save_config(api_url=None, installation_id=None):
    """Update ~/.pr-review/config.json with new values."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

    if api_url:
        data["API_URL"] = api_url
    if installation_id:
        data["installation_id"] = installation_id

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Config updated at {CONFIG_FILE}")

# Load API_URL + installation_id
API_URL, INSTALLATION_ID = load_config()

# --- CLI commands ---
async def list_prs(limit: int):
    if not INSTALLATION_ID:
        print("⚠️ installation_id not set. Run `pr-review config --set-installation-id <id>` first.")
        return

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_URL}/api/prs", params={"installation_id": INSTALLATION_ID, "limit": limit})
        
        print(f"Response status: {resp.status_code}")
        print(f"Response type: {type(resp.json())}")
        
        prs = resp.json()

        if isinstance(prs, str):
            prs = json.loads(prs)
        
        if not prs:
            print("⚠️ No PRs found in history.")
            return
            
        print(f"📋 Last {len(prs)} PRs analyzed:")

        for pr in prs:
            # Handle if each PR is still a string
            if isinstance(pr, str):
                pr = json.loads(pr)
            
            print(f"- #{pr['pr_number']} | {pr['repo']} | status={pr.get('status','done')}")
async def show_pr(pr_number: int):
    if not INSTALLATION_ID:
        print("⚠️ installation_id not set. Run `pr-review config --set-installation-id <id>` first.")
        return

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_URL}/api/prs/{pr_number}", params={"installation_id": INSTALLATION_ID})
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
    if not INSTALLATION_ID:
        print("⚠️ installation_id not set. Run `pr-review config --set-installation-id <id>` first.")
        return

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_URL}/api/prs/{pr_number}/recheck")
        if resp.status_code == 404:
            print(f"❌ Could not find repo for PR #{pr_number}")
            return
        data = resp.json()
        print(f"♻️ Requeued PR #{pr_number} ({data['repo']}) for re-review.")

# --- Main CLI parser ---
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

    # config command
    config_parser = subparsers.add_parser("config")
    config_parser.add_argument("--set-installation-id", type=int, help="Set or update installation_id")

    args = parser.parse_args()

    if args.command == "list-prs":
        asyncio.run(list_prs(args.limit))
    elif args.command == "show-pr":
        asyncio.run(show_pr(args.pr_number))
    elif args.command == "recheck-pr":
        asyncio.run(recheck_pr(args.pr_number))
    elif args.command == "config":
        if args.set_installation_id:
            save_config(installation_id=args.set_installation_id)
        else:
            # Print current config
            api_url, installation_id = load_config()
            print("🔧 Current config:")
            print(f"   API_URL: {api_url}")
            print(f"   installation_id: {installation_id or '❌ not set'}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
