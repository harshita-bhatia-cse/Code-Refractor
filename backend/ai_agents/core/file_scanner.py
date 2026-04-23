import os


class FileScanner:
    SOURCE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".cs",
        ".go",
        ".php",
        ".rs",
    }

    IGNORED_DIRS = {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".pytest_cache",
        "analysis_output",
    }

    IGNORED_EXTENSIONS = {
        ".pyc",
        ".pyo",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".pdf",
        ".zip",
        ".gz",
        ".tar",
        ".exe",
        ".dll",
        ".so",
        ".class",
        ".jar",
        ".env",
    }

    def scan(self, root):
        result = []

        for current_root, dirs, files in os.walk(root):
            dirs[:] = [dirname for dirname in dirs if dirname not in self.IGNORED_DIRS]

            for filename in files:
                path = os.path.join(current_root, filename)
                _, ext = os.path.splitext(filename.lower())

                if filename.startswith(".") or ext in self.IGNORED_EXTENSIONS:
                    continue

                if ext not in self.SOURCE_EXTENSIONS:
                    continue

                try:
                    if os.path.getsize(path) > 1_000_000:
                        continue

                    with open(path, "r", encoding="utf-8", errors="ignore") as file_handle:
                        content = file_handle.read()
                        if content.strip():
                            result.append((path, content))
                except Exception:
                    pass

        return result
