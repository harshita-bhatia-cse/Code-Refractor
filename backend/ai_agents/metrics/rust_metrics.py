class RustMetrics:
    def analyze(self, code):
        return {
            "lines": len(code.splitlines()),
            "functions": code.count("("),
            "classes": 0,
            "conditionals": {
                "if": code.count("if "),
                "for": code.count("for "),
                "while": code.count("while "),
                "switch": code.count("switch ")
            }
        }
