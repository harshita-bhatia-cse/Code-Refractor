import json
import os

try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from groq import GroqError
except Exception:
    ChatGroq = None
    ChatPromptTemplate = None
    GroqError = None


class AIReasoningAgent:

    def __init__(self):
        self.chain = None
        if ChatGroq is None or ChatPromptTemplate is None:
            return

        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            # Treat missing key same as missing package: disable gracefully.
            return

        try:
            self.llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0,
                api_key=api_key,
            )

            self.prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a senior software architect analyzing repository quality."),
                ("human", """
Repository metrics:
{metrics}

Analyze the repository and return ONLY valid JSON.

The JSON must contain these keys:
maintainability_score (number 1-10)
complexity_level (low/medium/high)
architecture_type
strengths (array)
weaknesses (array)
recommendations (array)

Return JSON only. No explanation.
""")
            ])

            self.chain = self.prompt | self.llm
        except Exception as exc:
            # Any Groq init failure disables AI reasoning but keeps API alive.
            if GroqError is not None and isinstance(exc, GroqError):
                pass  # known missing/invalid key path; fall back silently
            else:
                # Optional: lightweight log for local debugging without failing CI.
                print(f"[AIReasoningAgent] Groq init skipped: {exc}")
            self.chain = None

    def analyze(self, metrics: dict):
        if self.chain is None:
            return {
                "maintainability_score": 0,
                "complexity_level": "unknown",
                "architecture_type": "unavailable",
                "strengths": [],
                "weaknesses": [
                    "AI reasoning disabled: langchain_groq missing or GROQ_API_KEY not set."
                ],
                "recommendations": [
                    "Install langchain-groq and set GROQ_API_KEY to enable repository-level AI reasoning."
                ],
            }

        formatted_prompt = self.chain.invoke({
            "metrics": json.dumps(metrics)
        })

        # Force parse safely
        try:
            return json.loads(formatted_prompt.content)
        except Exception:
            return {
                "error": "LLM did not return valid JSON",
                "raw_output": formatted_prompt.content
            }
