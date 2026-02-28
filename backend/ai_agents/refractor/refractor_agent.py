import json
import os
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

        system_prompt = (
            "You are a senior code reviewer and refactoring engineer. "
            "Improve code readability, naming, structure, and maintainability while preserving behavior. "
            "Return JSON only with keys: summary (string), issues (array of strings), refactored_code (string). "
            "Do not add markdown fences."
        )

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

        parsed = self._parse_json_content(content)
        if not parsed:
            return {
                "ok": False,
                "language": language,
                "filename": filename,
                "error": "LLM output was not valid JSON",
                "summary": "Received non-JSON output from LLM.",
                "issues": [],
                "refactored_code": code,
                "raw_output": content,
            }

        issues = parsed.get("issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)]

        return {
            "ok": True,
            "language": language,
            "filename": filename,
            "error": None,
            "summary": str(parsed.get("summary", "")).strip(),
            "issues": [str(item) for item in issues],
            "refactored_code": str(parsed.get("refactored_code", code)),
        }

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
