class JavaMetrics:
    def analyze(self, code):
        return {
            "lines": len(code.splitlines()),
            "functions": code.count("public "),
            "classes": code.count("class "),
            "conditionals": {
                "if": code.count("if "),
                "for": code.count("for "),
                "while": code.count("while "),
                "switch": code.count("switch ")
            }
        }
