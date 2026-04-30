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
        # ✅ ENV CONFIG (FIXED)
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "llama3-8b-8192").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")

        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2048"))

        # ✅ STRONG RETRY CONFIG
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "5"))
        self.retry_backoff = float(os.getenv("LLM_RETRY_BACKOFF", "2"))

        self.max_direct_chars = int(os.getenv("LLM_MAX_DIRECT_CHARS", "6000"))
        self.chunk_size_chars = int(os.getenv("LLM_CHUNK_SIZE_CHARS", "3000"))

        self.local_refactor = LocalStyleRefactor()

        print("===== LLM CONFIG =====")
        print("API KEY:", "SET" if self.api_key else "MISSING")
        print("MODEL:", self.model)
        print("BASE URL:", self.base_url)

    # ============================================================
    # MAIN ENTRY
    # ============================================================
    def refactor(self, code: str, filename: str, analysis=None, style_profile=None) -> dict:
        language = detect_language(filename)
        profile = self._coerce_style_profile(style_profile)

        # ❌ NO API KEY → DIRECT FALLBACK
        if not self.api_key:
            return self._local_result(language, filename, code, "Missing API key", profile)

        try:
            if len(code) > self.max_direct_chars:
                return self._refactor_chunked(code, filename, analysis, language, profile)

            return self._refactor_single(code, filename, analysis, language, profile)

        except Exception as e:
            print("🔥 LLM CRASH:", str(e))
            return self._local_result(language, filename, code, str(e), profile)

    # ============================================================
    # 🔥 IMPROVED REQUEST HANDLER
    # ============================================================
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
                print(f"🚀 LLM REQUEST ATTEMPT {attempt}")

                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )

                # 🔥 HANDLE RATE LIMIT
                if response.status_code == 429:
                    wait = self.retry_backoff ** attempt
                    print(f"⚠️ RATE LIMITED → waiting {wait}s")
                    time.sleep(wait)
                    continue

                # 🔥 HANDLE SERVER ERRORS
                if response.status_code >= 500:
                    wait = self.retry_backoff ** attempt
                    print(f"⚠️ SERVER ERROR {response.status_code} → retrying in {wait}s")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                wait = self.retry_backoff ** attempt
                print(f"⚠️ NETWORK ERROR: {e} → retrying in {wait}s")
                time.sleep(wait)

        print("❌ LLM FAILED AFTER RETRIES")
        return None

    # ============================================================
    # 🔥 SINGLE REFACTOR (ROBUST)
    # ============================================================
    def _refactor_single(self, code, filename, analysis, language, profile):

        focus_code = self._focused_context(code)

        messages = self._build_messages(filename, language, analysis, profile, focus_code)

        response = self._make_request(messages)

        # ❌ HARD FAIL → FALLBACK
        if response is None:
            return self._local_result(
                language,
                filename,
                code,
                "LLM unavailable (rate limit or network)",
                profile
            )

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except Exception:
            return self._local_result(language, filename, code, "Invalid LLM response", profile)

        print("🔥 RAW LLM RESPONSE:\n", content)

        parsed = self._parse_json(content)

        refactored = parsed.get("refactored_code") if parsed else None

        # 🔥 FIX OBJECT → STRING
        if isinstance(refactored, dict):
            refactored = "\n".join(refactored.keys())

        # 🔥 RETRY IF BAD OUTPUT
        if not refactored or not isinstance(refactored, str):
            print("⚠️ BAD OUTPUT → retrying once")

            retry_messages = [
                {
                    "role": "system",
                    "content": "Return ONLY valid code string. No JSON. No object."
                },
                {
                    "role": "user",
                    "content": code
                }
            ]

            response = self._make_request(retry_messages)

            if response:
                try:
                    content = response.json()["choices"][0]["message"]["content"]
                    refactored = content.strip()
                except:
                    refactored = None

        # 🔥 FINAL FALLBACK
        if not refactored:
            print("⚠️ USING LOCAL FALLBACK")
            return self._local_result(language, filename, code, "LLM output invalid", profile)

        return {
            "ok": True,
            "fallback": False,
            "skipped": False,
            "reason": None,
            "language": language,
            "filename": filename,
            "summary": parsed.get("summary", "Refactored") if parsed else "Refactored",
            "issues": parsed.get("issues", []) if parsed else [],
            "refactored_code": refactored,
            "style_profile": profile.model_dump(),
        }

    # ============================================================
    # CHUNKED
    # ============================================================
    def _refactor_chunked(self, code, filename, analysis, language, profile):
        chunks = self._split_code_chunks(code, self.chunk_size_chars)

        final_code = ""
        issues = []

        for chunk in chunks:
            result = self._refactor_single(chunk, filename, analysis, language, profile)
            final_code += result.get("refactored_code", chunk)
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
            "refactored_code": final_code,
            "style_profile": profile.model_dump(),
        }

    # ============================================================
    # RAG
    # ============================================================
    def _focused_context(self, code):
        rag = RAGPipeline(chunk_size=600, overlap=60)
        rag.index_code(code)
        chunks = rag.query("refactor deeply", top_k=2)
        return "\n\n".join(chunks)[:1500] if chunks else code[:1500]

    # ============================================================
    # PARSER
    # ============================================================
    def _parse_json(self, text):
        try:
            return json.loads(text)
        except:
            try:
                start = text.find("{")
                end = text.rfind("}")
                return json.loads(text[start:end + 1])
            except:
                return {}

    def _coerce_style_profile(self, sp):
        if isinstance(sp, StyleProfile):
            return sp
        if isinstance(sp, dict):
            return StyleProfile(**sp)
        return StyleProfile()

    # ============================================================
    # 🔥 IMPROVED FALLBACK MESSAGE
    # ============================================================
    def _local_result(self, language, filename, code, reason, profile):
        return {
            "ok": True,
            "fallback": True,
            "skipped": False,
            "reason": reason,
            "language": language,
            "filename": filename,
            "summary": "⚠️ LLM unavailable — fallback used",
            "issues": [],
            "refactored_code": self.local_refactor.refactor(code, language, profile),
            "style_profile": profile.model_dump(),
        }

    def _split_code_chunks(self, code, size):
        return [code[i:i + size] for i in range(0, len(code), size)]

    # ============================================================
    # PROMPT
    # ============================================================
    def _build_messages(self, filename, language, analysis, profile, code):
        return [
            {
                "role": "system",
                "content": (
                    "You are an expert software engineer.\n"
                    "Refactor code for readability.\n"
                    "Return ONLY JSON with:\n"
                    "summary, issues, refactored_code (STRING).\n"
                )
            },
            {
                "role": "user",
                "content": f"Refactor this {language} code:\n\n{code}"
            }
        ]