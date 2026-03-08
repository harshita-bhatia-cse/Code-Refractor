import requests

from backend.utils.url_validation import validate_github_raw_url


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
    def get_repositories(self):
        # Use authenticated endpoint so private repositories are included.
        url = "https://api.github.com/user/repos"
        params = {
            "visibility": "all",
            "affiliation": "owner,collaborator,organization_member",
            "per_page": 100,
            "sort": "updated",
        }

        repos = []
        page = 1
        while True:
            page_params = dict(params)
            page_params["page"] = page

            resp = requests.get(url, headers=self.headers, params=page_params)
            if resp.status_code != 200:
                raise Exception(f"GitHub API error: {resp.text}")

            chunk = resp.json()
            if not chunk:
                break

            repos.extend(chunk)
            if len(chunk) < params["per_page"]:
                break
            page += 1

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
        safe_url = validate_github_raw_url(raw_url)
        resp = requests.get(safe_url, headers=self.headers, allow_redirects=False)

        if resp.status_code != 200:
            return {
                "error": True,
                "message": "Unable to fetch file content"
            }

        return {
            "content": resp.text
        }
        # --------------------------------------------------
    # Download full repository as ZIP
    # --------------------------------------------------
    def download_repo(self, owner: str, repo: str, save_path: str):

        import os
        import zipfile

        url = f"https://api.github.com/repos/{owner}/{repo}/zipball"

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to download repo: {response.text}")

        zip_path = os.path.join(save_path, "repo.zip")

        # Save zip file
        with open(zip_path, "wb") as f:
            f.write(response.content)

        # Extract zip
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(save_path)


