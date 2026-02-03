import ast
from backend.ai_agents.metrics.common_metrics import CommonMetrics


class PythonMetrics(CommonMetrics):
    def analyze(self, code: str):
        base = super().analyze(code)

        try:
            tree = ast.parse(code)
        except Exception:
            # If AST parsing fails, return base metrics safely
            return base

        # ---------- FUNCTIONS ----------
        base["functions"] = len(
            [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        )

        # ---------- CLASSES ----------
        base["classes"] = len(
            [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        )

        # ---------- CONDITIONALS ----------
        base["conditionals"] = {
            "if": len([n for n in ast.walk(tree) if isinstance(n, ast.If)]),
            "for": len([n for n in ast.walk(tree) if isinstance(n, ast.For)]),
            "while": len([n for n in ast.walk(tree) if isinstance(n, ast.While)]),
            "switch": 0,  # Python has no switch (match-case handled separately)
        }

        # ---------- LIBRARIES ----------
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        base["libraries"] = sorted(imports)

        return base
