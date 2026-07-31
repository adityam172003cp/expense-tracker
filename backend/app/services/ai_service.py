import os
from typing import Any

from groq import Client


class AIService:
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required in the environment")
        self.client = Client(api_key=self.api_key)

    def summarize_expenses(self, payload: dict[str, Any]) -> str:
        prompt = self._build_summary_prompt(payload)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or "No insights available."

    def ask(self, question: str, context: dict[str, Any]) -> str:
        prompt = self._build_question_prompt(question, context)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or "No answer available."

    def _build_summary_prompt(self, payload: dict[str, Any]) -> str:
        return (
            "You are a concise personal finance assistant. Use only the exact numbers in this data; never invent or recalculate different numbers.\n"
            f"{payload}\n"
            "Return ONLY a JSON array with 2 or 3 objects. Each object must have exactly these keys: insight and severity. "
            "The insight must be one short qualitative plain-English sentence (maximum 18 words). Do not include any numbers, percentages, currency, counts, dates, or names. "
            "All numeric facts are shown separately by the app and must not be repeated or estimated. "
            "Severity must be one of: info, warning, positive. "
            "Do not use markdown, code fences, Python, explanations, or extra text."
        )

    def _build_question_prompt(self, question: str, context: dict[str, Any]) -> str:
        return (
            "You are a concise financial assistant. Answer using only the exact expense context below.\n"
            f"Context:\n{context}\n"
            f"Question: {question}\n"
            "Return ONLY one short plain-English sentence with the answer. Do not include JSON, markdown, code, calculations, or explanations."
        )
