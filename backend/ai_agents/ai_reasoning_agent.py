import json
import os

import requests

from backend.utils.env import load_project_env


load_project_env()


class AIReasoningAgent:

    def __init__(self):
        self.api_key = (
            os.getenv("LLM_API_KEY", "").strip()
            or os.getenv("GROQ_API_KEY", "").strip()
        )
        self.model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()
        self.base_url = os.getenv(
            "LLM_BASE_URL",
            "https://api.groq.com/openai/v1",
        ).rstrip("/")
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1024"))

    @staticmethod
    def _fallback(reason: str):
        return {
            "maintainability_score": 0,
            "complexity_level": "unknown",
            "architecture_type": "unavailable",
            "strengths": [],
            "weaknesses": [reason],
            "recommendations": [
                "Check LLM_API_KEY, LLM_BASE_URL, and model access to enable repository-level AI reasoning."
            ],
        }

    @staticmethod
    def _extract_json(content: str):
        raw = (content or "").strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) >= 2:
                raw = parts[1]
            raw = raw.removeprefix("json").strip()
        return json.loads(raw)

    def analyze(self, metrics: dict):
        if not self.api_key:
            return self._fallback("AI reasoning disabled: LLM_API_KEY is not set.")

        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a senior software architect analyzing repository quality. "
                        "Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Repository metrics:\n"
                        f"{json.dumps(metrics)}\n\n"
                        "Analyze the repository and return JSON with these keys:\n"
                        "maintainability_score (number 1-10)\n"
                        "complexity_level (low/medium/high)\n"
                        "architecture_type\n"
                        "strengths (array)\n"
                        "weaknesses (array)\n"
                        "recommendations (array)\n"
                    ),
                },
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
                timeout=(10, self.timeout_seconds),
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = self._extract_json(content)
        except Exception as exc:
            return self._fallback(f"AI reasoning unavailable: {exc}")

        return {
            "maintainability_score": parsed.get("maintainability_score", 0),
            "complexity_level": parsed.get("complexity_level", "unknown"),
            "architecture_type": parsed.get("architecture_type", "unavailable"),
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", []),
            "recommendations": parsed.get("recommendations", []),
        }
