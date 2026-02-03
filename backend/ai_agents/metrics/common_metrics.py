import re

class CommonMetrics:
    def analyze(self, code: str):
        lines = code.splitlines()

        return {
            "lines": len(lines),
            "functions": len(re.findall(r"\bdef\b|\bfunction\b", code)),
            "classes": len(re.findall(r"\bclass\b", code)),
            "conditionals": {
                "if": len(re.findall(r"\bif\b", code)),
                "for": len(re.findall(r"\bfor\b", code)),
                "while": len(re.findall(r"\bwhile\b", code)),
                "switch": len(re.findall(r"\bswitch\b", code)),
            },
            "libraries": []
        }