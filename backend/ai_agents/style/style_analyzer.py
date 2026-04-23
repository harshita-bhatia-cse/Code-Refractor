from __future__ import annotations

import os
import re
from collections import Counter

from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.style.profile import FileStyleMetrics


IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
FUNCTION_PATTERNS = {
    "python": re.compile(r"^\s*def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", re.MULTILINE),
    "javascript": re.compile(
        r"^\s*(?:async\s+)?function\s+[A-Za-z_$][A-Za-z0-9_$]*\s*\(|"
        r"^\s*(?:const|let|var)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
        re.MULTILINE,
    ),
    "typescript": re.compile(
        r"^\s*(?:async\s+)?function\s+[A-Za-z_$][A-Za-z0-9_$]*\s*\(|"
        r"^\s*(?:const|let|var)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
        re.MULTILINE,
    ),
    "java": re.compile(
        r"^\s*(?:public|private|protected)?\s*(?:static\s+)?[A-Za-z0-9_<>\[\]]+\s+"
        r"[A-Za-z_][A-Za-z0-9_]*\s*\([^;]*\)\s*\{",
        re.MULTILINE,
    ),
}


class StyleAnalyzer:
    LANGUAGE_KEYWORDS = {
        "python": {"def", "class", "return", "import", "from", "if", "else", "for", "while", "try", "except"},
        "javascript": {"function", "const", "let", "var", "return", "if", "else", "for", "while", "import", "export"},
        "typescript": {"function", "const", "let", "var", "return", "if", "else", "for", "while", "import", "export"},
        "java": {"public", "private", "protected", "class", "return", "if", "else", "for", "while", "static", "void"},
        "html": {"html", "head", "body", "div", "span", "script", "style", "class", "id"},
        "css": {"px", "rem", "em", "solid", "flex", "grid", "block", "none"},
    }

    def analyze_file(self, path: str, code: str) -> FileStyleMetrics:
        language = detect_language(path)
        lines = code.splitlines()

        return FileStyleMetrics(
            path=path,
            language=language,
            naming_counts=dict(self._detect_naming(code, language)),
            indentation_counts=dict(self._detect_indentation(lines)),
            line_count=len(lines),
            avg_function_length=self._avg_function_length(code, language),
            function_count=self._function_count(code, language),
            comment_density=self._comment_density(lines, language),
            comment_styles=dict(self._comment_styles(lines, language)),
            structure_counts=dict(self._structure_counts(code, language)),
            frontend_group=self._frontend_group(path, language),
        )

    def _detect_naming(self, code: str, language: str) -> Counter:
        counts = Counter()
        keywords = self.LANGUAGE_KEYWORDS.get(language, set())

        for identifier in IDENTIFIER_RE.findall(code):
            if identifier in keywords or identifier.isupper() or len(identifier) <= 1:
                continue
            if re.fullmatch(r"[a-z]+(?:_[a-z0-9]+)+", identifier):
                counts["snake_case"] += 1
            elif re.fullmatch(r"[a-z]+(?:[A-Z][a-z0-9]*)+", identifier):
                counts["camelCase"] += 1
            elif re.fullmatch(r"[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)*", identifier):
                counts["PascalCase"] += 1
            elif re.fullmatch(r"[a-z][a-z0-9]*", identifier):
                counts["lowercase"] += 1

        return counts

    @staticmethod
    def _detect_indentation(lines: list[str]) -> Counter:
        counts = Counter()
        for line in lines:
            if not line.strip():
                continue
            prefix = line[: len(line) - len(line.lstrip(" \t"))]
            if not prefix:
                continue
            if "\t" in prefix:
                counts["tabs"] += 1
            else:
                spaces = len(prefix)
                if spaces % 4 == 0:
                    counts["4 spaces"] += 1
                elif spaces % 2 == 0:
                    counts["2 spaces"] += 1
                else:
                    counts["variable spaces"] += 1
        return counts

    @staticmethod
    def _function_count(code: str, language: str) -> int:
        pattern = FUNCTION_PATTERNS.get(language)
        return len(pattern.findall(code)) if pattern else 0

    def _avg_function_length(self, code: str, language: str) -> float:
        pattern = FUNCTION_PATTERNS.get(language)
        if not pattern:
            return 0.0

        starts = [code[: match.start()].count("\n") for match in pattern.finditer(code)]
        if not starts:
            return 0.0

        total_lines = len(code.splitlines())
        lengths = []
        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else total_lines
            lengths.append(max(1, end - start))
        return sum(lengths) / len(lengths)

    @staticmethod
    def _comment_density(lines: list[str], language: str) -> float:
        if not lines:
            return 0.0
        comment_markers = ("#",) if language == "python" else ("//", "/*", "*", "<!--")
        comment_lines = sum(1 for line in lines if line.strip().startswith(comment_markers))
        return comment_lines / len(lines)

    @staticmethod
    def _comment_styles(lines: list[str], language: str) -> Counter:
        counts = Counter()
        for line in lines:
            stripped = line.strip()
            if language == "python" and stripped.startswith("#"):
                counts["hash"] += 1
            elif stripped.startswith("//"):
                counts["double_slash"] += 1
            elif stripped.startswith("/*") or stripped.startswith("*"):
                counts["block"] += 1
            elif stripped.startswith("<!--"):
                counts["html"] += 1
        return counts

    @staticmethod
    def _structure_counts(code: str, language: str) -> Counter:
        counts = Counter()
        counts["classes"] = len(re.findall(r"\bclass\s+[A-Za-z_][A-Za-z0-9_]*", code))
        counts["imports"] = len(re.findall(r"^\s*(?:import|from|const\s+.*require|#include)\b", code, re.MULTILINE))
        counts["functions"] = StyleAnalyzer._function_count(code, language)
        counts["inline_handlers"] = len(re.findall(r"\bon[A-Z][A-Za-z]+\s*=", code))
        return counts

    @staticmethod
    def _frontend_group(path: str, language: str) -> str | None:
        if language not in {"html", "css", "javascript", "typescript"}:
            return None
        return os.path.normpath(os.path.dirname(path))
