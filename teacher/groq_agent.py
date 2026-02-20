import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Structured JSON schema the LLM must follow
_RESPONSE_SCHEMA = {
    "analogy": "A creative, fun metaphor explaining the concept.",
    "technical": "A clear technical explanation of what the code does.",
    "key_takeaway": "One catchy sentence summary.",
}

_SYSTEM_PROMPT = (
    "You are 'Vibe Teacher', an expert coding tutor.\n"
    "You MUST reply with ONLY a valid JSON object — no markdown, no commentary.\n"
    "The JSON object MUST have exactly these keys:\n"
    '  "analogy"       – a creative metaphor for the concept\n'
    '  "technical"     – a clear technical explanation\n'
    '  "key_takeaway"  – one catchy summary sentence\n'
    "Do NOT wrap in code fences. Output raw JSON only."
)

_TONE_MAP = {
    "beginner": "Explain like I'm 5 years old. Use very simple metaphors.",
    "intermediate": "Explain to a junior developer. Balance clarity and technical terms.",
    "advanced": "Explain to a senior engineer. Focus on performance, memory, and advanced patterns.",
}

_FALLBACK = {
    "analogy": "The AI got a bit confused.",
    "technical": "Could not parse the response.",
    "key_takeaway": "AI output format error.",
}


def _try_parse_json(text: str) -> dict | None:
    """Attempt to parse JSON from *text*, stripping markdown fences if present."""
    # Strip possible ```json ... ``` wrapping
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


class GroqTeacher:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Warning: GROQ_API_KEY not found in .env")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)

    def explain_code(
        self,
        code_snippet: str,
        context: str = "",
        level: str = "intermediate",
    ) -> dict:
        """
        Explains *code_snippet* via Groq (Llama 3) and returns structured JSON.

        Parameters
        ----------
        code_snippet : str
            The source code to explain.
        context : str, optional
            Extra context (e.g. "External Library").
        level : str
            One of 'beginner', 'intermediate', 'advanced'.

        Returns
        -------
        dict with keys: analogy, technical, key_takeaway
        """
        if not self.client:
            return {
                "analogy": "API Key Missing",
                "technical": "Check your .env file.",
                "key_takeaway": "No API key = No Vibe.",
            }

        tone = _TONE_MAP.get(level, _TONE_MAP["intermediate"])

        user_prompt = (
            f"Target Audience: {tone}\n\n"
            f"{'Context: ' + context + chr(10) if context else ''}"
            f"Code:\n```python\n{code_snippet}\n```"
        )

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=600,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content
            parsed = _try_parse_json(raw)

            if parsed is None:
                return {**_FALLBACK, "technical": raw}

            # Ensure all expected keys exist
            return {
                "analogy": parsed.get("analogy", _FALLBACK["analogy"]),
                "technical": parsed.get("technical", _FALLBACK["technical"]),
                "key_takeaway": parsed.get("key_takeaway", _FALLBACK["key_takeaway"]),
            }

        except Exception as e:
            return {
                "analogy": "Connection Error",
                "technical": str(e),
                "key_takeaway": "Check Groq API status.",
            }
