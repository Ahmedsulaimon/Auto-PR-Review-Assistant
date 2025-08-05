# Auto‑PR Review Assistant

## Overview

The Auto‑PR Review Assistant is a developer tool designed to automate the pull‑request review process. Leveraging AI-powered language models, it analyzes opened or updated GitHub pull requests, provides inline suggestions, highlights potential issues (e.g., style violations, missing tests, security concerns), and streamlines collaboration by offering consistent, contextual feedback.

This repository contains the core components required to run the assistant, including event handling, language model integration, and optional web dashboard.

## MVP Features

The Minimum Viable Product will include the following capabilities:

1. **GitHub Webhook Integration**  
   - Receive pull request events (opened, synchronized) via GitHub Webhooks.  
   - Authenticate and validate webhook signatures.

2. **AI‑Powered Review Engine**  
   - Process changed files in a pull request and generate review comments using a language model (e.g., OpenAI GPT).  
   - Support for basic code quality checks: syntax, linting reminders, docstrings.

3. **Inline Comment Posting**  
   - Post review comments directly on the PR diffs via GitHub API.  
   - Group comments by file and section.

4. **Configuration & Thresholds**  
   - Allow repository owners to configure which checks are enabled (e.g., style, complexity, security).  
   - Threshold for comment verbosity (e.g., summary‑only vs. detailed feedback).

5. **Basic Dashboard (CLI Stub)**  
   - Local CLI to list recent analyzed PRs and their review statuses.  

## Tech Stack

| Layer            | Technology                 | Purpose                                                                    |
|------------------|----------------------------|----------------------------------------------------------------------------|
| **Backend API**  | Python 3.11, FastAPI       | Webhook listener, review orchestration                                     |
| **AI Engine**    | OpenAI GPT API             | Generate review feedback                                                   |
| **GitHub Client**| GitHub GraphQL API         | Webhook validation, posting comments                                       |
| **Persistence**  | Redis                      | Fast, in-memory storage for caching PR metadata, config, and job queues    |
| **CLI Dashboard**| Typer (Python CLI toolkit) | Local interface to query PR statuses                                       |
| **Deployment**   | Docker, GitHub Actions     | Containerization & CI/CD                                                   |
| **Configuration**| YAML files                 | Define checks, thresholds, API keys                                        |



## Design Rationale


### Why Redis Instead SQLite or JSON files?

While SQLite or JSON files could offer a lightweight option for early development, Redis was chosen for its performance and flexibility. It enables:

- Fast, in-memory data access for real-time processing.  
- Support for queues and pub/sub mechanisms (useful for job orchestration).  
- Better scalability for concurrent webhook events across repositories.  
- Simpler migration path to distributed deployments.

### Why FastAPI Instead of Flask?

| Feature            | FastAPI                               | Flask                                |
|--------------------|---------------------------------------|--------------------------------------|
| Async Support      |  Native `async`/`await`               |  Requires setup                      |
| Performance        |  Starlette + Pydantic stack           | Moderate                             |
| Type Safety        |  Strong with Pydantic                 | Manual                               |
| Auto Docs          |  Swagger & ReDoc built-in             | Needs extension                      |
| Design Philosophy  |  Async-first, modern Pythonic         | Legacy-compatible                    |

**Conclusion:** FastAPI is ideal for webhook-heavy, async-capable APIs like this one. Flask remains an option for simpler or familiar workflows, but FastAPI provides a more robust and scalable backbone for our use case.

### Why GitHub GraphQL API over REST API?

### Efficiency & Flexibility

- With GraphQL you can fetch exactly the fields you need in one round‑trip (e.g., pull‑request title, diff, author, files changed, review comments) rather than juggling multiple REST endpoints.  
- If tomorrow you need additional metadata (say a check‑run status, CI details, or labels) you can add it to your query without changing URLs or client logic.

### Performance & Rate‑Limit Benefits

- GitHub’s GraphQL API gives you a higher rate‑limit quota (measured in points) compared to REST, and batching multiple REST calls into one GraphQL query usually consumes fewer points.  
- Fewer network hops means lower latency and less complexity in orchestrating parallel calls.

### Strong Typing & Discoverability

- The GraphQL schema is strongly typed: your IDE can autocomplete available fields, and you get immediate feedback when a field doesn’t exist.  
- This makes it easier to evolve your data models and client code in lock‑step.

### Uniform Tooling with Octokit

- Octokit (the official GitHub SDK) offers built‑in GraphQL client support in multiple languages, so you can still leverage its authentication helpers, pagination utilities, and error handling—just pointing it at a GraphQL endpoint instead of REST.

### Why CLI Dashboard First Instead of React + Tailwind?

| Factor                     | CLI (Typer)                    | React + Tailwind Frontend              |
|----------------------------|--------------------------------|----------------------------------------|
| Development Speed          |  Faster for MVP                |  Slower setup                          |
| Dev Tool Focus             |  Terminal-friendly             |  Web-friendly                          |
| Infrastructure Simplicity  |  Single container              |  Multi-part stack (frontend/backend)   |
| Extensibility              |  Hooks ready for expansion     |  Future upgrade possible               |

**Conclusion:** Starting with a CLI dashboard enables rapid prototyping and fast feedback. A full web UI is a future milestone once data pipelines and review analysis are stable.

## Project Structure

```text
auto‑pr-review-assistant/
├── README.md
├── CONTRIBUTING.md
├── docs/
│   ├── architecture.md
│   └── api-spec.md
├── services/
│   ├── webhook-listener/
│   │   ├── README.md
|   |   |── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   └── review-engine/
│       ├── README.md
|       |── Dockerfile
│       ├── engine.py
│       └── requirements.txt
├── cli/
│   ├── README.md
│   └── cli.py
├── infrastructure/
|   |── .env    
│   ├── docker-compose.yml
│   └── github-actions.yml
├── config/
│   └── default-config.yaml
└── tests/
|    ├── service_tests/
|    └── cli_tests/
|──.gitignore

```

## Getting Started
### Prerequisites
- Python 3.11
- Redis
- GitHub GraphQL API access token

### Installation
```bash
git clone <repo-url>
cd auto-pr-review-assistant
pip install -r services/webhook-listener/requirements.txt \
            -r services/review-engine/requirements.txt
```
### Usage
- Start Redis: redis-server
- Run webhook listener: uvicorn services/webhook-listener.main:app --reload
- Use CLI: python cli/cli.py list-prs           


---

_This document outlines the high‑level plan and is subject to refinement as the project evolves._
