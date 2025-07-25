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

| Layer            | Technology                | Purpose                                                                    |
|------------------|----------------------------|----------------------------------------------------------------------------|
| **Backend API**  | Python 3.11, FastAPI       | Webhook listener, review orchestration                                     |
| **AI Engine**    | OpenAI GPT API             | Generate review feedback                                                   |
| **GitHub Client**| PyGitHub or Octokit.py     | Webhook validation, posting comments                                       |
| **Persistence**  | Redis                      | Fast, in-memory storage for caching PR metadata, config, and job queues    |
| **CLI Dashboard**| Typer (Python CLI toolkit) | Local interface to query PR statuses                                       |
| **Deployment**   | Docker, GitHub Actions     | Containerization & CI/CD                                                   |
| **Configuration**| YAML files                 | Define checks, thresholds, API keys                                        |



## Design Rationale


### Why Redis SQLite or JSON files?

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

### Why CLI Dashboard First Instead of React + Tailwind?

| Factor                     | CLI (Typer)                    | React + Tailwind Frontend              |
|----------------------------|--------------------------------|----------------------------------------|
| Development Speed          |  Faster for MVP                |  Slower setup                          |
| Dev Tool Focus             |  Terminal-friendly             |  Web-friendly                          |
| Infrastructure Simplicity  |  Single container              |  Multi-part stack (frontend/backend)   |
| Extensibility              |  Hooks ready for expansion     |  Future upgrade possible               |

**Conclusion:** Starting with a CLI dashboard enables rapid prototyping and fast feedback. A full web UI is a future milestone once data pipelines and review analysis are stable.

## Roadmap & Next Steps

1. Implement webhook receiver and basic request validation.  
2. Wire up OpenAI API and develop prompt templates.  
3. Post inline comments for small test repos.  
4. Introduce configuration file parsing.  
5. Expand checks (security scanning, test coverage hints).  
6. Build a web dashboard for organization‑wide overview.

---

_This document outlines the high‑level plan and is subject to refinement as the project evolves._
