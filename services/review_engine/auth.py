import os
import time
import jwt  # PyJWT
import httpx

def generate_jwt():
    """
    Generate a JWT for GitHub App authentication
    """
    app_id = os.getenv("GITHUB_APP_ID")
    private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")

    if not app_id or not private_key:
        raise RuntimeError("Missing GITHUB_APP_ID or GITHUB_APP_PRIVATE_KEY")

    # Convert PEM string into usable RSA key
    private_key = private_key.replace("\\n", "\n")  # Handle Render-style envs

    now = int(time.time())
    payload = {
        "iat": now - 60,          # issued at
        "exp": now + (10 * 60),   # max 10 minutes
        "iss": app_id
    }

    return jwt.encode(payload, private_key, algorithm="RS256")

async def get_installation_token(installation_id: int) -> str:
    """
    Exchange the App JWT for an installation token
    """
    jwt_token = generate_jwt()

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json"
            }
        )

        if resp.status_code != 201:
            raise RuntimeError(f"Failed to get installation token: {resp.status_code} {resp.text}")

        data = resp.json()
        return data["token"]
