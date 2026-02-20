"""Groq LLM integration for code explanations."""

import os
from typing import Optional

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore

from dotenv import load_dotenv

load_dotenv()

_LEVEL_PROMPTS = {
    "beginner": (
        "You are a patient coding tutor. Explain the following Python code to a complete "
        "beginner who has never coded before. Use simple language, real-world analogies, "
        "and avoid jargon. Keep it under 200 words."
    ),
    "intermediate": (
        "You are a helpful Python mentor. Explain the following Python code to someone with "
        "about 6 months of coding experience. Mention key concepts, patterns, and why this "
        "code is written the way it is. Keep it under 250 words."
    ),
    "advanced": (
        "You are a senior Python engineer. Give a technical explanation of the following "
        "Python code: discuss design decisions, complexity, edge cases, and potential "
        "improvements. Keep it under 300 words."
    ),
}


class GroqAgent:
    """Wraps the Groq SDK to explain Python code snippets."""

    def __init__(self, model: str = "llama3-8b-8192"):
        self.model = model
        api_key = os.getenv("GROQ_API_KEY")
        if Groq is None:
            raise RuntimeError(
                "The 'groq' package is not installed. Run: pip install groq"
            )
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        self.client = Groq(api_key=api_key)

    def explain(
        self,
        node_label: str,
        source_code: str,
        level: str = "beginner",
    ) -> str:
        """Return a natural-language explanation of *source_code*.

        Parameters
        ----------
        node_label:
            Human-readable name of the function/class being explained.
        source_code:
            The raw Python source code to explain.
        level:
            One of ``"beginner"``, ``"intermediate"``, or ``"advanced"``.
        """
        system_prompt = _LEVEL_PROMPTS.get(level, _LEVEL_PROMPTS["beginner"])
        user_message = (
            f"Please explain this Python code (function/class: `{node_label}`):\n\n"
            f"```python\n{source_code}\n```"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
