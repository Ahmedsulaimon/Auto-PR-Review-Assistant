import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch

import services.review_engine.engine as engine


@pytest.mark.asyncio
async def test_review_worker_processes_job(monkeypatch):
    """Test that review_worker consumes a job and processes it end-to-end."""

    # --- Fake Redis ---
    fake_redis = AsyncMock()
    fake_redis.brpop.return_value = (
        "pr-review-queue",
        json.dumps({
            "repo": "user/repo",
            "pr_number": 1,
            "action": "opened"
        }),
    )
    fake_redis.rpush.return_value = 1
    fake_redis.ltrim.return_value = 1

    # --- Fake GraphQL ---
    fake_graphql_client = AsyncMock()
    fake_graphql_client.execute_async.return_value = {
        "repository": {
            "pullRequest": {
                "id": "PR_id",
                "title": "Test PR",
                "url": "http://example.com/pr/1"
            }
        }
    }

    # --- Fake REST (files) ---
    fake_files = [
        {"filename": "test.py", "patch": "@@ -1,2 +1,2 @@\n-print('hello')\n+print('hi')"}
    ]
    async def fake_get(*args, **kwargs):
        class FakeResponse:
            def json(self_inner): return fake_files
        return FakeResponse()

    # --- Fake LLM review ---
    async def fake_generate_review(pr_title, chunks):
        return json.dumps([{"file": "test.py", "comment": "Looks good", "line_number": 1}])

    def fake_parse_review_json(output):
        return [{"body": "Looks good", "path": "test.py", "line": 1}]

    async def fake_post_pr_comments(owner, repo, pr_number, comments, token):
        return True

    # --- Monkeypatch dependencies ---
    monkeypatch.setenv("REDIS_URL_DOCKER", "redis://fake")
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")

    monkeypatch.setattr(engine, "from_url", AsyncMock(return_value=fake_redis))
    monkeypatch.setattr(engine, "Client", lambda *a, **kw: fake_graphql_client)
    monkeypatch.setattr(engine.httpx, "AsyncClient", lambda *a, **kw: AsyncMock(get=fake_get))
    monkeypatch.setattr(engine, "generate_review", fake_generate_review)
    monkeypatch.setattr(engine, "parse_review_json", fake_parse_review_json)
    monkeypatch.setattr(engine, "post_pr_comments", fake_post_pr_comments)

    # --- Run only ONE iteration of worker ---
    async def one_iteration_worker():
        task = asyncio.create_task(engine.review_worker())
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await one_iteration_worker()

    # --- Assertions ---
    fake_redis.brpop.assert_called_with("pr-review-queue")
    fake_graphql_client.execute_async.assert_called_once()
