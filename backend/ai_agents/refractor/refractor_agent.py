import json
import os
import time
from typing import Any

import requests

from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.rag.rag_pipeline import RAGPipeline
from backend.ai_agents.refractor.base_refractor import BaseRefractor
from backend.utils.env import load_project_env

load_project_env()


class LLMRefractorAgent(BaseRefractor):
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        

        self.model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant ").strip()
        self.base_url = os.getenv(
            "LLM_BASE_URL", "https://api.groq.com/openai/v1"
        ).strip().rstrip("/")
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1500"))
        self.max_retries = 3

    def refactor(self, code: str, filename: str, analysis: dict | None = None) -> dict:
        language = detect_language(filename)

        if not self.api_key:
            return self._fallback(language, filename, code, "Missing API key")

        if len(code) > 8000:
            return self._fallback(language, filename, code, "File too large")

        try:
            return self._refactor_single(code, filename, analysis, language)
        except Exception as exc:
            return self._fallback(language, filename, code, str(exc))

    def _make_request(self, messages: list[dict[str, str]]):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=self.timeout_seconds,
                )
                if response.status_code == 429:
                    print("Rate limited, retrying...")
                    time.sleep(2 * (attempt + 1))
                    continue
                if response.status_code != 200:
                    print(f"LLM ERROR: {response.status_code} {response.text}")
                    return None
                return response
            except Exception as exc:
                print(f"Request error: {exc}")
                time.sleep(2)

        return None

    def _refactor_single(self, code, filename, analysis, language):
        rag = RAGPipeline(chunk_size=600, overlap=60)
        rag.index_code(code)

        chunks = rag.query("improve readability", top_k=2)
        focus_code = "\n\n".join(chunks) if chunks else code[:800]
        if len(focus_code) > 1200:
            focus_code = focus_code[:1200]

        system_prompt = (
            "You are a senior software engineer.\n"
            "Refactor code for readability and maintainability.\n"
            "Return ONLY JSON:\n"
            '{ "summary": string, "issues": [], "refactored_code": string }'
        )
        user_prompt = (
            f"Filename: {filename}\n"
            f"Language: {language}\n\n"
            f"Analysis:\n{json.dumps(analysis or {})}\n\n"
            f"Code:\n{focus_code}"
        )

        response = self._make_request(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        if response is None:
            return self._fallback(language, filename, code, "LLM unavailable")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except Exception:
            return self._fallback(language, filename, code, "Invalid response")

        parsed = self._parse_json(content)
        if not parsed:
            parsed = self._parse_json_content(content) or self._parse_json_content_loose(content)
        normalized = self._coerce_parsed_envelope(parsed) if parsed else None
        if not normalized:
            return self._fallback(language, filename, code, "Parsing failed")

        return {
            "ok": True,
            "language": language,
            "filename": filename,
            "summary": normalized.get("summary") or "No summary",
            "issues": self._normalize_issues(normalized.get("issues")),
            "refactored_code": normalized.get("refactored_code") or code,
        }

    def _parse_json(self, text: str):
        try:
            return json.loads(text)
        except Exception:
            try:
                start = text.find("{")
                end = text.rfind("}")
                return json.loads(text[start : end + 1])
            except Exception:
                return None

    @staticmethod
    def _parse_json_content(text: str):
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return None

    @staticmethod
    def _parse_json_content_loose(text: str):
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start : end + 1])
        except Exception:
            return None
        return None

    @staticmethod
    def _coerce_parsed_envelope(parsed: Any):
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

    def _normalize_issues(self, issues):
        clean = []
        for item in issues or []:
            if isinstance(item, dict):
                clean.append(item.get("description") or item.get("type") or str(item))
            else:
                clean.append(str(item))
        return clean

    def _fallback(self, language, filename, code, reason):
        reason_text = str(reason)
        return {
            "ok": True,
            "fallback": True,
            "skipped": "file too large" in reason_text.lower(),
            "reason": reason_text,
            "language": language,
            "filename": filename,
            "summary": f"Fallback used: {reason_text}",
            "issues": [],
            "refactored_code": code,
        }
