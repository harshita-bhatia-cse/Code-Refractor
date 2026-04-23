from __future__ import annotations

import json
import os
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
        self.base_url = os.getenv(
            "LLM_BASE_URL", "https://api.groq.com/openai/v1"
        ).strip().rstrip("/")
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2048"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.max_direct_chars = int(os.getenv("LLM_MAX_DIRECT_CHARS", "8000"))
        self.chunk_size_chars = int(os.getenv("LLM_CHUNK_SIZE_CHARS", "4000"))
        self.local_refactor = LocalStyleRefactor()

    def refactor(
        self,
        code: str,
        filename: str,
        analysis: dict | None = None,
        style_profile: dict | StyleProfile | None = None,
    ) -> dict:
        language = detect_language(filename)
        profile = self._coerce_style_profile(style_profile)

        if len(code) > self.max_direct_chars and ("\n" not in code or not self.api_key):
            return self._skipped(language, filename, code, "File too large for safe chunking", profile)

        if not self.api_key:
            return self._local_result(language, filename, code, "Missing API key", profile)

        try:
            if len(code) > self.max_direct_chars:
                return self._refactor_chunked(code, filename, analysis, language, profile)
            return self._refactor_single(code, filename, analysis, language, profile)
        except Exception as exc:
            return self._local_result(language, filename, code, str(exc), profile)

    def _make_request(self, payload: dict | list[dict]):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if isinstance(payload, list):
            body = {
                "model": self.model,
                "messages": payload,
                "temperature": 0,
                "max_tokens": self.max_output_tokens,
                "response_format": {"type": "json_object"},
            }
        else:
            body = {
                "model": self.model,
                "temperature": 0,
                "max_tokens": self.max_output_tokens,
                "response_format": {"type": "json_object"},
            }
            body.update(payload)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=self.timeout_seconds,
                )

                if response.status_code == 429:
                    last_error = requests.HTTPError("429 Too Many Requests")
                    time.sleep(2 * (attempt + 1))
                    continue

                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2 * (attempt + 1))

        raise last_error or RuntimeError("LLM request failed")

    def _refactor_single(
        self,
        code: str,
        filename: str,
        analysis: dict | None,
        language: str,
        style_profile: StyleProfile,
    ) -> dict:
        focus_code = self._focused_context(code)
        messages = self._build_messages(filename, language, analysis, style_profile, focus_code)

        response = self._make_request(messages)
        content = response.json()["choices"][0]["message"]["content"]

        parsed = self._parse_json(content) or self._parse_json_content_loose(content)
        normalized = self._coerce_parsed_envelope(parsed) if parsed else None

        if not normalized:
            return self._local_result(language, filename, code, "Parsing failed", style_profile)

        refactored_code = normalized.get("refactored_code") or code
        refactored_code = self._post_process_refactored_code(
            refactored_code,
            language,
            style_profile,
        )

        return {
            "ok": True,
            "fallback": False,
            "skipped": False,
            "reason": None,
            "language": language,
            "filename": filename,
            "summary": normalized.get("summary", "Refactored using detected style"),
            "issues": self._normalize_issues(normalized.get("issues", [])),
            "refactored_code": refactored_code,
            "style_profile": style_profile.model_dump(),
        }

    def _refactor_chunked(
        self,
        code: str,
        filename: str,
        analysis: dict | None,
        language: str,
        style_profile: StyleProfile,
    ) -> dict:
        chunks = self._split_code_chunks(code, self.chunk_size_chars)
        refactored_chunks = []
        issues = []

        for index, chunk in enumerate(chunks, start=1):
            chunk_filename = f"{filename} chunk {index} of {len(chunks)}"
            result = self._refactor_single(chunk, chunk_filename, analysis, language, style_profile)
            refactored_chunks.append(result.get("refactored_code", chunk))
            issues.extend(result.get("issues", []))

        return {
            "ok": True,
            "fallback": False,
            "skipped": False,
            "reason": None,
            "language": language,
            "filename": filename,
            "summary": f"Refactored in {len(chunks)} chunks using detected style.",
            "issues": list(dict.fromkeys(issues)),
            "refactored_code": "".join(refactored_chunks),
            "style_profile": style_profile.model_dump(),
        }

    def _focused_context(self, code: str) -> str:
        rag = RAGPipeline(chunk_size=600, overlap=60)
        rag.index_code(code)
        chunks = rag.query("refactor this code while preserving behavior and local style", top_k=2)
        focus_code = "\n\n".join(chunks) if chunks else code[:1200]
        return focus_code[:1600]

    def _post_process_refactored_code(
        self,
        refactored_code: str,
        language: str,
        style_profile: StyleProfile,
    ) -> str:
        return self.local_refactor.refactor(refactored_code, language, style_profile)

    @staticmethod
    def _build_messages(
        filename: str,
        language: str,
        analysis: dict | None,
        style_profile: StyleProfile,
        code: str,
    ) -> list[dict]:
        system_prompt = (
            "You are a senior software engineer and code transformation agent.\n"
            "Rewrite the input into a realistic, human-maintained version while matching the provided StyleProfile.\n"
            "Do not return the same code. Transform formatting, naming, and structure significantly.\n"
            "Preserve the user's intended functionality, but do not preserve weak or incomplete structure.\n"
            "If code is too minimal, expand it into a realistic working version with missing best practices.\n"
            "For frontend code, improve semantic HTML, normalize spacing and attributes, fix HTML/CSS syntax, and add missing controls/layout when the UI is incomplete.\n"
            "Follow StyleProfile for indentation, naming, comment density, and structure. Avoid placeholder comments.\n"
            "Return refactored code only in the refactored_code field, with no markdown fences.\n"
            "Return one strict JSON object with exactly these keys: summary, issues, refactored_code."
        )

        user_prompt = (
            f"Filename: {filename}\n"
            f"Language: {language}\n\n"
            f"StyleProfile:\n{style_profile.to_prompt_text()}\n\n"
            f"Static analysis:\n{json.dumps(analysis or {}, ensure_ascii=True)}\n\n"
            f"Code to refactor:\n{code}\n\n"
            "Refactor rules:\n"
            "- Do not return the same code.\n"
            "- Preserve the intended behavior, but rewrite poor structure aggressively.\n"
            "- Change formatting, naming, and structure where it improves maintainability.\n"
            "- Match the naming, indentation, comment density, and structure from StyleProfile.\n"
            "- Add missing best practices for frontend code, including semantic HTML, useful form controls, and clean CSS.\n"
            "- If the input is a minimal UI mockup, expand it into a realistic working frontend file.\n"
            "- Do not add comments like 'Add styles here' or 'HTML5 Document'.\n\n"
            "Output JSON schema:\n"
            '{ "summary": "...", "issues": ["..."], "refactored_code": "..." }'
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def _split_code_chunks(code: str, max_chars: int) -> list[str]:
        max_chars = max(1, max_chars)
        lines = code.splitlines(keepends=True)
        chunks = []
        current = ""

        for line in lines:
            if len(current) + len(line) <= max_chars:
                current += line
                continue

            if current:
                chunks.append(current)
                current = ""

            if len(line) > max_chars:
                for start in range(0, len(line), max_chars):
                    chunks.append(line[start:start + max_chars])
            else:
                current = line

        if current:
            chunks.append(current)

        return chunks

    @staticmethod
    def _coerce_style_profile(style_profile: dict | StyleProfile | None) -> StyleProfile:
        if isinstance(style_profile, StyleProfile):
            return style_profile
        if isinstance(style_profile, dict):
            return StyleProfile(**style_profile)
        return StyleProfile()

    @staticmethod
    def _parse_json_content(text: str):
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        try:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                return json.loads(cleaned[start:end + 1])
        except Exception:
            return None

        return None

    @staticmethod
    def _parse_json_content_loose(text: str):
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end + 1])
        except Exception:
            return None
        return None

    def _parse_json(self, text: str):
        return self._parse_json_content(text) or self._parse_json_content_loose(text)

    @staticmethod
    def _coerce_parsed_envelope(parsed: Any) -> dict | None:
        if not isinstance(parsed, dict):
            return None

        summary = parsed.get("summary", "")
        issues = parsed.get("issues", []) or []
        refactored_code = parsed.get("refactored_code", "")

        if isinstance(refactored_code, str):
            try:
                inner = json.loads(refactored_code)
                if isinstance(inner, dict):
                    refactored_code = inner.get("refactored_code", refactored_code)
            except Exception:
                pass
            refactored_code = refactored_code.replace("\\n", "\n")

        return {
            "summary": summary,
            "issues": issues,
            "refactored_code": refactored_code,
        }

    @staticmethod
    def _normalize_issues(issues):
        clean = []
        for item in issues or []:
            if isinstance(item, dict):
                clean.append(item.get("description") or item.get("type") or str(item))
            else:
                clean.append(str(item))
        return clean

    def _fallback(
        self,
        language: str,
        filename: str,
        code: str,
        reason: str,
        style_profile: StyleProfile,
        raw_output: str | None = None,
    ) -> dict:
        return {
            "ok": True,
            "fallback": True,
            "skipped": False,
            "reason": reason,
            "language": language,
            "filename": filename,
            "summary": f"Fallback used: {reason}",
            "issues": [],
            "refactored_code": code,
            "raw_output": raw_output,
            "style_profile": style_profile.model_dump(),
        }

    def _local_result(
        self,
        language: str,
        filename: str,
        code: str,
        reason: str,
        style_profile: StyleProfile,
    ) -> dict:
        refactored_code = self.local_refactor.refactor(code, language, style_profile)
        changed = refactored_code != code

        return {
            "ok": True,
            "fallback": True,
            "skipped": False,
            "reason": reason,
            "language": language,
            "filename": filename,
            "summary": self._fallback_summary(reason, changed),
            "issues": [] if changed else ["No local deterministic cleanup was available for this code."],
            "refactored_code": refactored_code,
            "style_profile": style_profile.model_dump(),
        }

    @staticmethod
    def _fallback_summary(reason: str, changed: bool) -> str:
        if not changed:
            return f"Fallback used: {reason}"

        reason_lower = (reason or "").lower()
        if "429" in reason_lower or "too many requests" in reason_lower:
            return "Applied local style rewrite because the LLM provider is rate-limited."
        if "missing api key" in reason_lower:
            return "Applied local style rewrite because the LLM API key is missing."
        if "parsing failed" in reason_lower:
            return "Applied local style rewrite because the LLM response could not be parsed."
        return f"Applied local style rewrite because the LLM request failed: {reason}"

    def _skipped(
        self,
        language: str,
        filename: str,
        code: str,
        reason: str,
        style_profile: StyleProfile,
    ) -> dict:
        return {
            "ok": True,
            "fallback": False,
            "skipped": True,
            "reason": reason,
            "language": language,
            "filename": filename,
            "summary": "LLM refactor skipped",
            "issues": [],
            "refactored_code": code,
            "style_profile": style_profile.model_dump(),
        }
