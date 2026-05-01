from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import requests

from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.rag.rag_pipeline import RAGPipeline
from backend.ai_agents.refractor.base_refractor import BaseRefractor
from backend.ai_agents.refractor.local_refractor import LocalStyleRefactor
from backend.ai_agents.style.profile import StyleProfile


class LLMRefractorAgent(BaseRefractor):
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "llama3-8b-8192").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2048"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "5"))
        self.retry_backoff = float(os.getenv("LLM_RETRY_BACKOFF", "2"))
        self.max_direct_chars = int(os.getenv("LLM_MAX_DIRECT_CHARS", "6000"))
        self.chunk_size_chars = int(os.getenv("LLM_CHUNK_SIZE_CHARS", "3000"))
        self.local_refactor = LocalStyleRefactor()

    def refactor(self, code: str, filename: str, analysis=None, style_profile=None) -> dict:
        language = detect_language(filename)
        profile = self._coerce_style_profile(style_profile)

        if len(code) > 8000:
            return {
                "ok": True,
                "fallback": False,
                "skipped": True,
                "reason": "File too large for direct refactor",
                "language": language,
                "filename": filename,
                "summary": "Skipped LLM refactor for oversized file",
                "issues": [],
                "refactored_code": code,
                "style_profile": profile.model_dump(),
            }

        if not self.api_key:
            return self._local_result(language, filename, code, "Missing API key", profile)

        try:
            if len(code) > self.max_direct_chars:
                return self._refactor_chunked(code, filename, analysis, language, profile)
            return self._refactor_single(code, filename, analysis, language, profile)
        except Exception as exc:
            return self._local_result(language, filename, code, str(exc), profile)

    def _make_request(self, messages):
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )

                if response.status_code == 429:
                    time.sleep(self.retry_backoff ** attempt)
                    continue

                if response.status_code >= 500:
                    time.sleep(self.retry_backoff ** attempt)
                    continue

                return response
            except requests.exceptions.RequestException:
                time.sleep(self.retry_backoff ** attempt)

        return None

    def _refactor_single(self, code, filename, analysis, language, profile):
        focus_code = self._focused_context(code)
        messages = self._build_messages(filename, language, analysis, profile, focus_code)
        response = self._make_request(messages)

        if response is None:
            return self._local_result(language, filename, code, "LLM unavailable (rate limit or network)", profile)

        content = self._extract_response_content(response)
        if not content:
            return self._local_result(language, filename, code, "Invalid LLM response", profile)

        parsed = self._parse_json_content(content) or self._parse_json_content_loose(content)
        normalized = self._coerce_parsed_envelope(parsed)

        refactored = normalized.get("refactored_code") if normalized else None
        if not isinstance(refactored, str) or not refactored.strip():
            return self._local_result(language, filename, code, "LLM output invalid", profile)

        refactored = self._post_process_refactored_code(refactored, language, profile)

        return {
            "ok": True,
            "fallback": False,
            "skipped": False,
            "reason": None,
            "language": language,
            "filename": filename,
            "summary": normalized.get("summary", "Refactored"),
            "issues": normalized.get("issues", []),
            "refactored_code": refactored,
            "style_profile": profile.model_dump(),
        }

    def _refactor_chunked(self, code, filename, analysis, language, profile):
        chunks = self._split_code_chunks(code, self.chunk_size_chars)
        final_code = []
        issues = []

        for chunk in chunks:
            result = self._refactor_single(chunk, filename, analysis, language, profile)
            final_code.append(result.get("refactored_code", chunk))
            issues.extend(result.get("issues", []))

        return {
            "ok": True,
            "fallback": False,
            "skipped": False,
            "reason": None,
            "language": language,
            "filename": filename,
            "summary": "Chunked refactor",
            "issues": issues,
            "refactored_code": "".join(final_code),
            "style_profile": profile.model_dump(),
        }

    def _focused_context(self, code: str) -> str:
        rag = RAGPipeline(chunk_size=600, overlap=60)
        rag.index_code(code)
        chunks = rag.query("refactor deeply", top_k=2)
        return "\n\n".join(chunks)[:1500] if chunks else code[:1500]

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        value = (text or "").strip()
        if value.startswith("```"):
            value = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", value)
            value = re.sub(r"\s*```$", "", value)
        return value.strip()

    @classmethod
    def _parse_json_content(cls, text: str) -> dict[str, Any] | None:
        cleaned = cls._strip_code_fences(text)
        try:
            parsed = json.loads(cleaned)
        except Exception:
            return None
        return parsed if isinstance(parsed, dict) else None

    @classmethod
    def _parse_json_content_loose(cls, text: str) -> dict[str, Any] | None:
        cleaned = cls._strip_code_fences(text)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except Exception:
            return None
        return parsed if isinstance(parsed, dict) else None

    @classmethod
    def _coerce_parsed_envelope(cls, parsed: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            return {}

        summary = parsed.get("summary") or "Refactored"
        issues = parsed.get("issues")
        issues = cls._normalize_issues(issues)

        refactored = parsed.get("refactored_code")
        if isinstance(refactored, dict):
            refactored = cls._extract_code_string(refactored)
            nested = cls._parse_json_content(refactored) or cls._parse_json_content_loose(refactored) if isinstance(refactored, str) else None
        elif isinstance(refactored, str):
            nested = cls._parse_json_content(refactored) or cls._parse_json_content_loose(refactored)
        else:
            nested = None

        if isinstance(nested, dict) and isinstance(nested.get("refactored_code"), str):
            refactored = nested["refactored_code"]

        if not isinstance(refactored, str):
            refactored = json.dumps(refactored, indent=2) if refactored is not None else ""

        return {
            "summary": summary,
            "issues": issues,
            "refactored_code": refactored,
        }

    @staticmethod
    def _extract_code_string(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key in ("code", "refactored_code", "content", "text"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate
            try:
                return json.dumps(value, indent=2)
            except Exception:
                return ""
        return ""

    @staticmethod
    def _normalize_issues(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []

        normalized = []
        for item in value:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict):
                issue_type = str(item.get("type", "")).strip()
                description = str(item.get("description", "")).strip()
                if issue_type and description:
                    normalized.append(f"{issue_type}: {description}")
                elif description:
                    normalized.append(description)
                elif issue_type:
                    normalized.append(issue_type)
        return normalized

    @staticmethod
    def _extract_response_content(response) -> str | None:
        try:
            body = response.json()
        except Exception:
            return None

        if response.ok:
            try:
                return body["choices"][0]["message"]["content"]
            except Exception:
                return None

        error = body.get("error") if isinstance(body, dict) else None
        if isinstance(error, dict):
            failed_generation = error.get("failed_generation")
            if isinstance(failed_generation, str) and failed_generation.strip():
                return failed_generation

        return None

    def _coerce_style_profile(self, style_profile) -> StyleProfile:
        if isinstance(style_profile, StyleProfile):
            return style_profile
        if isinstance(style_profile, dict):
            return StyleProfile(**style_profile)
        return StyleProfile()

    def _local_result(self, language, filename, code, reason, profile):
        cleaned = self._post_process_refactored_code(code, language, profile)
        return {
            "ok": True,
            "fallback": True,
            "skipped": False,
            "reason": reason,
            "language": language,
            "filename": filename,
            "summary": f"Local refactor used because the LLM was unavailable or rate-limited: {reason}",
            "issues": [],
            "refactored_code": cleaned,
            "style_profile": profile.model_dump(),
        }

    def _split_code_chunks(self, code, size):
        return [code[index : index + size] for index in range(0, len(code), size)]

    @staticmethod
    def _build_messages(filename, language, analysis, profile, code):
        del filename, analysis
        return [
            {
                "role": "system",
                "content": (
                    "You are an expert software engineer.\n"
                    "Return strict JSON with keys: summary, issues, refactored_code.\n"
                    "issues must be an array of strings only.\n"
                    "refactored_code must always be a string.\n"
                    "Do not return nested objects for issues or refactored_code.\n"
                    "Respect the repository StyleProfile below.\n"
                    f"StyleProfile:\n{profile.to_prompt_text()}\n"
                    "Do not add comments unless the style profile clearly supports comment-heavy code.\n"
                    "If code is too minimal, expand it into a realistic, working example while preserving the user intent.\n"
                    "For HTML, prefer semantic HTML and accessible labels.\n"
                ),
            },
            {
                "role": "user",
                "content": f"Refactor this {language} code:\n\n{code}",
            },
        ]

    def _post_process_refactored_code(self, code: str, language: str, profile: StyleProfile) -> str:
        return self.local_refactor.refactor(code, language, profile)
