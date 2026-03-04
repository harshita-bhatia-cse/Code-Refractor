class PythonDomainClassifier:
    """
    Classifies Python code into a tech domain
    based on detected libraries.
    """

    def classify(self, libraries: list[str] | str) -> str:
        if isinstance(libraries, str):
            libs = self._extract_imports_from_code(libraries)
        else:
            libs = set(libraries)

        if libs & {"tensorflow", "torch", "keras"}:
            return "deep_learning"

        if libs & {"nltk", "spacy", "transformers"}:
            return "nlp"

        if libs & {"sklearn", "numpy", "pandas"}:
            return "machine_learning"

        if libs & {"fastapi", "flask", "django"}:
            return "backend"

        if libs & {"pandas", "matplotlib", "seaborn"}:
            return "data_science"

        return "general"

    @staticmethod
    def _extract_imports_from_code(code: str) -> set[str]:
        found = set()
        for line in code.splitlines():
            s = line.strip()
            if s.startswith("import "):
                part = s.replace("import ", "", 1).split(",")
                for item in part:
                    found.add(item.strip().split(".")[0])
            elif s.startswith("from "):
                bits = s.split()
                if len(bits) >= 2:
                    found.add(bits[1].split(".")[0])
        return {x for x in found if x}
