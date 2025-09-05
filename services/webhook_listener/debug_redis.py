import os
import redis

# Use the same env var your app uses
redis_url = os.getenv("REDIS_URL_DOCKER", "redis://redis:6379")
print(f"Connecting to Redis at {redis_url}")

r = redis.from_url(redis_url)

# Check which DB index we're connected to
connection_info = r.connection_pool.connection_kwargs
print(f"DB index: {connection_info.get('db', 0)}")

# List all keys
keys = r.keys("*")
print(f"Keys in Redis: {keys}")

# Check queue contents
queue = r.lrange("pr-review-queue", 0, -1)
print(f"Queue contents ({len(queue)} items):")
for i, item in enumerate(queue, 1):
    print(f"{i}: {item}")
