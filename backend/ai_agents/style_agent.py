import re

class StyleAgent:
    def run(self, code: str) -> dict:
        issues = []

        for i, line in enumerate(code.splitlines(), 1):
            if len(line) > 100:
                issues.append(f"Line {i}: exceeds 100 characters")

        functions = re.findall(r"def\s+([A-Za-z0-9_]+)\(", code)
        for fn in functions:
            if fn.lower() != fn:
                issues.append(f"Function '{fn}' should be snake_case")

        return {
            "style_issues": issues or ["No style issues found"]
        }
