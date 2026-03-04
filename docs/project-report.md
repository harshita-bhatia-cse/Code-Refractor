# Project Report

## Project
Code-Refractor (AI-Based)

## Current Objective
Provide a GitHub-connected workflow to:
- browse repositories/files,
- analyze code quality with rule-based metrics,
- produce LLM-assisted readable refactors.

## Completed
- GitHub OAuth login and JWT issuance.
- Protected API routes with bearer auth.
- Repo/file browsing from GitHub APIs.
- File-level analysis endpoint.
- Repo-level analysis endpoint with JSON artifact output.
- LLM refactor endpoint with fallback parsing/normalization.
- Frontend pages for login, dashboard, repos, files, and code viewer.

## Recent Hardening (March 4, 2026)
- Fixed broken login route token call.
- Standardized env loading from repository root `.env` with backend fallback.
- Tightened CORS to explicit origins (configurable via `CORS_ALLOW_ORIGINS`).
- Improved auth error handling for missing bearer tokens.
- Updated repository listing to authenticated `/user/repos` with pagination.
- Added API and architecture documentation.

## Known Gaps
- Secrets are in local `.env`; they must be rotated and never committed.
- `generate` route is still a stub.
- Several modules are placeholder/basic implementations (metrics fidelity can be improved).
- No test suite currently enforces regression checks.

## Next Engineering Priorities
1. Security baseline
   - rotate secrets, enforce secure defaults, tighten CORS for deployment domains only.
2. Reliability
   - add request/response validation tests for critical routes.
3. Product quality
   - improve metrics accuracy and add richer explanations per language.
4. Documentation and DX
   - setup runbook (`uvicorn`, frontend host, env setup, troubleshooting).
