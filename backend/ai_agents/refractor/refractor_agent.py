import json
import os
import ast
from typing import Any

import requests

from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.refractor.base_refractor import BaseRefractor


class LLMRefractorAgent(BaseRefractor):
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "gpt-4.1-mini").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096"))

    def refactor(self, code: str, filename: str, analysis: dict | None = None) -> dict:
        language = detect_language(filename)

        if not self.api_key:
            return {
                "ok": False,
                "language": language,
                "filename": filename,
                "error": "LLM_API_KEY is not configured",
                "summary": "LLM refactor is disabled because no API key was provided.",
                "issues": [],
                "refactored_code": code,
            }

        system_prompt = self._build_system_prompt(language)

        analysis_text = json.dumps(analysis, ensure_ascii=False) if analysis else "{}"
        user_prompt = (
            f"Filename: {filename}\n"
            f"Detected language: {language}\n"
            f"Existing static analysis: {analysis_text}\n\n"
            "Task:\n"
            "1) Identify key readability/standard-style issues.\n"
            "2) Refactor the code into a human-readable standard form.\n"
            "3) Preserve behavior as much as possible.\n"
            "4) Keep the response strictly valid JSON.\n\n"
            "Code:\n"
            f"{code}"
        )

        payload = {
            "model": self.model,
            "temperature": 0.2,
            "max_tokens": self.max_output_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except Exception as exc:
            return {
                "ok": False,
                "language": language,
                "filename": filename,
                "error": f"LLM request failed: {exc}",
                "summary": "Failed to call LLM service.",
                "issues": [],
                "refactored_code": code,
            }

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            finish_reason = data["choices"][0].get("finish_reason")
        except Exception:
            return {
                "ok": False,
                "language": language,
                "filename": filename,
                "error": "Unexpected LLM response format",
                "summary": "LLM responded with an unexpected format.",
                "issues": [],
                "refactored_code": code,
            }

        if finish_reason == "length":
            return {
                "ok": False,
                "language": language,
                "filename": filename,
                "error": "LLM output was truncated due to token limit (finish_reason=length)",
                "summary": "LLM output was truncated. Increase LLM_MAX_OUTPUT_TOKENS or use a smaller input.",
                "issues": [],
                "refactored_code": code,
                "raw_output": content,
            }

        parsed = self._parse_json_content(content)
        if not parsed:
            # Fallback: accept plain-text model output and normalize when possible.
            fallback_code = self._extract_code_from_text(content)
            normalized_code, normalization_issue = self._normalize_refactored_code(
                code=fallback_code,
                language=language,
            )
            issues = []
            if normalization_issue:
                issues.append(normalization_issue)
            issues.append("LLM response did not follow required JSON envelope; used fallback parsing.")
            return {
                "ok": True,
                "language": language,
                "filename": filename,
                "error": None,
                "summary": "Used fallback parser because model returned non-JSON envelope.",
                "issues": issues,
                "refactored_code": normalized_code,
                "raw_output": content,
            }

        issues = parsed.get("issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)]

        normalized_code, normalization_issue = self._normalize_refactored_code(
            code=str(parsed.get("refactored_code", code)),
            language=language,
        )
        if normalization_issue:
            issues.append(normalization_issue)

        return {
            "ok": True,
            "language": language,
            "filename": filename,
            "error": None,
            "summary": str(parsed.get("summary", "")).strip(),
            "issues": [str(item) for item in issues],
            "refactored_code": normalized_code,
        }

    @staticmethod
    def _build_system_prompt(language: str) -> str:
        base = (
            "You are a senior code reviewer and refactoring engineer. "
            "Improve readability, naming, structure, and maintainability while preserving behavior. "
            "Return JSON only with keys: summary (string), issues (array of strings), refactored_code (string). "
            "Do not include markdown fences. "
        )

        if language == "json":
            return (
                base
                + "The refactored_code must be STRICT valid JSON text with double quotes, lowercase true/false/null, "
                + "and no trailing commas. Never return Python dict syntax."
            )

        return base + "The refactored_code must be valid in its original language."

    @staticmethod
    def _normalize_refactored_code(code: str, language: str) -> tuple[str, str | None]:
        if language != "json":
            return code, None

        # If already valid JSON, normalize formatting.
        try:
            payload = json.loads(code)
            return json.dumps(payload, indent=2, ensure_ascii=False), None
        except Exception:
            pass

        # Recover from Python-dict style output when possible.
        try:
            payload = ast.literal_eval(code)
            return json.dumps(payload, indent=2, ensure_ascii=False), (
                "LLM returned non-JSON syntax; converted to valid JSON format automatically."
            )
        except Exception:
            return code, "LLM returned invalid JSON syntax and auto-normalization failed."

    @staticmethod
    def _extract_code_from_text(content: str) -> str:
        text = (content or "").strip()
        if not text:
            return ""

        # Prefer fenced code body if present.
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                candidate = parts[1]
                lines = candidate.splitlines()
                if lines and lines[0].strip().lower() in {
                    "json", "javascript", "typescript", "python", "java", "go", "c", "cpp", "csharp", "php", "rust"
                }:
                    return "\n".join(lines[1:]).strip()
                return candidate.strip()

        return text

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, Any] | None:
        content = content.strip()

        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        snippet = content[start : end + 1]
        try:
            data = json.loads(snippet)
            if isinstance(data, dict):
                return data
        except Exception:
            return None

        return None
