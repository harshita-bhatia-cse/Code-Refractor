import re


class CPPMetrics:
    FUNCTION_RE = re.compile(
        r"^\s*(?!if\b|for\b|while\b|switch\b)(?:[A-Za-z_~]\w*::)?(?:[A-Za-z_]\w*[\s:\*&<>,]+)+[A-Za-z_~]\w*\s*\([^;{}]*\)\s*(?:const\s*)?\{",
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
