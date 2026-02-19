# import json
# from langchain_groq import ChatGroq
# from langchain_core.prompts import ChatPromptTemplate


# class AIReasoningAgent:

#     def __init__(self):

#         self.llm = ChatGroq(
#             model="llama-3.1-8b-instant",
#             temperature=0,
#             max_tokens=500
#         )

#         self.prompt = ChatPromptTemplate.from_messages([
#             ("system",
#              "You are a senior software architect. "
#              "Always return ONLY valid JSON. No explanations. No markdown."),
#             ("human",
#              """
# Here are repository metrics:

# {metrics}

# Return ONLY JSON with:

# {
#   "maintainability_score": number (1-10),
#   "complexity_level": "low" | "medium" | "high",
#   "architecture_type": string,
#   "strengths": list,
#   "weaknesses": list,
#   "recommendations": list
# }
#              """)
#         ])

#         self.chain = self.prompt | self.llm

#     def analyze(self, metrics: dict):

#         response = self.chain.invoke({
#             "metrics": json.dumps(metrics)
#         })

#         raw_output = response.content.strip()

#         print("🔥 LLM RAW OUTPUT:\n", raw_output)

#         # Remove markdown blocks if present
#         if raw_output.startswith("```"):
#             raw_output = raw_output.split("```")[1]

#         try:
#             return json.loads(raw_output)

#         except Exception as e:
#             return {
#                 "error": "Invalid JSON from LLM",
#                 "exception": str(e),
#                 "raw_output": raw_output
#             }

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import json


class AIReasoningAgent:

    def __init__(self):

        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0
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

    def analyze(self, metrics: dict):

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
