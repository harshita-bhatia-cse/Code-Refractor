class StyleAgent:
    def run(self, code: str, filename: str | None = None) -> dict:
        issues = []

        # Detect language from filename
        language = "unknown"
        if filename:
            if filename.endswith(".java"):
                language = "java"
            elif filename.endswith(".py"):
                language = "python"
            elif filename.endswith(".js"):
                language = "javascript"

        # Basic style checks (language-agnostic)
        for i, line in enumerate(code.splitlines(), 1):
            if len(line) > 100:
                issues.append(f"Line {i}: exceeds 100 characters")

        return {
            "language": language,
            "style_issues": issues or ["No style issues found"]
        }
