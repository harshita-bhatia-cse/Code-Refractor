import os

class FileScanner:
    def scan(self, root):
        result = []
        for r, _, files in os.walk(root):
            for f in files:
                path = os.path.join(r, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        result.append((path, fh.read()))
                except:
                    pass
        return result
