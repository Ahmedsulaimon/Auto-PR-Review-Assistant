import os


def debug_private_key():
    """Debug function to check private key format"""
    private_key_env = os.getenv("GITHUB_APP_PRIVATE_KEY", "")
    if private_key_env:
        key = private_key_env.replace('\\n', '\n').strip()
        print(f"Key starts with: {key[:50]}...")
        print(f"Key ends with: ...{key[-50:]}")
        print(f"Key length: {len(key)}")
        print(f"Has proper BEGIN: {key.startswith('-----BEGIN')}")
        print(f"Has proper END: {key.endswith('-----')}")
    else:
        print("GITHUB_APP_PRIVATE_KEY is not set")
print('Debugging private key:')
debug_private_key()