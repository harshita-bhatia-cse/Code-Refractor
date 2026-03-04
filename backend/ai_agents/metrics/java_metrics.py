import re


class JavaMetrics:
    METHOD_RE = re.compile(
        r"^\s*(?:public|private|protected)?\s*"
        r"(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
        r"[\w<>\[\], ?]+\s+[A-Za-z_]\w*\s*\([^;{}]*\)\s*\{",
        re.MULTILINE,
    )

    def analyze(self, code: str):
        return {
            "lines": len(code.splitlines()),
            "functions": len(self.METHOD_RE.findall(code)),
            "classes": len(re.findall(r"\bclass\s+[A-Za-z_]\w*", code)),
            "conditionals": {
                "if": len(re.findall(r"\bif\s*\(", code)),
                "for": len(re.findall(r"\bfor\s*\(", code)),
                "while": len(re.findall(r"\bwhile\s*\(", code)),
                "switch": len(re.findall(r"\bswitch\s*\(", code)),
            },
        }
