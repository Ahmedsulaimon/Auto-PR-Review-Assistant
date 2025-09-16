import httpx
import os
from services.review_engine.auth import get_installation_token

async def post_pr_comments(owner, repo, pr_number, comments, github_token, installation_id=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"

    async def _do_post(token):
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client:
            # Get latest commit
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
            commits_resp = await client.get(commits_url, headers=headers)
            if commits_resp.status_code == 401:
                return None, 401
            commits_resp.raise_for_status()
            commit_id = commits_resp.json()[-1]["sha"]

            # Post comments
            for comment in comments:
                payload = {
                    "body": comment.get("body") or comment.get("comment") or "(no text)",
                    "commit_id": commit_id,
                    "path": comment.get("path") or comment.get("file"),
                    "side": "RIGHT",
                    "line": comment.get("line") or comment.get("line_number"),
                }
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 401:
                    return None, 401
                print(f"🔍 Comment POST status: {resp.status_code}")
            return True, 200

    # First attempt
    result, status = await _do_post(github_token)

    if status == 401 and installation_id:
        print("⚠️ GitHub token expired while posting comments, refreshing...")
        new_token = await get_installation_token(int(installation_id))
        result, status = await _do_post(new_token)
        if status != 200:
            raise RuntimeError(f"❌ Failed to post comments after retry (status {status})")

    return result
