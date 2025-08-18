import httpx

async def post_pr_comments(owner, repo, pr_number, comments, github_token):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"

    # 🔑 Fetch latest commit SHA for PR
    commits_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
    headers = {"Authorization": f"token {github_token}"}
    async with httpx.AsyncClient() as client:
        commits_resp = await client.get(commits_url, headers=headers)
        commits_resp.raise_for_status()
        commit_id = commits_resp.json()[-1]["sha"]  # last commit in PR

        for comment in comments:
            payload = {
                "body": comment["comment"],
                "commit_id": commit_id,
                "path": comment["file"],
                "side": "RIGHT",
                "line": comment["line_number"]
            }
            print(f"📤 Posting comment payload: {payload}")
            resp = await client.post(url, headers=headers, json=payload)
            print(f"🔍 Status: {resp.status_code}")
            print(f"🔍 Response: {resp.text}")
