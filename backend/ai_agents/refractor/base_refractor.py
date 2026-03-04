class BaseRefractor:
    def refactor(self, code: str, filename: str, analysis: dict | None = None) -> dict:
        raise NotImplementedError
