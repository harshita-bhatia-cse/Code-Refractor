class RefactorAgent:
    def run(self, code: str) -> dict:
        suggestions = []

        if "print(" in code:
            suggestions.append("Avoid print statements in production code.")

        if "import *" in code:
            suggestions.append("Avoid wildcard imports.")

        if len(code.splitlines()) > 300:
            suggestions.append("File is too long. Consider splitting into modules.")

        return {
            "suggestions": suggestions or ["No major refactoring needed"]
        }
