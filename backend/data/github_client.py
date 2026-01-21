import requests

class GitHubClient:
    def __init__(self, token: str):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

    def list_repos(self):
        """Fetch user repositories"""
        url = f"{self.base_url}/user/repos"
        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            raise Exception(f"GitHub API error: {res.text}")

        return res.json()

    def get_repo_contents(self, owner: str, repo: str, path: str = ""):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        res = requests.get(url, headers=self.headers)
        return res.json()

    def get_file_content(self, raw_url: str):
        res = requests.get(raw_url, headers=self.headers)

        if res.status_code != 200:
            return {"error": True, "message": "Unable to fetch file"}

        return {
            "error": False,
            "content": res.text
        }
