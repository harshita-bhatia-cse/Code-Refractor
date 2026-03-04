import re


class JSMetrics:
    FUNCTION_RE = re.compile(
        r"\bfunction\b\s*[A-Za-z_]\w*\s*\(|\b(?:const|let|var)\b\s+[A-Za-z_]\w*\s*=\s*\([^)]*\)\s*=>",
        re.MULTILINE,
    )

    def analyze(self, code: str):
        return {
            "lines": len(code.splitlines()),
            "functions": len(self.FUNCTION_RE.findall(code)),
            "classes": len(re.findall(r"\bclass\s+[A-Za-z_]\w*", code)),
            "conditionals": {
                "if": len(re.findall(r"\bif\s*\(", code)),
                "for": len(re.findall(r"\bfor\s*\(", code)),
                "while": len(re.findall(r"\bwhile\s*\(", code)),
                "switch": len(re.findall(r"\bswitch\s*\(", code)),
            },
        }
