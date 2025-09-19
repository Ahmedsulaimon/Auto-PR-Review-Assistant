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
    private_key_env = os.getenv("GITHUB_APP_PRIVATE_KEY", "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAv8DPGVJTC5kK0l4CWA/8uZ4Bc60WzCihhlgWpRC/QyLip3ip\n8eqFZD/o8YtjX/traiS29ywifPjz10pPzqFJT+5DxUPQI+7c7eMTDLePKKAKBioa\nYEVYOABwgWHN9/S3CEyYwuSk2a8yrYrbM3qDrb11xRj8ZJ2xQR8ELHgKo0gQm7IO\nwFeM4XX4E0IzJh9Hiqcau6ZaT+jhKTFdCtsz/Sue8cTg9TenWxejOuTji7MeJLwb\nE/SFhd8gT7CcDCYtku+EEVaKizonBWxoIAaG5i9uP0RbsLetpF92I4sjtlNrylsy\nYb940pmdi6/vzp7Jv3MWd5++4SVpCJ1jGC3RcQIDAQABAoIBAH+Bu3TQDE7K/qoy\nPwbF4rye98Iu19j8L6RA0RYEE9qVyPepwgAOfZLS+JgdowABFEUpksy7eVd2x9Zi\nIL16/F/9RO1YkYBDZn99Hn63VKej++ZresyHcAkVKbqvCaIXBNqs7Gu0VHY4DM/f\nZLFPh14xfK2KVtKlFWgDMuhLDm/R5id6Js4e789g5Mbl4ldOnPQy50JTIvDClbAC\n19ysrSl9GVBm/rgqeQsh5iru7vxs6FnxpohR51QN7ek1kwmIL34tBByPqLdQhKtB\nxJuqAlXpr9lcluJD3cvX47n7gMnSgPjYaFzAXWWvy6qJnnN8CeKQRwEo/l21pVUS\ncqrmcI0CgYEA3uICOjWlQZS4LcIxX9nqwtS5NcOyjpuyj6TiWSOVwmpSZwgNEOJ3\nP6BQP4UDAvNz27zzN72c4Y9itBeIO4Hrf+kb2H1MWRHQwbWGZ9jjWDFZ19JvFcmo\nlu5EBfOUXl8oVyp3hh+laa1x8Kf3ERvKy5/eqOHtTf/Aw2Aovl2Tw58CgYEA3D6x\nZaS6NpW2+yDQw4YY90qub8LsATVgCqULIy51tub2XMcWMKQxx5iYnCcQR5OW3xCC\nR+yzXYFy9ZRS9AcSBwdBiYhl65M3baSv0ogOu9PJTj8IpiZAT1MVnoZ5h71gBBGI\ndcQ1mPC8lstD8LV0+ma9vsQoV7viln91pkcX0O8CgYBk9i4aHijgvzR7Ded9yuHs\nJZ5MO3zL2r2VEhSyWktBiRYQs/XvOxbXjJAtZdxKXuuRk1L9YfgJuQD2IV7FzgFW\nrMq/U2rdQhO1W7wpmHbLgXd4K0vEq9ehnwbTR1ZjNWm5qnQAHp+4cigV4pApgNRp\nTt7203jCh2LTXeC28v63cwKBgQCN0JR7hWkd8qMC6uthqrvyp5TQg+thD9RKpmEY\ngzbq0ab6sHq6UU94XOqPSZvy6rav5TpuQ5xu7gZu2NXdKZxTCDoL69bsrDt5jxxj\nbJZIHSO3DWFtUp4ANdhq3d3tKGRl2kBKzE9SrlhQpIuXt8+d2H//EOGFNIa/L007\nBvXv4wKBgAd5H0G1In1zuDOXthAu6FPPof9IsWcZTyxQQHM86/u2/59i7IVQLNpl\n1DwPihAJ6jrJatSYoCaE0YsiPD5zMowYUKJ0Du3SY2EnjSlcFlP9zD1I32DVfphE\n8cQJ7Y3z0IWHJJMlrxD/PnKK7+l+dp6KaTfRTwRxUe2mFbr69cWJ\n-----END RSA PRIVATE KEY-----")
   
    
    if not app_id:
        raise RuntimeError("Missing GITHUB_APP_ID")
    
    # Handle different key formats
    private_key = None

    if private_key_env:
        # Direct key with \n replacements
        private_key = private_key_env.strip()

    else:
        raise RuntimeError("Missing GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_B64")
    
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