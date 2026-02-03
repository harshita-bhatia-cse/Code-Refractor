class CommonStyle:
    def analyze(self, code):
        lines = code.splitlines()
        return {
            "avg_line_length": sum(len(l) for l in lines) // max(len(lines), 1)
        }
