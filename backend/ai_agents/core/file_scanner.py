import os

class FileScanner:
    def scan(self, root):
        result = []

        for r, dirs, files in os.walk(root):

            # 🚫 Remove unwanted directories
            dirs[:] = [
                d for d in dirs
                if d not in ["__pycache__", "venv", ".git", "analysis_output"]
            ]

            for f in files:
                path = os.path.join(r, f)

                # 🚫 Skip unwanted files
                if (
                    f.endswith(".pyc")
                    or f.startswith(".")
                    or f.endswith(".json")
                    or f.endswith(".env")
                ):
                    continue

                # ✅ Only analyze real source code files
                if not f.endswith((".py", ".js", ".java", ".ts", ".cpp", ".c")):
                    continue

                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()

                        # 🚫 Skip empty files
                        if content.strip():
                            result.append((path, content))

                except Exception:
                    pass

        return result
