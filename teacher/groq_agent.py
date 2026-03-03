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
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
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
                model=self.model_name,
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

    # ------------------------------------------------------------------
    # Free-form chat about a code snippet
    # ------------------------------------------------------------------

    def chat(
        self,
        code_snippet: str,
        question: str,
        history: list[dict] | None = None,
    ) -> str:
        """
        Free-form conversation about *code_snippet*.

        Parameters
        ----------
        code_snippet : str
            Source code the user is asking about.
        question : str
            The user's current question.
        history : list[dict], optional
            Previous messages: ``[{"role": "user"|"assistant", "content": ...}]``

        Returns
        -------
        str  – Markdown-formatted answer.
        """
        if not self.client:
            return "⚠️ GROQ_API_KEY eksik. `.env` dosyanı kontrol et."

        system_msg = (
            "Sen bir kod öğretmenisin. Kullanıcı şu fonksiyon hakkında soru soruyor:\n"
            f"```python\n{code_snippet}\n```\n"
            "Türkçe veya kullanıcının dilinde, net ve öğretici cevap ver."
        )

        messages: list[dict] = [{"role": "system", "content": system_msg}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": question})

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=800,
                top_p=1,
                stream=False,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"⚠️ Groq API hatası: {e}"

    # ------------------------------------------------------------------
    # Suggest a learning path for a file's nodes / edges
    # ------------------------------------------------------------------

    def suggest_learning_path(
        self,
        nodes_summary: str,
        edges_summary: str,
        file_path: str,
    ) -> list[dict]:
        """
        Ask the LLM to suggest a step-by-step learning order.

        Returns
        -------
        list[dict]  – ``[{"step": int, "node_id": str, "reason": str}, ...]``
        """
        if not self.client:
            return [{"step": 1, "node_id": "N/A", "reason": "GROQ_API_KEY missing."}]

        system_msg = (
            "You are a coding tutor. You MUST reply with ONLY a valid JSON object.\n"
            "The JSON object must have exactly one key: \"steps\" which is an array.\n"
            "Each element: {\"step\": <int>, \"node_id\": \"<str>\", \"reason\": \"<str>\"}.\n"
            "Do NOT wrap in code fences. Output raw JSON only."
        )

        user_prompt = (
            f"Bu Python dosyasındaki ({file_path}) fonksiyonlar ve sınıflar:\n"
            f"{nodes_summary}\n\n"
            f"Aralarındaki çağrı ilişkileri (edges):\n"
            f"{edges_summary}\n\n"
            "Bir öğrenci bu dosyayı öğrenmek istese hangi sırayla incelemeli? "
            "JSON array olarak cevap ver."
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=600,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content
            parsed = _try_parse_json(raw)
            if parsed and "steps" in parsed:
                return parsed["steps"]
            return [{"step": 1, "node_id": "parse_error", "reason": raw}]
        except Exception as e:
            return [{"step": 1, "node_id": "error", "reason": str(e)}]
