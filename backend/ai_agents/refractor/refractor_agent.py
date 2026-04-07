import ast
import json
import os
import time
from typing import Any
from email.utils import parsedate_to_datetime

import requests

from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.refractor.base_refractor import BaseRefractor
from backend.utils.env import load_project_env


load_project_env()


class LLMRefractorAgent(BaseRefractor):
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "gpt-4.1-mini").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "4096"))
        self.max_input_chars = int(os.getenv("LLM_MAX_INPUT_CHARS", "5000"))
        self.max_analysis_chars = int(os.getenv("LLM_MAX_ANALYSIS_CHARS", "2000"))
        self.chunk_enabled = os.getenv("LLM_CHUNK_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
        self.chunk_size_chars = int(os.getenv("LLM_CHUNK_SIZE_CHARS", str(self.max_input_chars)))
        self.chunk_shrink_factor = float(os.getenv("LLM_CHUNK_SHRINK_FACTOR", "0.75"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
        self.retry_backoff_base = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "1.0"))
        self.max_chunks = int(os.getenv("LLM_CHUNK_MAX_CHUNKS", "30"))
        self.enforce_json_response = os.getenv("LLM_ENFORCE_JSON_RESPONSE", "1").strip().lower() not in {
            "0",
            "false",
            "no",
        }

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

        if self.chunk_enabled and len(code) > self.max_input_chars:
            return self._refactor_chunked(code, filename, analysis, language)

        return self._refactor_single(code, filename, analysis, language)

    def _refactor_chunked(self, code: str, filename: str, analysis: dict | None, language: str) -> dict:
        current_chunk_size = min(self.chunk_size_chars, self.max_input_chars)
        last_result = None

        for attempt in range(self.max_retries + 1):
            chunks = self._split_code_chunks(code, max_chars=current_chunk_size)

            if len(chunks) <= 1:
                return self._refactor_single(code, filename, analysis, language)

            if len(chunks) > self.max_chunks:
                return {
                    "ok": False,
                    "language": language,
                    "filename": filename,
                    "error": f"Too many chunks ({len(chunks)}) exceeded LLM_CHUNK_MAX_CHUNKS={self.max_chunks}.",
                    "summary": "Unable to refactor because the file is too large after chunking.",
                    "issues": [],
                    "refactored_code": code,
                }

            refactored_chunks: list[str] = []
            issues: list[str] = []
            successful_chunks = 0
            chunk_too_large = False

            for idx, chunk in enumerate(chunks, start=1):
                chunk_name = f"{filename} (chunk {idx}/{len(chunks)})"
                result = self._refactor_single(chunk, chunk_name, analysis, language)

                if result.get("ok"):
                    successful_chunks += 1
                    refactored_chunks.append(result.get("refactored_code", chunk))
                    issues.extend(result.get("issues", []))
                    continue

                error_text = str(result.get("error", "") or "")
                refactored_chunks.append(chunk)
                issues.append(f"Chunk {idx}/{len(chunks)} failed: {error_text or 'unknown error'}")

                lowered = error_text.lower()
                if any(
                    marker in lowered
                    for marker in [
                        "413",
                        "payload too large",
                        "context length",
                        "token",
                        "too large",
                        "maximum context",
                    ]
                ):
                    chunk_too_large = True

            if chunk_too_large and attempt < self.max_retries:
                current_chunk_size = max(1, int(current_chunk_size * self.chunk_shrink_factor))
                continue

            last_result = {
                "ok": successful_chunks == len(chunks),
                "language": language,
                "filename": filename,
                "error": None if successful_chunks == len(chunks) else "Partial success: some chunk requests failed.",
                "summary": (
                    f"Refactor processed in {len(chunks)} chunks to reduce token usage. "
                    f"{successful_chunks}/{len(chunks)} chunks completed successfully."
                ),
                "issues": list(dict.fromkeys(issues)),
                "refactored_code": "".join(refactored_chunks),
            }
            break

        return last_result or {
            "ok": False,
            "language": language,
            "filename": filename,
            "error": "Chunked refactor failed repeatedly.",
            "summary": "Unable to complete chunked refactor after retries.",
            "issues": [],
            "refactored_code": code,
        }

    def _split_code_chunks(self, code: str, max_chars: int | None = None) -> list[str]:
        effective_max = int(max_chars) if max_chars is not None else self.chunk_size_chars
        chunk_limit = max(1, min(effective_max, self.max_input_chars))
        lines = code.splitlines(keepends=True)
        chunks: list[str] = []
        current = ""

        for line in lines:
            if len(current) + len(line) <= chunk_limit:
                current += line
                continue

            if current:
                chunks.append(current)
                current = ""

            if len(line) > chunk_limit:
                start = 0
                while start < len(line):
                    chunks.append(line[start : start + chunk_limit])
                    start += chunk_limit
            else:
                current = line

        if current:
            chunks.append(current)

        return chunks

    def _make_request(self, payload: dict[str, Any]) -> requests.Response:
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(1, self.max_retries + 2):
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=(10, self.timeout_seconds),
                )
                response.raise_for_status()
                return response
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code in {429, 500, 502, 503, 504} and attempt <= self.max_retries:
                    retry_after = self._retry_after_seconds(exc.response)
                    wait_seconds = retry_after if retry_after is not None else self.retry_backoff_base * (2 ** (attempt - 1))
                    time.sleep(max(1, wait_seconds))
                    continue
                raise
            except (requests.Timeout, requests.ConnectionError):
                if attempt <= self.max_retries:
                    time.sleep(self.retry_backoff_base * (2 ** (attempt - 1)))
                    continue
                raise

        raise RuntimeError("LLM request failed unexpectedly")

    def _refactor_single(self, code: str, filename: str, analysis: dict | None, language: str) -> dict:
        system_prompt = self._build_system_prompt(language)
        analysis_text = self._compact_analysis_text(analysis, language)
        if len(analysis_text) > self.max_analysis_chars:
            analysis_text = analysis_text[: self.max_analysis_chars] + "..."

        user_prompt = (
            f"Filename: {filename}\n"
            f"Language: {language}\n"
            f"Static analysis: {analysis_text}\n\n"
            "Task:\n"
            "1. Identify readability, maintainability, and style issues.\n"
            "2. Refactor the code while preserving behavior.\n"
            "3. Keep the output compact and practical.\n"
            "4. Return valid JSON only.\n\n"
            f"Code:\n{code}"
        )

        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": self._target_output_tokens(code),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.enforce_json_response:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = self._make_request(payload)
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in {400, 422} and "response_format" in payload:
                payload.pop("response_format", None)
                try:
                    response = self._make_request(payload)
                except Exception as retry_exc:
                    return self._request_error_result(code, filename, language, retry_exc)
            else:
                return self._request_error_result(code, filename, language, exc)
        except Exception as exc:
            return self._request_error_result(code, filename, language, exc)

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
                "error": "LLM output was truncated due to token limit",
                "summary": "Reduce input size or lower chunk size to avoid output truncation.",
                "issues": [],
                "refactored_code": code,
                "raw_output": content,
            }

        parsed = self._parse_json_content(content) or self._parse_json_content_loose(content)
        if not parsed:
            return {
                "ok": True,
                "language": language,
                "filename": filename,
                "summary": "Model returned non-JSON output; raw content was used as fallback.",
                "issues": ["Model did not return valid JSON."],
                "refactored_code": content,
                "raw_output": content,
            }

        parsed = self._coerce_parsed_envelope(parsed)

        issues = parsed.get("issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)]
        issues = [str(item) for item in issues]

        refactored_code = str(parsed.get("refactored_code", code))
        if not self._looks_like_code(refactored_code, language):
            issues.append("Model returned metadata/structure instead of usable refactored source code.")
            return {
                "ok": False,
                "language": language,
                "filename": filename,
                "summary": "LLM response was received, but it did not contain valid refactored code.",
                "issues": issues,
                "error": "Non-code refactor output",
                "refactored_code": code,
                "raw_output": content,
            }

        return {
            "ok": True,
            "language": language,
            "filename": filename,
            "summary": str(parsed.get("summary", "")).strip() or "Refactor completed.",
            "issues": issues,
            "refactored_code": refactored_code,
            "raw_output": content,
        }

    @staticmethod
    def _request_error_result(code: str, filename: str, language: str, exc: Exception) -> dict:
        error_text = str(exc)
        summary = "Failed to call LLM service."
        issues: list[str] = []

        if "429" in error_text or "Too Many Requests" in error_text:
            summary = "The LLM provider rate-limited this refactor request. Please wait a bit and retry."
            issues = [
                "Provider rate limit reached.",
                "Retry after a short wait or reduce request frequency.",
            ]

        return {
            "ok": False,
            "language": language,
            "filename": filename,
            "error": f"LLM request failed: {error_text}",
            "summary": summary,
            "issues": issues,
            "refactored_code": code,
        }

    @staticmethod
    def _retry_after_seconds(response: requests.Response | None) -> int | None:
        if response is None:
            return None

        value = response.headers.get("Retry-After")
        if not value:
            return None

        try:
            return max(1, int(value.strip()))
        except Exception:
            pass

        try:
            dt = parsedate_to_datetime(value)
            return max(1, int(dt.timestamp() - time.time()))
        except Exception:
            return None

    def _compact_analysis_text(self, analysis: dict | None, language: str) -> str:
        if not analysis:
            return "{}"

        lang_block = ((analysis.get("analysis") or {}).get(language) or {})
        metrics = lang_block.get("metrics", {}) if isinstance(lang_block, dict) else {}
        compact = {
            "language": language,
            "overall_quality_score": analysis.get("overall_quality_score"),
            "overall_grade": analysis.get("overall_grade"),
            "risk_badges": analysis.get("overall_risk_badges", []),
            "metrics": {
                "lines": metrics.get("lines"),
                "functions": metrics.get("functions"),
                "classes": metrics.get("classes"),
                "conditionals": metrics.get("conditionals", {}),
            },
        }
        return json.dumps(compact, ensure_ascii=False)

    def _target_output_tokens(self, code: str) -> int:
        code_len = len(code or "")
        dynamic = max(300, min(self.max_output_tokens, code_len // 3 + 400))
        return min(dynamic, 1200)

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, Any] | None:
        text = (content or "").strip()
        if not text:
            return None

        if text.startswith("```") and text.endswith("```"):
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1].strip()
                if text.lower().startswith("json"):
                    text = text[4:].strip()

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None

        return None

    @staticmethod
    def _parse_json_content_loose(content: str) -> dict[str, Any] | None:
        text = (content or "").strip()
        if not text:
            return None

        start = text.find("{")
        end = text.rfind("}")
        candidates = [text]
        if start != -1 and end != -1 and end > start:
            candidates.append(text[start : end + 1])

        for candidate in candidates:
            try:
                parsed = ast.literal_eval(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue

        return None

    @classmethod
    def _coerce_parsed_envelope(cls, parsed: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            return {
                "summary": "",
                "issues": [],
                "refactored_code": str(parsed),
            }

        normalized = {
            "summary": str(parsed.get("summary", "")).strip(),
            "issues": parsed.get("issues", []),
            "refactored_code": parsed.get("refactored_code", ""),
        }

        issues = normalized["issues"]
        if not isinstance(issues, list):
            issues = [str(issues)]
        normalized["issues"] = [str(item) for item in issues if str(item).strip()]

        refactored_code = normalized["refactored_code"]
        if isinstance(refactored_code, str):
            nested = cls._parse_json_content(refactored_code) or cls._parse_json_content_loose(refactored_code)
            if isinstance(nested, dict):
                nested_code = nested.get("refactored_code")
                if nested_code:
                    normalized["refactored_code"] = str(nested_code)
                nested_issues = nested.get("issues", [])
                if not isinstance(nested_issues, list):
                    nested_issues = [str(nested_issues)]
                normalized["issues"] = normalized["issues"] or [str(item) for item in nested_issues if str(item).strip()]
                normalized["summary"] = normalized["summary"] or str(nested.get("summary", "")).strip()
            else:
                rebuilt = cls._rebuild_code_from_structure(cls._parse_json_content_loose(refactored_code))
                normalized["refactored_code"] = rebuilt or refactored_code
        else:
            rebuilt = cls._rebuild_code_from_structure(refactored_code if isinstance(refactored_code, dict) else None)
            normalized["refactored_code"] = rebuilt or str(refactored_code)

        if not normalized["refactored_code"]:
            normalized["refactored_code"] = ""

        return normalized

    @classmethod
    def _rebuild_code_from_structure(cls, data: Any) -> str | None:
        if not isinstance(data, dict):
            return None

        class_name = data.get("class")
        methods = data.get("methods")
        if not class_name or not isinstance(methods, list) or not methods:
            return None

        method_blocks = []
        for method in methods:
            if not isinstance(method, dict):
                continue

            method_name = str(method.get("name", "method")).strip() or "method"
            return_type = str(method.get("return_type", "void")).strip() or "void"
            parameters = method.get("parameters", [])
            params_text = cls._format_parameters(parameters)
            body = method.get("body", {})
            body_lines = cls._rebuild_method_body(body)
            if not body_lines:
                body_lines = ["return null;"] if return_type != "void" else []

            indented_body = "\n".join(f"        {line}" for line in body_lines) if body_lines else ""
            method_blocks.append(
                "    public "
                f"{return_type} {method_name}({params_text}) {{\n"
                f"{indented_body}\n"
                "    }"
            )

        if not method_blocks:
            return None

        return "class " + str(class_name).strip() + " {\n" + "\n\n".join(method_blocks) + "\n}"

    @staticmethod
    def _format_parameters(parameters: Any) -> str:
        if not isinstance(parameters, list):
            return ""
        formatted = []
        for param in parameters:
            if isinstance(param, dict):
                p_type = str(param.get("type", "Object")).strip() or "Object"
                p_name = str(param.get("name", "arg")).strip() or "arg"
                formatted.append(f"{p_type} {p_name}")
        return ", ".join(formatted)

    @classmethod
    def _rebuild_method_body(cls, body: Any) -> list[str]:
        if not isinstance(body, dict):
            return []

        lines: list[str] = []
        variables = body.get("variables", [])
        for variable in variables if isinstance(variables, list) else []:
            if not isinstance(variable, dict):
                continue
            var_type = str(variable.get("type", "Object")).strip() or "Object"
            var_name = str(variable.get("name", "value")).strip() or "value"
            var_value = str(variable.get("value", "")).strip()
            if var_value:
                lines.append(f"{var_type} {var_name} = {var_value};")
            else:
                lines.append(f"{var_type} {var_name};")

        statements = body.get("statements", [])
        for statement in statements if isinstance(statements, list) else []:
            lines.extend(cls._normalize_statement(statement))

        return lines

    @classmethod
    def _normalize_statement(cls, statement: Any) -> list[str]:
        if not isinstance(statement, str):
            return []

        text = statement.strip()
        if not text:
            return []

        if text.startswith("if ") or text.startswith("if("):
            text = text.replace("{,", "{").replace("{ ,", "{")
            return [text]

        if text in {"}", "};"}:
            return ["}"]

        if text.endswith(";"):
            return [text]

        if text.endswith("{"):
            return [text]

        if text.startswith("return "):
            return [f"{text};"]

        return [f"{text};"]

    @staticmethod
    def _build_system_prompt(language: str) -> str:
        return (
            "You are a senior software engineer.\n"
            f"The source language is {language}.\n"
            "Refactor for readability, maintainability, and conventional style.\n"
            "Preserve behavior.\n"
            "Return strictly valid JSON with keys: summary, issues, refactored_code.\n"
            "The refactored_code value must contain only source code, never explanations, ASTs, metadata objects, or file descriptions."
        )

    @staticmethod
    def _looks_like_code(text: str, language: str) -> bool:
        candidate = (text or "").strip()
        if not candidate:
            return False

        lowered = candidate.lower()
        if candidate.startswith("{") and any(token in lowered for token in ['"summary"', "'summary'", '"issues"', "'issues'"]):
            return False
        if any(token in candidate for token in ["'class':", "'methods':", '"methods":', '"variables":', "'variables':"]):
            return False

        language_markers = {
            "java": ["class ", "public ", "private ", "protected ", "return ", ";", "{", "}"],
            "python": ["def ", "class ", "return ", ":", "\n"],
            "javascript": ["function ", "const ", "let ", "return ", ";", "{", "}"],
            "typescript": ["function ", "const ", "let ", "return ", ";", "{", "}", "interface "],
            "c": ["return ", ";", "{", "}"],
            "cpp": ["return ", ";", "{", "}"],
        }
        markers = language_markers.get(language, ["return ", ";", "{", "}", "\n"])
        score = sum(1 for marker in markers if marker in candidate)
        return score >= 2
