import os, time, jwt

app_id = os.getenv("GITHUB_APP_ID")
private_key = os.getenv("GITHUB_APP_PRIVATE_KEY").strip()

now = int(time.time())
payload = {"iat": now - 60, "exp": now + 600, "iss": app_id}

token = jwt.encode(payload, private_key, algorithm="RS256")
print("JWT:", token[:80], "...")
