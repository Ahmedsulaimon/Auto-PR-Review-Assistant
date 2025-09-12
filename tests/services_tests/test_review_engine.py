# import pytest
# import asyncio
# from unittest.mock import AsyncMock, patch


# @pytest.fixture(autouse=True)
# def test_set_env_vars(monkeypatch):
#     """Provide fake environment variables for tests."""
#     monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
#     monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
#     monkeypatch.setenv("REDIS_URL_DOCKER", "redis://fake-url")
    
# import services.review_engine.engine as engine

# @pytest.mark.asyncio
# async def test_review_worker_processes_job(monkeypatch):
#     """Smoke test: review_worker should process one fake PR job."""

#     # --- Fake Redis ---
#     fake_redis = AsyncMock()
#     fake_redis.brpop = AsyncMock(
#         return_value=(
#             "pr-review-queue",
#             '{"repo": "user/repo", "pr_number": 42, "action": "opened"}',
#         )
#     )
#     fake_redis.rpush = AsyncMock()
#     fake_redis.ltrim = AsyncMock()
#     fake_redis.ping = AsyncMock(return_value=True)

#     monkeypatch.setattr(engine, "from_url", AsyncMock(return_value=fake_redis))

#     # --- Fake GraphQL ---
#     fake_graphql_client = AsyncMock()
#     fake_graphql_client.execute_async = AsyncMock(
#         return_value={
#             "repository": {
#                 "pullRequest": {
#                     "title": "Add new feature",
#                     "url": "https://github.com/user/repo/pull/42",
#                 }
#             }
#         }
#     )
#     monkeypatch.setattr(engine, "Client", lambda *a, **kw: fake_graphql_client)

#     # --- Fake OpenAI (generate_review) ---
#     monkeypatch.setattr(
#         engine, "generate_review", AsyncMock(return_value='[{"file": "test.py", "comment": "Looks good", "line_number": 1}]')
#     )
#     monkeypatch.setattr(
#         engine, "parse_review_json",
#         lambda x: [{"body": "Looks good", "path": "test.py", "line": 1}]
#     )

#     # --- Fake post_pr_comments ---
#     monkeypatch.setattr(engine, "post_pr_comments", AsyncMock())

#     # --- Fake HTTPX ---
#     fake_httpx_client = AsyncMock()
#     fake_httpx_client.__aenter__.return_value.get = AsyncMock(
#         return_value=AsyncMock(json=lambda: [{"filename": "test.py", "patch": "@@ -1 +1 @@\n+print('hi')"}])
#     )
#     monkeypatch.setattr(engine.httpx, "AsyncClient", lambda *a, **kw: fake_httpx_client)

#     # --- Run worker (just once) ---
#     async def run_once():
#         task = asyncio.create_task(engine.review_worker())
#         await asyncio.sleep(0.1)  # allow first loop iteration
#         task.cancel()
#         try:
#             await task
#         except asyncio.CancelledError:
#             pass

#     await run_once()

#     # Assertions
#     fake_redis.brpop.assert_awaited()
#     engine.post_pr_comments.assert_awaited_once()
