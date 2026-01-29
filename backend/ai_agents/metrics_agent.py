import re

class MetricsAgent:
    """Compute simple code metrics."""

    def run(self, code: str) -> dict:
        return {
            "lines": len(code.splitlines()),
            "characters": len(code),
            "words": len(code.split()),
            "functions": len(re.findall(r"def\s+[A-Za-z0-9_]+\(", code))
        }
