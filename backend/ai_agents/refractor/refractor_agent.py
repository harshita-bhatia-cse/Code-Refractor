# import json
# import os
# import time
# import random
# from typing import Any

# import requests

# from backend.ai_agents.core.language_detector import detect_language
# from backend.ai_agents.refractor.base_refractor import BaseRefractor
# from backend.ai_agents.rag.rag_pipeline import RAGPipeline


# class LLMRefractorAgent(BaseRefractor):
#     """
#     Groq-backed refactor agent with chunking support and robust JSON parsing.
#     Compatible with existing tests that exercise parsing helpers and chunking.
#     """

#     def __init__(self):
#         # Groq API config
#         self.api_key = os.getenv("LLM_API_KEY", "").strip()
#         self.model = os.getenv("LLM_MODEL", "llama3-8b-8192").strip()
#         self.base_url = os.getenv(
#             "LLM_BASE_URL", "https://api.groq.com/openai/v1"
#         ).strip().rstrip("/")

#         self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
#         self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2048"))

#         # Chunking controls
#         self.chunk_enabled = os.getenv("LLM_CHUNK_ENABLED", "1").strip().lower() not in {
#             "0",
#             "false",
#             "no",
#         }
#         self.max_input_chars = int(os.getenv("LLM_MAX_INPUT_CHARS", "4000"))
#         self.chunk_size_chars = int(
#             os.getenv("LLM_CHUNK_SIZE_CHARS", str(self.max_input_chars))
#         )
#         self.chunk_shrink_factor = float(os.getenv("LLM_CHUNK_SHRINK_FACTOR", "0.75"))
#         self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
#         self.retry_backoff_base = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "1.0"))
#         self.max_chunks = int(os.getenv("LLM_CHUNK_MAX_CHUNKS", "50"))

#         # request retry for rate limits
#         self.request_max_retries = int(os.getenv("LLM_REQUEST_MAX_RETRIES", "5"))
#         self.request_retry_backoff = float(os.getenv("LLM_REQUEST_RETRY_BACKOFF", "2.0"))

#     # =========================
#     # ENTRY
#     # =========================
#     def refactor(self, code: str, filename: str, analysis: dict | None = None) -> dict:
#         language = detect_language(filename)

#         if not self.api_key:
#             return self._error(language, filename, "Missing API key", code)

#         if self.chunk_enabled and len(code) > self.max_input_chars:
#             return self._refactor_chunked(code, filename, analysis, language)

#         return self._refactor_single(code, filename, analysis, language)

#     # =========================
#     # GROQ REQUEST
#     # =========================
#     def _make_request(self, payload: dict | list[dict]):
#         """
#         Send a chat completion request to the LLM provider.

#         Returns the raw response object so callers (and tests) can inspect HTTP
#         details like status_code. Retries on 429 with exponential backoff.
#         """

#         url = f"{self.base_url}/chat/completions"
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json",
#         }

#         # Accept either a list of messages or a full payload dict.
#         if isinstance(payload, list):
#             request_body = {
#                 "model": self.model,
#                 "messages": payload,
#                 "temperature": 0,
#                 "max_tokens": self.max_output_tokens,
#                 "response_format": {"type": "json_object"},
#             }
#         else:
#             # Merge defaults with caller-provided values; caller overrides defaults.
#             request_body = {
#                 "model": self.model,
#                 "temperature": 0,
#                 "max_tokens": self.max_output_tokens,
#                 "response_format": {"type": "json_object"},
#             }
#             request_body.update(payload)

#         backoff = self.retry_backoff_base if self.retry_backoff_base is not None else 0
#         last_error = None
#         for attempt in range(self.request_max_retries + 1):
#             try:
#                 response = requests.post(
#                     url,
#                     headers=headers,
#                     json=request_body,
#                     timeout=self.timeout_seconds,
#                 )

#                 if response.status_code == 429:
#                     last_error = requests.HTTPError(
#                         f"429 Too Many Requests (attempt {attempt + 1})"
#                     )
#                     retry_after = response.headers.get("Retry-After")
#                     sleep_for = (
#                         float(retry_after)
#                         if retry_after is not None and retry_after.isdigit()
#                         else backoff * (attempt + 1)
#                     )
#                     # add jitter to avoid thundering herd
#                     sleep_for += random.uniform(0, self.request_retry_backoff)
#                     time.sleep(max(sleep_for, 0))
#                     continue

#                 response.raise_for_status()
#                 return response
#             except Exception as exc:
#                 last_error = exc
#                 if attempt < self.request_max_retries:
#                     sleep_for = backoff * (attempt + 1) + random.uniform(
#                         0, self.request_retry_backoff
#                     )
#                     time.sleep(max(sleep_for, 0))
#                     continue
#                 break

#         raise last_error or RuntimeError("Unknown request failure")

#     # =========================
#     # SINGLE REFACTOR
#     # =========================
#     def _refactor_single(self, code, filename, analysis, language):

#         # --- RAG retrieval to supply focused context ---
#         rag = RAGPipeline()
#         rag.index_code(code)
#         relevant_chunks = rag.query("refactor this code for readability", top_k=3)
#         context = "\n\n".join(relevant_chunks[:3])

#         system_prompt = (
#             "You are a senior software engineer.\n"
#             "Refactor code for readability and maintainability.\n"
#             "Return STRICT JSON object only, no prose, no code fences:\n"
#             "{ \"summary\": string, \"issues\": [], \"refactored_code\": string }"
#         )

#         user_prompt = (
#             f"Filename: {filename}\n"
#             f"Language: {language}\n"
#             f"Analysis: {json.dumps(analysis or {})}\n\n"
#             f"Relevant context:\n{context}\n\n"
#             f"Target code:\n{code}"
#         )

#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt},
#         ]

#         try:
#             response = self._make_request(messages)
#             data = response.json()
#             content = data["choices"][0]["message"]["content"]
#         except Exception as e:
#             return self._error(language, filename, str(e), code)

#         parsed = self._parse_json(content) or self._parse_json_content_loose(content)
#         normalized = self._coerce_parsed_envelope(parsed) if parsed else None

#         if not normalized:
#             # Last-ditch: attempt to coerce by extracting inner braces
#             rescued = self._parse_json_content(content)
#             normalized = self._coerce_parsed_envelope(rescued) if rescued else None

#         if not normalized:
#             return {
#                 "ok": True,
#                 "language": language,
#                 "filename": filename,
#                 "summary": "Fallback used",
#                 "issues": ["Invalid JSON from model"],
#                 "refactored_code": content,
#             }

#         issues = self._normalize_issues(normalized.get("issues", []))
#         return {
#             "ok": True,
#             "language": language,
#             "filename": filename,
#             "summary": normalized.get("summary", ""),
#             "issues": issues,
#             "refactored_code": normalized.get("refactored_code", code) or code,
#         }

#     # =========================
#     # CHUNKING
#     # =========================
#     def _refactor_chunked(self, code, filename, analysis, language):
#         current_chunk_size = min(self.chunk_size_chars, self.max_input_chars)
#         last_result = None

#         for attempt in range(self.max_retries + 1):
#             chunks = self._split_code_chunks(code, max_chars=current_chunk_size)
#             if len(chunks) <= 1:
#                 return self._refactor_single(code, filename, analysis, language)

#             if len(chunks) > self.max_chunks:
#                 if attempt < self.max_retries and current_chunk_size < self.max_input_chars:
#                     current_chunk_size = min(
#                         self.max_input_chars, int(current_chunk_size * 1.5)
#                     )
#                     continue

#                 return {
#                     "ok": False,
#                     "language": language,
#                     "filename": filename,
#                     "error": f"Too many chunks ({len(chunks)}) exceeded LLM_CHUNK_MAX_CHUNKS={self.max_chunks}.",
#                     "summary": "Unable to refactor because split result is too many chunks.",
#                     "issues": [],
#                     "refactored_code": code,
#                 }

#             final_code = ""
#             issues: list[str] = []
#             successful_chunks = 0
#             chunk_too_large = False
#             rate_limited = False

#             for idx, chunk in enumerate(chunks, start=1):
#                 chunk_name = f"{filename} (chunk {idx}/{len(chunks)})"
#                 result = self._refactor_single(chunk, chunk_name, analysis, language)

#                 size_error_indicators = [
#                     "payload too large",
#                     "413",
#                     "request entity too large",
#                     "context length",
#                     "max_tokens",
#                     "input was truncated",
#                     "finish_reason=length",
#                 ]

#                 if result.get("ok"):
#                     successful_chunks += 1
#                     final_code += result.get("refactored_code", chunk)
#                     issues.extend(result.get("issues", []))
#                 else:
#                     final_code += chunk
#                     errors = str(result.get("error", "unknown") or "").lower()
#                     issues.append(
#                         f"Chunk {idx}/{len(chunks)} failed: {result.get('error', 'unknown')}"
#                     )
#                     if "429" in errors or "too many requests" in errors:
#                         rate_limited = True
#                     if any(indicator in errors for indicator in size_error_indicators):
#                         chunk_too_large = True

#             if chunk_too_large and attempt < self.max_retries:
#                 current_chunk_size = max(
#                     1, int(current_chunk_size * self.chunk_shrink_factor)
#                 )
#                 continue

#             if rate_limited and attempt < self.max_retries:
#                 # Respect retry_backoff_base to avoid hammering provider.
#                 sleep_for = self.retry_backoff_base * (attempt + 1) + random.uniform(
#                     0, self.request_retry_backoff
#                 )
#                 time.sleep(max(sleep_for, 0))
#                 continue

#             summary = (
#                 f"Refactored in {len(chunks)} chunks ({successful_chunks} successful). "
#                 + (
#                     "Some chunks failed."
#                     if successful_chunks < len(chunks)
#                     else "Refactor completed in chunks."
#                 )
#             )

#             last_result = {
#                 "ok": successful_chunks == len(chunks),
#                 "language": language,
#                 "filename": filename,
#                 "error": None
#                 if successful_chunks == len(chunks)
#                 else "Partial success: some chunk requests failed.",
#                 "summary": summary,
#                 "issues": list(dict.fromkeys(issues)),
#                 "refactored_code": final_code,
#             }

#             break

#         return last_result or {
#             "ok": False,
#             "language": language,
#             "filename": filename,
#             "error": "Partial success: some chunk requests failed.",
#             "summary": "Unable to refactor due to repeated chunk size/timeouts.",
#             "issues": [],
#             "refactored_code": code,
#         }

#     def _split_code_chunks(self, code: str, max_chars: int | None = None) -> list[str]:
#         effective_max = int(max_chars) if max_chars is not None else self.chunk_size_chars
#         max_chars = max(1, min(effective_max, self.max_input_chars))
#         lines = code.splitlines(keepends=True)
#         chunks: list[str] = []
#         current = ""

#         for line in lines:
#             if len(current) + len(line) <= max_chars:
#                 current += line
#                 continue

#             if current:
#                 chunks.append(current)
#                 current = ""

#             if len(line) > max_chars:
#                 start = 0
#                 while start < len(line):
#                     chunks.append(line[start : start + max_chars])
#                     start += max_chars
#             else:
#                 current = line

#         if current:
#             chunks.append(current)

#         return chunks

#     # =========================
#     # JSON helpers
#     # =========================
#     @staticmethod
#     def _parse_json_content(text: str):
#         cleaned = text.strip()
#         if cleaned.startswith("```"):
#             cleaned = cleaned.strip("`")
#         try:
#             return json.loads(cleaned)
#         except Exception:
#             pass

#         try:
#             start = cleaned.find("{")
#             end = cleaned.rfind("}")
#             if start != -1 and end != -1:
#                 return json.loads(cleaned[start : end + 1])
#         except Exception:
#             return None

#     @staticmethod
#     def _parse_json_content_loose(text: str):
#         try:
#             start = text.find("{")
#             end = text.rfind("}")
#             if start != -1 and end != -1:
#                 return json.loads(text[start : end + 1])
#         except Exception:
#             return None

#     @staticmethod
#     def _coerce_parsed_envelope(parsed: Any) -> dict | None:
#         if not isinstance(parsed, dict):
#             return None

#         summary = parsed.get("summary", "")
#         issues = parsed.get("issues", []) or []
#         refactored_code = parsed.get("refactored_code", "")

#         if isinstance(refactored_code, str):
#             # Unwrap inner JSON string if present.
#             try:
#                 inner = json.loads(refactored_code)
#                 if isinstance(inner, dict):
#                     refactored_code = inner.get("refactored_code", refactored_code)
#             except Exception:
#                 pass
#             refactored_code = refactored_code.replace("\\n", "\n")

#         return {
#             "summary": summary,
#             "issues": issues,
#             "refactored_code": refactored_code,
#         }

#     def _parse_json(self, text: str):
#         # Backwards-compatible alias used by legacy paths.
#         return self._parse_json_content(text) or self._parse_json_content_loose(text)

#     @staticmethod
#     def _normalize_issues(issues: list[Any]) -> list[str]:
#         out: list[str] = []
#         for item in issues or []:
#             if item is None:
#                 continue
#             try:
#                 out.append(str(item))
#             except Exception:
#                 out.append(repr(item))
#         return out

#     # =========================
#     # ERROR helper
#     # =========================
#     def _error(self, language, filename, error, code):
#         return {
#             "ok": False,
#             "language": language,
#             "filename": filename,
#             "error": error,
#             "summary": "LLM failed",
#             "issues": [],
#             "refactored_code": code,
#         }


import json
import os
import time
import requests

from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.refractor.base_refractor import BaseRefractor
from backend.ai_agents.rag.rag_pipeline import RAGPipeline


class LLMRefractorAgent(BaseRefractor):

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "llama3-8b-8192").strip()
        self.base_url = os.getenv(
            "LLM_BASE_URL", "https://api.groq.com/openai/v1"
        ).strip().rstrip("/")

        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1500"))

        self.max_retries = 3

    # =========================
    # ENTRY POINT
    # =========================
    def refactor(self, code: str, filename: str, analysis: dict | None = None) -> dict:
        language = detect_language(filename)

        if not self.api_key:
            return self._fallback(language, filename, code, "Missing API key")

        if len(code) > 8000:
            return self._fallback(language, filename, code, "File too large")

        try:
            return self._refactor_single(code, filename, analysis, language)
        except Exception as e:
            return self._fallback(language, filename, code, str(e))

    # =========================
    # SAFE API REQUEST
    # =========================
    def _make_request(self, messages):

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
                    print("⚠️ Rate limited, retrying...")
                    time.sleep(2 * (attempt + 1))
                    continue

                if response.status_code != 200:
                    print("❌ LLM ERROR:", response.status_code, response.text)
                    return None

                return response

            except Exception as e:
                print("❌ Request error:", e)
                time.sleep(2)

        return None

    # =========================
    # MAIN REFACTOR LOGIC
    # =========================
    def _refactor_single(self, code, filename, analysis, language):

        # 🔥 RAG (focus only relevant code)
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
            "{ \"summary\": string, \"issues\": [], \"refactored_code\": string }"
        )

        user_prompt = (
            f"Filename: {filename}\n"
            f"Language: {language}\n\n"
            f"Analysis:\n{json.dumps(analysis or {})}\n\n"
            f"Code:\n{focus_code}"
        )

        response = self._make_request([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        if response is None:
            return self._fallback(language, filename, code, "LLM unavailable")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except Exception:
            return self._fallback(language, filename, code, "Invalid response")

        parsed = self._parse_json(content)

        if not parsed:
            return self._fallback(language, filename, code, "Parsing failed")

        return {
            "ok": True,
            "language": language,
            "filename": filename,
            "summary": parsed.get("summary") or "No summary",
            "issues": self._normalize_issues(parsed.get("issues")),
            "refactored_code": parsed.get("refactored_code") or code,
        }

    # =========================
    # JSON PARSER
    # =========================
    def _parse_json(self, text: str):
        try:
            return json.loads(text)
        except:
            try:
                start = text.find("{")
                end = text.rfind("}")
                return json.loads(text[start:end + 1])
            except:
                return None

    # =========================
    # 🔥 ISSUE NORMALIZER (FIX)
    # =========================
    def _normalize_issues(self, issues):
        clean = []
        for i in issues or []:
            if isinstance(i, dict):
                clean.append(i.get("description") or i.get("type") or str(i))
            else:
                clean.append(str(i))
        return clean

    # =========================
    # 🔥 FALLBACK (NEVER FAIL)
    # =========================
    def _fallback(self, language, filename, code, reason):
        return {
            "ok": True,  # ✅ UI SAFE
            "fallback": True,
            "reason": reason,
            "language": language,
            "filename": filename,
            "summary": f"Fallback used: {reason}",
            "issues": [],
            "refactored_code": code,  # ✅ NEVER NONE
        }