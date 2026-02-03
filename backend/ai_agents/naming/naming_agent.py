class NamingAgent:
    def analyze(self, code):
        return {
            "snake_case": code.count("_"),
            "camelCase": sum(1 for c in code if c.isupper())
        }
