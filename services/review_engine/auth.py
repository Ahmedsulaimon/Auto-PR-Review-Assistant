import os
import time
import jwt  # PyJWT
import httpx
import base64

def generate_jwt():
    """
    Generate a JWT for GitHub App authentication
    """
    app_id = os.getenv("GITHUB_APP_ID")
    private_key_env = os.getenv("GITHUB_APP_PRIVATE_KEY")
    
    if not app_id:
        raise RuntimeError("Missing GITHUB_APP_ID")
    
    # Handle different key formats
    private_key = None
    
    
    if private_key_env:
        # Direct key with \n replacements
        private_key = private_key_env.replace('\\n', '\n').strip()

    if not private_key:
        raise RuntimeError("Missing GITHUB_APP_PRIVATE_KEY")
    
    # Validate key format
    if not private_key.startswith('-----BEGIN') or not private_key.endswith('-----'):
        raise RuntimeError("Private key doesn't appear to be in PEM format")
    
    now = int(time.time())
    payload = {
        "iat": now - 60,          # issued at
        "exp": now + (10 * 60),   # max 10 minutes
        "iss": app_id
    }
    
    try:
        return jwt.encode(payload, private_key, algorithm="RS256")
    except Exception as e:
        raise RuntimeError(f"Failed to create JWT: {e}")

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
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )
        
        if resp.status_code != 201:
            raise RuntimeError(f"Failed to get installation token: {resp.status_code} {resp.text}")
        
        data = resp.json()
        return data["token"]