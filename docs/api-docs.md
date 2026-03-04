# API Docs

Base URL (local): `http://127.0.0.1:8000`

Auth model:
- Most routes require `Authorization: Bearer <jwt_token>`.
- JWT is issued after GitHub OAuth callback.

## Auth

### `GET /auth/github/login`
Redirects user to GitHub OAuth authorize URL.

### `GET /auth/github/callback?code=...`
Exchanges OAuth code for GitHub token, creates JWT, and redirects to frontend dashboard with query params.

## User/Profile

### `GET /profile/`
Returns JWT payload and status.

## Repositories and Files

### `GET /repos/`
Returns authenticated user repositories (including private/collaborator/org repos).

### `GET /files/{repo_name}?path=optional/sub/path`
Returns directory entries:
- `name`
- `path`
- `type` (`file` or `dir`)
- `raw_url` (for files)

### `GET /code/?raw_url=...`
Fetches raw file content and returns:
- `raw_url`
- `code`

## Analysis

### `GET /analyze/?raw_url=...`
Runs file-level static analysis and returns language-aware metrics.

### `POST /analyze-repo/?repo_path=...`
Runs repo-level metrics, writes output file, and returns summary metadata.

## Refactor

### `POST /refactor/`
Body:
```json
{
  "raw_url": "https://raw.githubusercontent.com/.../file.py"
}
```
Or provide inline code:
```json
{
  "code": "print('hello')",
  "filename": "sample.py"
}
```
Returns:
- `analysis` (static metrics)
- `llm_refactor` (`summary`, `issues`, `refactored_code`, `ok`, `error`)

## Generate (stub)

### `POST /generate/`
Currently returns `501 Not Implemented`.
