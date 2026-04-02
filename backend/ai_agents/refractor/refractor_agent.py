# # import ast
# # import json
# # import os
# # import re
# # import time
# # from typing import Any

# # import requests

# # from backend.ai_agents.core.language_detector import detect_language
# # from backend.ai_agents.refractor.base_refractor import BaseRefractor


# # class LLMRefractorAgent(BaseRefractor):
# #     def __init__(self):
# #         self.api_key = os.getenv("LLM_API_KEY", "").strip()
# #         self.model = os.getenv("LLM_MODEL", "gpt-4.1-mini").strip()
# #         self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
# #         self.is_gemini = "gemini.googleapis.com" in self.base_url or "gemini" in self.model.lower()

# #         if self.is_gemini:
# #             # Gemini uses the generativelanguage API endpoint and supports API key auth.
# #             if "gemini.googleapis.com" in self.base_url:
# #                 self.base_url = self.base_url.replace("gemini.googleapis.com", "generativelanguage.googleapis.com")
# #             if "generativelanguage.googleapis.com" not in self.base_url:
# #                 self.base_url = "https://generativelanguage.googleapis.com"

# #         self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
# #         self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096"))
# #         self.max_input_chars = int(os.getenv("LLM_MAX_INPUT_CHARS", "5000"))
# #         self.max_analysis_chars = int(os.getenv("LLM_MAX_ANALYSIS_CHARS", "3000"))
# #         self.chunk_enabled = os.getenv("LLM_CHUNK_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
# #         self.chunk_size_chars = int(os.getenv("LLM_CHUNK_SIZE_CHARS", str(self.max_input_chars)))
# #         self.chunk_shrink_factor = float(os.getenv("LLM_CHUNK_SHRINK_FACTOR", "0.75"))
# #         self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
# #         self.retry_backoff_base = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "1.0"))
# #         self.max_chunks = int(os.getenv("LLM_CHUNK_MAX_CHUNKS", "50"))
# #         self.truncate_input = os.getenv("LLM_TRUNCATE_INPUT", "1").strip().lower() not in {
# #             "0",
# #             "false",
# #             "no",
# #         }
# #         self.enforce_json_response = os.getenv("LLM_ENFORCE_JSON_RESPONSE", "1").strip().lower() not in {
# #             "0",
# #             "false",
# #             "no",
# #         }

# #     def refactor(self, code: str, filename: str, analysis: dict | None = None) -> dict:
# #         language = detect_language(filename)

# #         if not self.api_key:
# #             return {
# #                 "ok": False,
# #                 "language": language,
# #                 "filename": filename,
# #                 "error": "LLM_API_KEY is not configured",
# #                 "summary": "LLM refactor is disabled because no API key was provided.",
# #                 "issues": [],
# #                 "refactored_code": code,
# #             }

# #         if self.chunk_enabled and len(code) > self.max_input_chars:
# #             return self._refactor_chunked(code, filename, analysis, language)

# #         return self._refactor_single(code, filename, analysis, language)

# #     def _refactor_chunked(self, code: str, filename: str, analysis: dict | None, language: str) -> dict:
# #         current_chunk_size = min(self.chunk_size_chars, self.max_input_chars)
# #         last_result = None

# #         for attempt in range(self.max_retries + 1):
# #             chunks = self._split_code_chunks(code, max_chars=current_chunk_size)
# #             if len(chunks) <= 1:
# #                 return self._refactor_single(code, filename, analysis, language)

# #             if len(chunks) > self.max_chunks:
# #                 if attempt < self.max_retries and current_chunk_size < self.max_input_chars:
# #                     current_chunk_size = min(self.max_input_chars, int(current_chunk_size * 1.5))
# #                     continue

# #                 return {
# #                     "ok": False,
# #                     "language": language,
# #                     "filename": filename,
# #                     "error": f"Too many chunks ({len(chunks)}) exceeded LLM_CHUNK_MAX_CHUNKS={self.max_chunks}.",
# #                     "summary": "Unable to refactor because split result is too many chunks.",
# #                     "issues": [],
# #                     "refactored_code": code,
# #                 }

# #             final_code = ""
# #             issues: list[str] = []
# #             successful_chunks = 0
# #             chunk_too_large = False

# #             for idx, chunk in enumerate(chunks, start=1):
# #                 chunk_name = f"{filename} (chunk {idx}/{len(chunks)})"
# #                 result = self._refactor_single(chunk, chunk_name, analysis, language)

# #                 size_error_indicators = [
# #                     "Payload Too Large",
# #                     "413",
# #                     "Request entity too large",
# #                     "context length",
# #                     "max_tokens",
# #                     "input was truncated",
# #                     "finish_reason=length",
# #                 ]

# #                 if result.get("ok"):
# #                     successful_chunks += 1
# #                     final_code += result.get("refactored_code", chunk)
# #                     issues.extend(result.get("issues", []))
# #                 else:
# #                     final_code += chunk
# #                     errors = str(result.get("error", "unknown") or "").lower()
# #                     issues.append(f"Chunk {idx}/{len(chunks)} failed: {result.get('error', 'unknown')}")
# #                     if any(indicator.lower() in errors for indicator in size_error_indicators):
# #                         chunk_too_large = True

# #             if chunk_too_large and attempt < self.max_retries:
# #                 current_chunk_size = max(1000, int(current_chunk_size * self.chunk_shrink_factor))
# #                 continue

# #             summary = (
# #                 f"Refactored in {len(chunks)} chunks ({successful_chunks} successful). "
# #                 + ("Some chunks failed." if successful_chunks < len(chunks) else "Refactor completed in chunks.")
# #             )

# #             last_result = {
# #                 "ok": successful_chunks == len(chunks),
# #                 "language": language,
# #                 "filename": filename,
# #                 "error": None if successful_chunks == len(chunks) else "Partial success: some chunk requests failed.",
# #                 "summary": summary,
# #                 "issues": list(dict.fromkeys(issues)),
# #                 "refactored_code": final_code,
# #             }

# #             break

# #         return last_result or {
# #             "ok": False,
# #             "language": language,
# #             "filename": filename,
# #             "error": "Partial success: some chunk requests failed.",
# #             "summary": "Unable to refactor due to repeated chunk size/timeouts.",
# #             "issues": [],
# #             "refactored_code": code,
# #         }

# #     def _split_code_chunks(self, code: str, max_chars: int | None = None) -> list[str]:
# #         effective_max = int(max_chars) if max_chars is not None else self.chunk_size_chars
# #         max_chars = max(1000, min(effective_max, self.max_input_chars))
# #         lines = code.splitlines(keepends=True)
# #         chunks: list[str] = []
# #         current = ""

# #         for line in lines:
# #             if len(current) + len(line) <= max_chars:
# #                 current += line
# #                 continue

# #             if current:
# #                 chunks.append(current)
# #                 current = ""

# #             if len(line) > max_chars:
# #                 start = 0
# #                 while start < len(line):
# #                     chunks.append(line[start : start + max_chars])
# #                     start += max_chars
# #             else:
# #                 current = line

# #         if current:
# #             chunks.append(current)

# #         return chunks

# #     def _make_request(self, payload: dict[str, Any]) -> requests.Response:
# #         attempt = 0

# #         if self.is_gemini:
# #             # Try possible Gemini endpoints and latest Generative Language APIs.
# #             endpoints = []

# #             # Configured base URL already normalized in __init__
# #             endpoints.append(f"{self.base_url.rstrip('/')}/v1/models/{self.model}:generate?key={self.api_key}")
# #             endpoints.append(f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generate?key={self.api_key}")
# #             endpoints.append(f"https://generativelanguage.googleapis.com/v1beta2/models/{self.model}:generate?key={self.api_key}")
# #             endpoints.append(f"https://gemini.googleapis.com/v1/models/{self.model}:generate?key={self.api_key}")
# #         else:
# #             endpoints = [f"{self.base_url}/chat/completions"]

# #         headers = {"Content-Type": "application/json"}
# #         if not self.is_gemini:
# #             headers["Authorization"] = f"Bearer {self.api_key}"

# #         last_exc = None

# #         for endpoint in endpoints:
# #             attempt = 0
# #             while True:
# #                 attempt += 1
# #                 try:
# #                     response = requests.post(
# #                         endpoint,
# #                         headers=headers,
# #                         json=payload,
# #                         timeout=self.timeout_seconds,
# #                     )
# #                     response.raise_for_status()
# #                     return response
# #                 except requests.HTTPError as exc:
# #                     status_code = exc.response.status_code if exc.response is not None else None
# #                     if status_code == 404 and self.is_gemini:
# #                         last_exc = requests.HTTPError(
# #                             f"Gemini API endpoint not found (404) for URL: {endpoint}."
# #                             " Please verify LLM_BASE_URL, LLM_MODEL, and API access.",
# #                             response=exc.response,
# #                         )
# #                         break
# #                     if status_code in {429, 500, 502, 503, 504} and attempt <= self.max_retries:
# #                         wait_seconds = self.retry_backoff_base * (2 ** (attempt - 1))
# #                         time.sleep(wait_seconds)
# #                         continue
# #                     raise
# #                 except (requests.Timeout, requests.ConnectionError) as exc:
# #                     if attempt <= self.max_retries:
# #                         wait_seconds = self.retry_backoff_base * (2 ** (attempt - 1))
# #                         time.sleep(wait_seconds)
# #                         continue
# #                     last_exc = exc
# #                     break

# #             # If we reach here, this endpoint couldn't be used; proceed to next.
# #             continue

# #         if last_exc:
# #             raise last_exc

# #         raise RuntimeError("LLM request failed: no available endpoints")

# #     def _refactor_single(self, code: str, filename: str, analysis: dict | None, language: str) -> dict:
# #         system_prompt = self._build_system_prompt(language)
# #         analysis_text = json.dumps(analysis, ensure_ascii=False) if analysis else "{}"

# #         analysis_to_send = analysis_text
# #         analysis_truncated = False
# #         if self.truncate_input and len(analysis_to_send) > self.max_analysis_chars:
# #             analysis_to_send = analysis_to_send[: self.max_analysis_chars] + "..."
# #             analysis_truncated = True

# #         code_to_send = code
# #         truncation_note = ""

# #         if self.truncate_input and len(code_to_send) > self.max_input_chars:
# #             code_to_send = code_to_send[: self.max_input_chars]
# #             truncation_note = (
# #                 "\n\n" "NOTE: Input code was truncated to the first "
# #                 f"{self.max_input_chars} characters to avoid payload size limits."
# #             )

# #         if analysis_truncated:
# #             truncation_note += "\n\nNOTE: Static analysis data was truncated to avoid payload size limits."

# #         user_prompt = (
# #             f"Filename: {filename}\n"
# #             f"Detected language: {language}\n"
# #             f"Existing static analysis: {analysis_to_send}\n\n"
# #             "Task:\n"
# #             "1) Identify key readability/standard-style issues.\n"
# #             "2) Refactor the code into a human-readable standard form.\n"
# #             "3) Preserve behavior as much as possible.\n"
# #             "4) Keep the response strictly valid JSON.\n\n"
# #             "Code:\n"
# #             f"{code_to_send}{truncation_note}"
# #         )

# #         if self.is_gemini:
# #             payload = {
# #                 "temperature": 0,
# #                 "max_output_tokens": self.max_output_tokens,
# #                 "prompt": {
# #                     "messages": [
# #                         {"author": "user", "content": {"text": user_prompt}}
# #                     ]
# #                 },
# #             }
# #         else:
# #             payload = {
# #                 "model": self.model,
# #                 "temperature": 0,
# #                 "max_tokens": self.max_output_tokens,
# #                 "messages": [
# #                     {"role": "system", "content": system_prompt},
# #                     {"role": "user", "content": user_prompt},
# #                 ],
# #             }
# #             if self.enforce_json_response:
# #                 payload["response_format"] = {"type": "json_object"}

# #         try:
# #             response = self._make_request(payload)
# #         except requests.HTTPError as exc:
# #             status_code = exc.response.status_code if exc.response is not None else None
# #             if status_code == 413:
# #                 return {
# #                     "ok": False,
# #                     "language": language,
# #                     "filename": filename,
# #                     "error": "LLM request failed: Payload Too Large (413)",
# #                     "summary": "Input code is too large for the LLM endpoint. Reduce file size or set a lower LLM_MAX_INPUT_CHARS.",
# #                     "issues": [],
# #                     "refactored_code": code,
# #                 }
# #             if "response_format" in payload and status_code in {400, 422}:
# #                 payload.pop("response_format", None)
# #                 try:
# #                     response = self._make_request(payload)
# #                 except Exception as retry_exc:
# #                     return {
# #                         "ok": False,
# #                         "language": language,
# #                         "filename": filename,
# #                         "error": f"LLM request failed: {retry_exc}",
# #                         "summary": "Failed to call LLM service.",
# #                         "issues": [],
# #                         "refactored_code": code,
# #                     }
# #             else:
# #                 return {
# #                     "ok": False,
# #                     "language": language,
# #                     "filename": filename,
# #                     "error": f"LLM request failed: {exc}",
# #                     "summary": "Failed to call LLM service.",
# #                     "issues": [],
# #                     "refactored_code": code,
# #                 }
# #         except Exception as exc:
# #             return {
# #                 "ok": False,
# #                 "language": language,
# #                 "filename": filename,
# #                 "error": f"LLM request failed: {exc}",
# #                 "summary": "Failed to call LLM service.",
# #                 "issues": [],
# #                 "refactored_code": code,
# #             }

# #         try:
# #             data = response.json()
# #             if "choices" in data and data["choices"]:
# #                 content = data["choices"][0]["message"]["content"]
# #                 finish_reason = data["choices"][0].get("finish_reason")
# #             elif "candidates" in data and data["candidates"]:
# #                 candidate_content = data["candidates"][0].get("content", {})
# #                 content = candidate_content.get("text") or ""
# #                 finish_reason = data.get("metadata", {}).get("finish_reason")
# #             else:
# #                 return {
# #                     "ok": False,
# #                     "language": language,
# #                     "filename": filename,
# #                     "error": "Unexpected LLM response format",
# #                     "summary": "LLM responded with an unexpected format.",
# #                     "issues": [],
# #                     "refactored_code": code,
# #                 }
# #         except Exception:
# #             return {
# #                 "ok": False,
# #                 "language": language,
# #                 "filename": filename,
# #                 "error": "Unexpected LLM response format",
# #                 "summary": "LLM responded with an unexpected format.",
# #                 "issues": [],
# #                 "refactored_code": code,
# #             }

# #         if finish_reason == "length":
# #             return {
# #                 "ok": False,
# #                 "language": language,
# #                 "filename": filename,
# #                 "error": "LLM output was truncated due to token limit (finish_reason=length)",
# #                 "summary": "LLM output was truncated. Increase LLM_MAX_OUTPUT_TOKENS or use a smaller input.",
# #                 "issues": [],
# #                 "refactored_code": code,
# #                 "raw_output": content,
# #             }

# #         parsed = self._parse_json_content(content)
# #         if not parsed:
# #             parsed = self._parse_json_content_loose(content)

# #         if not parsed:
# #             pseudo = self._extract_fields_from_pseudo_json(content)
# #             if pseudo:
# #                 issues = pseudo.get("issues", [])
# #                 if not isinstance(issues, list):
# #                     issues = [str(issues)]
# #                 normalized_code, normalization_issue = self._normalize_refactored_code(
# #                     code=str(pseudo.get("refactored_code", code)),
# #                     language=language,
# #                 )
# #                 if normalization_issue:
# #                     issues.append(normalization_issue)
# #                 issues.append("LLM response did not follow required JSON envelope; used heuristic field extraction.")
# #                 return {
# #                     "ok": True,
# #                     "language": language,
# #                     "filename": filename,
# #                     "error": None,
# #                     "summary": str(pseudo.get("summary", "")).strip() or "Used heuristic fallback parser.",
# #                     "issues": [str(item) for item in issues],
# #                     "refactored_code": normalized_code,
# #                     "raw_output": content,
# #                 }

# #             fallback_code = self._extract_code_from_text(content)
# #             normalized_code, normalization_issue = self._normalize_refactored_code(
# #                 code=fallback_code,
# #                 language=language,
# #             )
# #             issues = []
# #             if normalization_issue:
# #                 issues.append(normalization_issue)
# #             issues.append("LLM response did not follow required JSON envelope; used fallback parsing.")
# #             return {
# #                 "ok": True,
# #                 "language": language,
# #                 "filename": filename,
# #                 "error": None,
# #                 "summary": "Used fallback parser because model returned non-JSON envelope.",
# #                 "issues": issues,
# #                 "refactored_code": normalized_code,
# #                 "raw_output": content,
# #             }

# #         parsed = self._coerce_parsed_envelope(parsed)

# #         issues = parsed.get("issues", [])
# #         if not isinstance(issues, list):
# #             issues = [str(issues)]

# #         normalized_code, normalization_issue = self._normalize_refactored_code(
# #             code=str(parsed.get("refactored_code", code)),
# #             language=language,
# #         )
# #         if normalization_issue:
# #             issues.append(normalization_issue)

# #         return {
# #             "ok": True,
# #             "language": language,
# #             "filename": filename,
# #             "error": None,
# #             "summary": str(parsed.get("summary", "")).strip(),
# #             "issues": [str(item) for item in issues],
# #             "refactored_code": normalized_code,
# #         }

# #     @staticmethod
# #     def _build_system_prompt(language: str) -> str:
# #         base = (
# #             "Refactor code for readability and maintainability while preserving behavior. "
# #             "Return valid JSON only (no prose, no markdown) with keys: "
# #             "summary (string), issues (array of strings), refactored_code (string). "
# #         )

# #         if language == "json":
# #             return (
# #                 base
# #                 + "The refactored_code must be STRICT valid JSON text with double quotes, lowercase true/false/null, "
# #                 + "and no trailing commas. Never return Python dict syntax."
# #             )

# #         return base + "The refactored_code must be valid in its original language."

# #     @staticmethod
# #     def _normalize_refactored_code(code: str, language: str) -> tuple[str, str | None]:
# #         if language != "json":
# #             return code, None

# #         # If already valid JSON, normalize formatting.
# #         try:
# #             payload = json.loads(code)
# #             return json.dumps(payload, indent=2, ensure_ascii=False), None
# #         except Exception:
# #             pass

# #         # Recover from Python-dict style output when possible.
# #         try:
# #             payload = ast.literal_eval(code)
# #             return json.dumps(payload, indent=2, ensure_ascii=False), (
# #                 "LLM returned non-JSON syntax; converted to valid JSON format automatically."
# #             )
# #         except Exception:
# #             return code, "LLM returned invalid JSON syntax and auto-normalization failed."

# #     @staticmethod
# #     def _extract_code_from_text(content: str) -> str:
# #         text = (content or "").strip()
# #         if not text:
# #             return ""

# #         # Prefer fenced code body if present.
# #         if "```" in text:
# #             parts = text.split("```")
# #             if len(parts) >= 3:
# #                 candidate = parts[1]
# #                 lines = candidate.splitlines()
# #                 if lines and lines[0].strip().lower() in {
# #                     "json", "javascript", "typescript", "python", "java", "go", "c", "cpp", "csharp", "php", "rust"
# #                 }:
# #                     return "\n".join(lines[1:]).strip()
# #                 return candidate.strip()

# #         return text

# #     @staticmethod
# #     def _coerce_parsed_envelope(data: dict[str, Any]) -> dict[str, Any]:
# #         """
# #         Normalize parsed payload and unwrap nested envelope when models return
# #         `refactored_code` as an embedded JSON object string.
# #         """
# #         result = dict(data)
# #         nested = result.get("refactored_code")
# #         if isinstance(nested, str):
# #             nested_parsed = LLMRefractorAgent._parse_json_content(nested) or LLMRefractorAgent._parse_json_content_loose(nested)
# #             if not nested_parsed:
# #                 nested_parsed = LLMRefractorAgent._extract_fields_from_pseudo_json(nested)
# #             if isinstance(nested_parsed, dict) and "refactored_code" in nested_parsed:
# #                 if "summary" not in result and "summary" in nested_parsed:
# #                     result["summary"] = nested_parsed["summary"]
# #                 if "issues" not in result and "issues" in nested_parsed:
# #                     result["issues"] = nested_parsed["issues"]
# #                 result["refactored_code"] = nested_parsed["refactored_code"]
# #         return result

# #     @staticmethod
# #     def _parse_json_content(content: str) -> dict[str, Any] | None:
# #         content = content.strip()

# #         try:
# #             data = json.loads(content)
# #             if isinstance(data, dict):
# #                 return data
# #         except Exception:
# #             pass

# #         start = content.find("{")
# #         end = content.rfind("}")
# #         if start == -1 or end == -1 or end <= start:
# #             return None

# #         snippet = content[start : end + 1]
# #         try:
# #             data = json.loads(snippet)
# #             if isinstance(data, dict):
# #                 return data
# #         except Exception:
# #             return None

# #         return None

# #     @staticmethod
# #     def _parse_json_content_loose(content: str) -> dict[str, Any] | None:
# #         """
# #         Best-effort parser for near-JSON payloads (e.g., Python dict style,
# #         single quotes, wrapper prose around an object).
# #         """
# #         text = (content or "").strip()
# #         if not text:
# #             return None

# #         if text.startswith("```") and text.endswith("```"):
# #             parts = text.split("```")
# #             if len(parts) >= 3:
# #                 text = parts[1].strip()
# #                 lines = text.splitlines()
# #                 if lines and lines[0].strip().lower() in {
# #                     "json", "javascript", "typescript", "python", "java", "go", "c", "cpp", "csharp", "php", "rust"
# #                 }:
# #                     text = "\n".join(lines[1:]).strip()

# #         candidates = [text]
# #         start = text.find("{")
# #         end = text.rfind("}")
# #         if start != -1 and end != -1 and end > start:
# #             candidates.append(text[start : end + 1])

# #         for candidate in candidates:
# #             try:
# #                 maybe = ast.literal_eval(candidate)
# #                 if isinstance(maybe, dict):
# #                     return maybe
# #             except Exception:
# #                 continue

# #         return None

# #     @staticmethod
# #     def _extract_fields_from_pseudo_json(content: str) -> dict[str, Any] | None:
# #         """
# #         Heuristic extractor for malformed JSON-like payloads where strict/loose
# #         parsing fails but field labels are still present.
# #         """
# #         text = (content or "").strip()
# #         if not text:
# #             return None
# #         text = LLMRefractorAgent._strip_markdown_fences(text)

# #         if '"refactored_code"' not in text:
# #             return None

# #         summary = ""
# #         summary_match = re.search(r'"summary"\s*:\s*"([^"]*)"', text, re.DOTALL)
# #         if summary_match:
# #             summary = summary_match.group(1).strip()

# #         issues: list[str] = []
# #         issues_block = re.search(r'"issues"\s*:\s*\[(.*?)\]', text, re.DOTALL)
# #         if issues_block:
# #             issues = [
# #                 item.strip()
# #                 for item in re.findall(r'"([^"]*)"', issues_block.group(1), re.DOTALL)
# #                 if item.strip()
# #             ]

# #         code_match = re.search(r'"refactored_code"\s*:\s*"(.*)"\s*(?:,|\})', text, re.DOTALL)
# #         if not code_match:
# #             return None

# #         raw_code = code_match.group(1).strip()
# #         if raw_code.endswith('",'):
# #             raw_code = raw_code[:-2]
# #         elif raw_code.endswith('"'):
# #             raw_code = raw_code[:-1]

# #         # Best-effort unescape to convert \" and \n to readable code.
# #         try:
# #             unescaped = bytes(raw_code, "utf-8").decode("unicode_escape")
# #         except Exception:
# #             unescaped = raw_code

# #         unescaped = unescaped.strip()
# #         if not unescaped:
# #             return None

# #         return {
# #             "summary": summary,
# #             "issues": issues,
# #             "refactored_code": unescaped,
# #         }

# #     @staticmethod
# #     def _strip_markdown_fences(text: str) -> str:
# #         if text.startswith("```") and text.endswith("```"):
# #             parts = text.split("```")
# #             if len(parts) >= 3:
# #                 body = parts[1].strip()
# #                 lines = body.splitlines()
# #                 if lines and lines[0].strip().lower() in {
# #                     "json", "javascript", "typescript", "python", "java", "go", "c", "cpp", "csharp", "php", "rust"
# #                 }:
# #                     return "\n".join(lines[1:]).strip()
# #                 return body
# #         return text


# import ast
# import json
# import os
# import re
# import time
# from typing import Any

# import requests

# from backend.ai_agents.core.language_detector import detect_language
# from backend.ai_agents.refractor.base_refractor import BaseRefractor


# class LLMRefractorAgent(BaseRefractor):
#     def __init__(self):
#         self.api_key = os.getenv("LLM_API_KEY", "").strip()
#         self.model = os.getenv("LLM_MODEL", "text-bison-001").strip()
#         self.base_url = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/")

#         self.is_gemini = "gemini" in self.model.lower() or "generativelanguage" in self.base_url

#         self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
#         self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096"))
#         self.max_input_chars = int(os.getenv("LLM_MAX_INPUT_CHARS", "5000"))
#         self.max_analysis_chars = int(os.getenv("LLM_MAX_ANALYSIS_CHARS", "3000"))

#         # fallback model order for Gemini-compatible keys
#         configured = [self.model]
#         env_models = os.getenv("LLM_MODEL_CANDIDATES", "text-bison-001,chat-bison-001,gemini-1.5-pro,gemini-1.0")
#         candidate_models = [x.strip() for x in env_models.split(",") if x.strip()]
#         self.model_candidates = list(dict.fromkeys(configured + candidate_models))

#     def refactor(self, code: str, filename: str, analysis: dict | None = None) -> dict:
#         language = detect_language(filename)

#         if not self.api_key:
#             return {
#                 "ok": False,
#                 "language": language,
#                 "filename": filename,
#                 "error": "LLM_API_KEY is not configured",
#                 "summary": "LLM refactor is disabled.",
#                 "issues": [],
#                 "refactored_code": code,
#             }

#         return self._refactor_single(code, filename, analysis, language)

#     # =========================
#     # 🔥 GEMINI REQUEST
#     # =========================
#     def _make_request(self, payload: dict[str, Any]) -> requests.Response:
#         # Try all candidate endpoints and models for Gemini compatibility.
#         endpoints: list[str] = []

#         if self.is_gemini:
#             for candidate_model in self.model_candidates:
#                 endpoints.extend(
#                     [
#                         f"{self.base_url}/v1/models/{candidate_model}:generateContent?key={self.api_key}",
#                         f"{self.base_url}/v1/models/{candidate_model}:generate?key={self.api_key}",
#                         f"{self.base_url}/v1beta2/models/{candidate_model}:generate?key={self.api_key}",
#                         f"https://generativelanguage.googleapis.com/v1/models/{candidate_model}:generate?key={self.api_key}",
#                         f"https://generativelanguage.googleapis.com/v1beta2/models/{candidate_model}:generate?key={self.api_key}",
#                     ]
#                 )
#         else:
#             endpoints.append(f"{self.base_url}/chat/completions")

#         headers = {"Content-Type": "application/json"}
#         if not self.is_gemini:
#             headers["Authorization"] = f"Bearer {self.api_key}"

#         last_exception = None

#         for endpoint in endpoints:
#             retries = 0
#             while retries <= 3:
#                 try:
#                     response = requests.post(
#                         endpoint,
#                         headers=headers,
#                         json=payload,
#                         timeout=self.timeout_seconds,
#                     )
#                     response.raise_for_status()
#                     return response
#                 except requests.HTTPError as exc:
#                     status_code = exc.response.status_code if exc.response is not None else None
#                     if status_code == 404 and self.is_gemini:
#                         last_exception = exc
#                         break  # try next endpoint/model
#                     if status_code in {429, 500, 502, 503, 504}:
#                         retries += 1
#                         time.sleep(self.retry_backoff_base * (2 ** (retries - 1)))
#                         continue
#                     raise
#                 except (requests.Timeout, requests.ConnectionError) as exc:
#                     last_exception = exc
#                     retries += 1
#                     if retries > 3:
#                         break
#                     time.sleep(self.retry_backoff_base * (2 ** (retries - 1)))
#                     continue
#             # move to next endpoint if this one failed
#             continue

#         if last_exception is not None:
#             raise last_exception

#         raise RuntimeError("LLM request failed: no available endpoint succeeded")

#     # =========================
#     # 🔥 MAIN REFACTOR
#     # =========================
#     def _refactor_single(self, code: str, filename: str, analysis: dict | None, language: str) -> dict:
#         system_prompt = self._build_system_prompt(language)
#         analysis_text = json.dumps(analysis, ensure_ascii=False) if analysis else "{}"

#         user_prompt = (
#             f"Filename: {filename}\n"
#             f"Detected language: {language}\n"
#             f"Existing static analysis: {analysis_text}\n\n"
#             "Task:\n"
#             "1) Identify issues\n"
#             "2) Refactor code\n"
#             "3) Preserve logic\n"
#             "4) RETURN JSON ONLY\n\n"
#             f"Code:\n{code}"
#         )

#         # ✅ GEMINI PAYLOAD (CORRECT)
#         payload = {
#             "contents": [
#                 {
#                     "parts": [
#                         {
#                             "text": system_prompt + "\n\n" + user_prompt
#                         }
#                     ]
#                 }
#             ],
#             "generationConfig": {
#                 "temperature": 0,
#                 "maxOutputTokens": self.max_output_tokens,
#             }
#         }

#         try:
#             response = self._make_request(payload)
#             data = response.json()

#             # ✅ CORRECT GEMINI PARSING
#             content = data["candidates"][0]["content"]["parts"][0]["text"]

#         except Exception as exc:
#             return {
#                 "ok": False,
#                 "language": language,
#                 "filename": filename,
#                 "error": f"LLM failed: {exc}",
#                 "summary": "Gemini request failed.",
#                 "issues": [],
#                 "refactored_code": code,
#             }

#         # =========================
#         # JSON PARSING
#         # =========================
#         parsed = self._parse_json(content)

#         if not parsed:
#             return {
#                 "ok": True,
#                 "language": language,
#                 "filename": filename,
#                 "summary": "Used fallback parsing",
#                 "issues": ["Model did not return proper JSON"],
#                 "refactored_code": content,
#             }

#         return {
#             "ok": True,
#             "language": language,
#             "filename": filename,
#             "summary": parsed.get("summary", ""),
#             "issues": parsed.get("issues", []),
#             "refactored_code": parsed.get("refactored_code", code),
#         }

#     # =========================
#     # JSON PARSER
#     # =========================
#     def _parse_json(self, text: str):
#         try:
#             return json.loads(text)
#         except:
#             pass

#         try:
#             start = text.find("{")
#             end = text.rfind("}")
#             return json.loads(text[start:end + 1])
#         except:
#             return None

#     # =========================
#     # PROMPT
#     # =========================
#     def _build_system_prompt(self, language: str) -> str:
#         return (
#             "You are a senior software engineer.\n"
#             "Refactor the code for readability.\n"
#             "STRICTLY return JSON:\n"
#             "{ summary: string, issues: [], refactored_code: string }"
#         )


import ast
import json
import os
import re
import time
from typing import Any

import requests

from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.refractor.base_refractor import BaseRefractor


class LLMRefractorAgent(BaseRefractor):
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "gemini-1.5-flash").strip()
        self.base_url = os.getenv(
            "LLM_BASE_URL",
            "https://generativelanguage.googleapis.com"
        ).strip()

        # If user supplies the full path accidentally, keep only host
        if "/v1" in self.base_url:
            self.base_url = self.base_url.split("/v1")[0]
        self.base_url = self.base_url.rstrip("/")

        # fallback model order
        candidates = [self.model]
        extra = os.getenv("LLM_MODEL_CANDIDATES", "gemini-1.5-flash,gemini-1.0,text-bison-001,chat-bison-001")
        for m in extra.split(","):
            m = m.strip()
            if m and m not in candidates:
                candidates.append(m)
        self.model_candidates = candidates

        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096"))

    # =========================
    # MAIN ENTRY
    # =========================
    def refactor(self, code: str, filename: str, analysis: dict | None = None) -> dict:
        language = detect_language(filename)

        if not self.api_key:
            return {
                "ok": False,
                "language": language,
                "filename": filename,
                "error": "LLM_API_KEY missing",
                "summary": "LLM disabled",
                "issues": [],
                "refactored_code": code,
            }

        return self._refactor_single(code, filename, analysis, language)

    # =========================
    # ✅ FIXED GEMINI REQUEST
    # =========================
    def _make_request(self, payload: dict[str, Any]) -> dict:
        endpoint_templates = []

        if self.base_url.startswith("https://"):
            # Try first with current model and fallback models
            for model in self.model_candidates:
                endpoint_templates.extend(
                    [
                        f"{self.base_url}/v1/models/{model}:generate?key={self.api_key}",
                        f"{self.base_url}/v1/models/{model}:generateContent?key={self.api_key}",
                        f"https://generativelanguage.googleapis.com/v1/models/{model}:generate?key={self.api_key}",
                        f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={self.api_key}",
                    ]
                )
        else:
            raise ValueError("LLM_BASE_URL must start with https://")

        last_exception = None

        for url in endpoint_templates:
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status == 404:
                    last_exception = exc
                    continue
                if status in {429, 500, 502, 503, 504}:
                    time.sleep(1)
                    continue
                raise
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exception = exc
                time.sleep(1)
                continue

        if last_exception is not None:
            raise last_exception

        raise RuntimeError("LLM request failed: no available endpoint succeeded")

    # =========================
    # REFACTOR LOGIC
    # =========================
    def _refactor_single(self, code: str, filename: str, analysis: dict | None, language: str) -> dict:

        system_prompt = (
            "You are a senior software engineer.\n"
            "Refactor code for readability and maintainability.\n"
            "STRICTLY RETURN JSON:\n"
            "{ summary: string, issues: [], refactored_code: string }"
        )

        analysis_text = json.dumps(analysis or {})

        user_prompt = (
            f"Filename: {filename}\n"
            f"Language: {language}\n"
            f"Analysis: {analysis_text}\n\n"
            "Task:\n"
            "1. Identify issues\n"
            "2. Refactor code\n"
            "3. Preserve logic\n"
            "4. RETURN ONLY JSON\n\n"
            f"Code:\n{code}"
        )

        # ✅ CORRECT GEMINI PAYLOAD
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": system_prompt + "\n\n" + user_prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": self.max_output_tokens,
            }
        }

        try:
            data = self._make_request(payload)

            # ✅ CORRECT PARSING
            content = data["candidates"][0]["content"]["parts"][0]["text"]

        except Exception as e:
            return {
                "ok": False,
                "language": language,
                "filename": filename,
                "error": str(e),
                "summary": "Gemini request failed",
                "issues": [],
                "refactored_code": code,
            }

        # =========================
        # JSON PARSING
        # =========================
        parsed = self._parse_json(content)

        if not parsed:
            return {
                "ok": True,
                "language": language,
                "filename": filename,
                "summary": "Fallback used",
                "issues": ["Model did not return JSON"],
                "refactored_code": content,
            }

        return {
            "ok": True,
            "language": language,
            "filename": filename,
            "summary": parsed.get("summary", ""),
            "issues": parsed.get("issues", []),
            "refactored_code": parsed.get("refactored_code", code),
        }

    # =========================
    # JSON PARSER
    # =========================
    def _parse_json(self, text: str):
        try:
            return json.loads(text)
        except:
            pass

        try:
            start = text.find("{")
            end = text.rfind("}")
            return json.loads(text[start:end + 1])
        except:
            return None