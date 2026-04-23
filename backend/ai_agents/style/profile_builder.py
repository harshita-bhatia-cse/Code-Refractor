from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from backend.ai_agents.core.file_scanner import FileScanner
from backend.ai_agents.style.profile import FileStyleMetrics, StyleProfile
from backend.ai_agents.style.style_analyzer import StyleAnalyzer


class StyleProfileBuilder:
    def __init__(self):
        self.scanner = FileScanner()
        self.analyzer = StyleAnalyzer()

    def build_from_repositories(self, repo_paths: Iterable[str]) -> StyleProfile:
        paths = list(repo_paths)
        file_metrics: list[FileStyleMetrics] = []

        for repo_path in paths:
            for path, code in self.scanner.scan(repo_path):
                file_metrics.append(self.analyzer.analyze_file(path, code))

        return self.build_from_file_metrics(file_metrics, repositories_analyzed=len(paths))

    def build_from_file_metrics(
        self,
        file_metrics: list[FileStyleMetrics],
        repositories_analyzed: int = 1,
    ) -> StyleProfile:
        naming = Counter()
        indentation = Counter()
        comment_styles = Counter()
        structure = Counter()
        languages = Counter()
        function_lengths: list[float] = []
        comment_densities: list[float] = []
        frontend_groups: dict[str, set[str]] = defaultdict(set)

        for metrics in file_metrics:
            naming.update(metrics.naming_counts)
            indentation.update(metrics.indentation_counts)
            comment_styles.update(metrics.comment_styles)
            structure.update(metrics.structure_counts)
            languages[metrics.language] += 1
            if metrics.avg_function_length:
                function_lengths.append(metrics.avg_function_length)
            comment_densities.append(metrics.comment_density)
            if metrics.frontend_group:
                frontend_groups[metrics.frontend_group].add(metrics.language)

        dominant_naming = self._dominant(naming, "mixed")
        dominant_indentation = self._dominant(indentation, "unknown")
        avg_comment_density = sum(comment_densities) / max(len(comment_densities), 1)
        avg_function_length = sum(function_lengths) / max(len(function_lengths), 1)

        return StyleProfile(
            naming=dominant_naming,
            indentation=dominant_indentation,
            comments=self._describe_comments(avg_comment_density, comment_styles),
            structure=self._describe_structure(structure, frontend_groups),
            function_style=self._describe_function_style(avg_function_length),
            languages=sorted(lang for lang in languages if lang != "unknown"),
            repositories_analyzed=repositories_analyzed,
            files_analyzed=len(file_metrics),
            confidence=self._confidence(file_metrics, naming, indentation),
            evidence={
                "naming_counts": dict(naming),
                "indentation_counts": dict(indentation),
                "comment_styles": dict(comment_styles),
                "avg_comment_density": round(avg_comment_density, 4),
                "avg_function_length": round(avg_function_length, 2),
                "structure_counts": dict(structure),
                "frontend_contexts": {
                    group: sorted(values) for group, values in frontend_groups.items()
                },
                "language_counts": dict(languages),
            },
        )

    @staticmethod
    def _dominant(counter: Counter, fallback: str) -> str:
        if not counter:
            return fallback
        return counter.most_common(1)[0][0]

    @staticmethod
    def _describe_comments(density: float, styles: Counter) -> str:
        style = styles.most_common(1)[0][0] if styles else "plain"
        if density < 0.03:
            level = "sparse"
        elif density > 0.15:
            level = "comment-heavy"
        else:
            level = "balanced"
        return f"{level}, {style}"

    @staticmethod
    def _describe_function_style(avg_length: float) -> str:
        if avg_length == 0:
            return "not enough function evidence"
        if avg_length <= 15:
            return "short functions"
        if avg_length <= 40:
            return "moderate functions"
        return "long functions"

    @staticmethod
    def _describe_structure(structure: Counter, frontend_groups: dict[str, set[str]]) -> str:
        functions = structure.get("functions", 0)
        classes = structure.get("classes", 0)
        imports = structure.get("imports", 0)
        complete_frontend_groups = sum(
            1 for values in frontend_groups.values()
            if "html" in values and "css" in values and ("javascript" in values or "typescript" in values)
        )

        parts = []
        if imports >= max(3, functions // 2):
            parts.append("modular")
        elif functions <= 2 and classes <= 1:
            parts.append("inline")
        else:
            parts.append("mixed")

        if classes > functions:
            parts.append("class-oriented")
        elif functions > 0:
            parts.append("function-oriented")

        if complete_frontend_groups:
            parts.append("unified frontend context")

        return ", ".join(parts)

    @staticmethod
    def _confidence(file_metrics: list[FileStyleMetrics], naming: Counter, indentation: Counter) -> float:
        if not file_metrics:
            return 0.0

        signals = 0
        if naming:
            signals += 1
        if indentation:
            signals += 1
        if any(item.function_count for item in file_metrics):
            signals += 1
        if any(item.comment_density > 0 for item in file_metrics):
            signals += 1

        coverage = min(1.0, len(file_metrics) / 20)
        return round((signals / 4) * 0.6 + coverage * 0.4, 2)
