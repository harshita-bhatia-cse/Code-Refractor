import os

class StructureAgent:
    def analyze(self, root):
        tree = {}
        for r, d, f in os.walk(root):
            tree[r] = f
        return tree
