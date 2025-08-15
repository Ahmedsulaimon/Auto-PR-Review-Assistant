import httpx

async def post_pr_comments(owner, repo, pr_number, comments, gh_token):
    async with httpx.AsyncClient() as client:
        for comment in comments:
            await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments",
                headers={"Authorization": f"Bearer {gh_token}"},
                json={
                    "path": comment["file"],
                    "body": comment["comment"],
                    "line": comment["line_number"],
                    "side": "RIGHT"
                }
            )
