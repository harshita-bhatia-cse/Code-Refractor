class JSMetrics:
    def analyze(self, code):
        return {
            "lines": len(code.splitlines()),
            "functions": code.count("function ") + code.count("=>"),
            "classes": code.count("class "),
            "conditionals": {
                "if": code.count("if "),
                "for": code.count("for "),
                "while": code.count("while "),
                "switch": code.count("switch ")
            }
        }
