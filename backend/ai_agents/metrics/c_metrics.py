import re


class CMetrics:
    FUNCTION_RE = re.compile(
        r"^\s*(?!if\b|for\b|while\b|switch\b)(?:[A-Za-z_]\w*[\s\*]+)+[A-Za-z_]\w*\s*\([^;{}]*\)\s*\{",
        re.MULTILINE,
    )

    def analyze(self, code: str):
        return {
            "lines": len(code.splitlines()),
            "functions": len(self.FUNCTION_RE.findall(code)),
            "classes": 0,
            "conditionals": {
                "if": len(re.findall(r"\bif\s*\(", code)),
                "for": len(re.findall(r"\bfor\s*\(", code)),
                "while": len(re.findall(r"\bwhile\s*\(", code)),
                "switch": len(re.findall(r"\bswitch\s*\(", code)),
            },
        }
