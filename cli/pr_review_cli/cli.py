import argparse
import asyncio
import httpx
import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".pr_review" / "config.json"
DEFAULT_API_URL = "https://auto-pr-review-assistant.onrender.com"

def load_config():
    """Load API_URL and installation_id strictly from config.json."""
    if not CONFIG_FILE.exists():
        raise RuntimeError(f"❌ Config file not found at {CONFIG_FILE}. Run `pr-review config` first.")

    with open(CONFIG_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"❌ Config file at {CONFIG_FILE} is invalid JSON.")

    api_url = data.get("API_URL")
    installation_id = data.get("installation_id")

    if not api_url:
        raise RuntimeError("❌ API_URL missing from config file.")

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
    
    # Always ensure API_URL is set to default if not present
    if "API_URL" not in data:
        data["API_URL"] = DEFAULT_API_URL

    if api_url is not None:
        data["API_URL"] = api_url
    if installation_id is not None:
        data["installation_id"] = installation_id

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Config updated at {CONFIG_FILE}")

# --- Helpers ---
def ensure_installation_id(api_url, installation_id):
    """Ensure installation_id exists, prompt user if missing."""
    if not installation_id:
        print("⚠️ installation_id not set in config.")
        try:
            new_id = int(input("👉 Please enter your GitHub App installation_id: ").strip())
            save_config(api_url=api_url, installation_id=new_id)
            return new_id
        except ValueError:
            raise RuntimeError("❌ Invalid installation_id. Must be an integer.")
    return installation_id

# --- CLI commands ---
async def list_prs(limit: int):
    api_url, installation_id = load_config()
    installation_id = ensure_installation_id(api_url, installation_id)

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{api_url}/api/prs", params={"installation_id": installation_id, "limit": limit})
        prs = resp.json()

        if isinstance(prs, str):
            prs = json.loads(prs)

        if not prs:
            print("⚠️ No PRs found in history.")
            return
            
        print(f"📋 Last {len(prs)} PRs analyzed:")
        for pr in prs:
            if isinstance(pr, str):
                pr = json.loads(pr)
            print(f"- #{pr['pr_number']} | {pr['repo']} | status={pr.get('status','done')}")

async def show_pr(pr_number: int):
    api_url, installation_id = load_config()
    installation_id = ensure_installation_id(api_url, installation_id)

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{api_url}/api/prs/{pr_number}", params={"installation_id": installation_id})
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
    api_url, installation_id = load_config()
    installation_id = ensure_installation_id(api_url, installation_id)

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{api_url}/api/prs/{pr_number}/recheck", params={"installation_id": installation_id})
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
    config_parser = subparsers.add_parser("config", help="View or update configuration")
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
            try:
                api_url, installation_id = load_config()
                print("🔧 Current config:")
                print(f"   API_URL: {api_url}")
                print(f"   installation_id: {installation_id or '❌ not set'}")
            except RuntimeError:
                # Config doesn't exist yet, initialize it
                print("⚠️ Config file not found. Creating new config...")
                save_config()  # This will create config with default API_URL
                print(f"✅ Config initialized with API_URL: {DEFAULT_API_URL}")
                print("\n👉 Now set your installation_id:")
                print("   pr-review config --set-installation-id <your-id>")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()