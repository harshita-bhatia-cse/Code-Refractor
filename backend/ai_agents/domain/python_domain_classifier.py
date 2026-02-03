class PythonDomainClassifier:
    """
    Classifies Python code into a tech domain
    based on detected libraries.
    """

    def classify(self, libraries: list[str]) -> str:
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
