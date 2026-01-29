import requests


class GitHubClient:
    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    # --------------------------------------------------
    # Get user repositories
    # --------------------------------------------------
    def get_repositories(self, username: str):
        url = f"https://api.github.com/users/{username}/repos"

        resp = requests.get(url, headers=self.headers)

        if resp.status_code != 200:
            raise Exception(f"GitHub API error: {resp.text}")

        repos = resp.json()

        return [
            {
                "name": repo["name"],
                "private": repo["private"],
                "url": repo["html_url"]
            }
            for repo in repos
        ]

    # --------------------------------------------------
    # Get repository contents (files & folders)
    # --------------------------------------------------
    def get_repo_contents(self, owner: str, repo: str, path: str = ""):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

        resp = requests.get(url, headers=self.headers)

        if resp.status_code != 200:
            raise Exception(f"GitHub API error: {resp.text}")

        return resp.json()

    # --------------------------------------------------
    # Get raw file content
    # --------------------------------------------------
    def get_file_content(self, raw_url: str):
        resp = requests.get(raw_url, headers=self.headers)

        if resp.status_code != 200:
            return {
                "error": True,
                "message": "Unable to fetch file content"
            }

        return {
            "content": resp.text
        }
