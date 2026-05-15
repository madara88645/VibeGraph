import hashlib
import json
import logging
import os
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock

from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from teacher.contract import (
    TeacherReferences,
    build_chat_user_prompt,
    build_contract_system_prompt,
    build_explain_user_prompt,
    build_ghost_user_prompt,
    build_refine_learning_user_prompt,
    build_suggest_learning_user_prompt,
    extract_node_ids_from_summary,
    normalize_chat_text,
    normalize_explain_payload,
    normalize_ghost_payload,
    normalize_learning_steps,
)

load_dotenv()

_openrouter_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(
        (APIConnectionError, APITimeoutError, RateLimitError)
    ),
    reraise=True,
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

_MAX_CACHE_SIZE = 256


def _try_parse_json(text: str) -> dict:
    """Attempt to parse JSON from *text*, stripping markdown fences if present."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(text) from exc


@dataclass
class NarrateStepContext:
    code_snippet: str
    node_id: str
    file_path: str | None = None
    previous_node_id: str | None = None
    edge_context: str = ""
    strategy: str = "smart"
    callers: list[str] = field(default_factory=list)
    callees: list[str] = field(default_factory=list)
    neighbors: list[str] = field(default_factory=list)


class OpenRouterTeacher:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        *,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout_seconds: int | None = None,
        http_referer: str | None = None,
        app_title: str | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = (
            model_name or os.getenv("OPENROUTER_DEFAULT_MODEL") or ""
        ).strip() or "anthropic/claude-haiku-4.5"
        self.timeout_seconds = timeout_seconds or int(
            os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30")
        )
        self.base_url = base_url
        self.http_referer = (
            http_referer or os.getenv("OPENROUTER_HTTP_REFERER") or ""
        ).strip() or None
        self.app_title = (
            app_title or os.getenv("OPENROUTER_APP_TITLE") or ""
        ).strip() or None
        self._explain_cache: OrderedDict[str, dict] = OrderedDict()
        self._cache_lock = RLock()

        if not self.api_key:
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                default_headers=self._default_headers(),
            )

    def _default_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.app_title:
            headers["X-Title"] = self.app_title
        return headers

    @_openrouter_retry
    def _call_openrouter(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

    @_openrouter_retry
    def _call_openrouter_stream(self, **kwargs):
        return self.client.chat.completions.create(stream=True, **kwargs)

    def explain_code(
        self,
        code_snippet: str,
        context: str = "",
        level: str = "intermediate",
        node_id: str = "",
        file_path: str | None = None,
        callers: list[str] | None = None,
        callees: list[str] | None = None,
        neighbors: list[str] | None = None,
    ) -> dict:
        if not self.client:
            return {
                "analogy": "API Key Missing",
                "technical": "OpenRouter API key is required.",
                "key_takeaway": "Add a valid key in AI Settings.",
            }

        cache_key = hashlib.sha256(
            f"{code_snippet}|{level}|{context}|{self.model_name}".encode()
        ).hexdigest()
        with self._cache_lock:
            cached = self._explain_cache.get(cache_key)
            if cached is not None:
                self._explain_cache.move_to_end(cache_key)
                return cached

        tone = _TONE_MAP.get(level, _TONE_MAP["intermediate"])
        refs = TeacherReferences(
            node_id=node_id,
            file_path=file_path,
            callers=callers or [],
            callees=callees or [],
            neighbors=neighbors or [],
        )
        user_prompt = build_explain_user_prompt(
            code_snippet=code_snippet,
            level_tone=tone,
            context=context,
            references=refs,
        )

        try:
            completion = self._call_openrouter(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": build_contract_system_prompt("explain-json"),
                    },
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
            result = (
                normalize_explain_payload(parsed, refs)
                if isinstance(parsed, dict)
                else {**_FALLBACK, "technical": "Could not parse the AI response."}
            )
            with self._cache_lock:
                self._explain_cache[cache_key] = result
                self._explain_cache.move_to_end(cache_key)
                if len(self._explain_cache) > _MAX_CACHE_SIZE:
                    self._explain_cache.popitem(last=False)
            return result
        except APITimeoutError:
            logging.error("OpenRouter API timeout", exc_info=True)
            return {
                "analogy": "Connection Timeout",
                "technical": "The request to OpenRouter timed out.",
                "key_takeaway": "Please try again later.",
            }
        except ValueError as exc:
            logging.error("Error parsing explain_code JSON: %s", exc, exc_info=True)
            return {**_FALLBACK, "technical": "Could not parse the AI response."}
        except Exception as exc:
            logging.error("Error during explain_code: %s", exc, exc_info=True)
            return {
                "analogy": "Connection Error",
                "technical": "An unexpected error occurred.",
                "key_takeaway": "Check OpenRouter status.",
            }

    def chat(
        self,
        code_snippet: str,
        question: str,
        history: list[dict] | None = None,
        project_context: str = "",
        node_id: str = "",
        file_path: str | None = None,
        callers: list[str] | None = None,
        callees: list[str] | None = None,
        neighbors: list[str] | None = None,
    ) -> str:
        if not self.client:
            return "OpenRouter API key missing. Add one in AI Settings."

        refs = TeacherReferences(
            node_id=node_id,
            file_path=file_path,
            callers=callers or [],
            callees=callees or [],
            neighbors=neighbors or [],
        )
        system_msg = build_contract_system_prompt("chat-json")
        user_msg = build_chat_user_prompt(
            code_snippet=code_snippet,
            question=question,
            project_context=project_context,
            references=refs,
        )

        messages: list[dict] = [{"role": "system", "content": system_msg}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_msg})

        try:
            completion = self._call_openrouter(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=800,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"},
            )
            return normalize_chat_text(completion.choices[0].message.content, refs)
        except APITimeoutError:
            logging.error("OpenRouter API timeout", exc_info=True)
            return "OpenRouter API timeout. Please try again."
        except Exception as exc:
            logging.error("Error during chat: %s", exc, exc_info=True)
            return "OpenRouter API error: An unexpected error occurred."

    def stream_chat(
        self,
        code_snippet: str,
        question: str,
        history: list[dict] | None = None,
        project_context: str = "",
        node_id: str = "",
        file_path: str | None = None,
        callers: list[str] | None = None,
        callees: list[str] | None = None,
        neighbors: list[str] | None = None,
    ):
        yield self.chat(
            code_snippet=code_snippet,
            question=question,
            history=history,
            project_context=project_context,
            node_id=node_id,
            file_path=file_path,
            callers=callers,
            callees=callees,
            neighbors=neighbors,
        )

    def narrate_step(self, context: NarrateStepContext) -> dict:
        if not self.client:
            return {
                "narration": "OpenRouter API key missing; narration is unavailable.",
                "relationship": "",
                "importance": "low",
            }

        snippet_hash = hashlib.sha256(context.code_snippet.encode()).hexdigest()[:16]
        cache_key = hashlib.sha256(
            (
                f"ghost|{context.file_path or ''}|{context.node_id}|"
                f"{context.previous_node_id or ''}|{snippet_hash}|{self.model_name}"
            ).encode()
        ).hexdigest()
        with self._cache_lock:
            cached = self._explain_cache.get(cache_key)
            if cached is not None:
                self._explain_cache.move_to_end(cache_key)
                return cached

        transition = (
            f"The ghost just moved from '{context.previous_node_id}' to '{context.node_id}' "
            f"(strategy: {context.strategy})."
            if context.previous_node_id
            else f"The ghost starts at '{context.node_id}' (strategy: {context.strategy})."
        )

        refs = TeacherReferences(
            node_id=context.node_id,
            file_path=context.file_path,
            callers=context.callers,
            callees=context.callees,
            neighbors=context.neighbors,
        )
        system_msg = build_contract_system_prompt("ghost-json")
        user_prompt = build_ghost_user_prompt(
            transition=transition,
            edge_context=context.edge_context,
            code_snippet=context.code_snippet[:1500],
            references=refs,
        )

        try:
            completion = self._call_openrouter(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=150,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content
            parsed = _try_parse_json(raw)
            result = (
                normalize_ghost_payload(parsed, refs)
                if isinstance(parsed, dict)
                else {"narration": "", "relationship": refs.render(), "importance": "low"}
            )
            with self._cache_lock:
                self._explain_cache[cache_key] = result
                self._explain_cache.move_to_end(cache_key)
                if len(self._explain_cache) > _MAX_CACHE_SIZE:
                    self._explain_cache.popitem(last=False)
            return result
        except APITimeoutError:
            logging.error("OpenRouter timeout during ghost narration", exc_info=True)
            return {
                "narration": "Narration timed out.",
                "relationship": "",
                "importance": "low",
            }
        except Exception as exc:
            logging.error("Error during narrate_step: %s", exc, exc_info=True)
            return {"narration": "", "relationship": "", "importance": "low"}

    def refine_learning_path(
        self,
        baseline_steps: list[dict],
        allowed_node_ids: list[str],
    ) -> list[dict]:
        if not self.client:
            return []

        # Send only the fields the model needs to reorder. Stripping `score`,
        # `signals`, `step`, etc. typically halves prompt input tokens for an
        # 8-step window without affecting refinement quality.
        slim_steps = [
            {
                key: step[key]
                for key in ("node_id", "node_name", "file_path", "reason")
                if key in step
            }
            for step in baseline_steps
        ]

        system_msg = build_contract_system_prompt("learning-path-refine")
        user_prompt = build_refine_learning_user_prompt(
            slim_steps=slim_steps,
            allowed_node_ids=allowed_node_ids,
        )

        try:
            completion = self._call_openrouter(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=700,
                top_p=1,
                stream=False,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content
            parsed = _try_parse_json(raw)
            steps = parsed.get("steps") if isinstance(parsed, dict) else []
            return normalize_learning_steps(
                steps,
                allowed_node_ids=allowed_node_ids,
                include_step_numbers=False,
            )
        except Exception as exc:
            logging.error("Error during refine_learning_path: %s", exc, exc_info=True)
            return []

    def suggest_learning_path(
        self,
        nodes_summary: str,
        edges_summary: str,
        file_path: str,
        allowed_node_ids: list[str] | None = None,
    ) -> list[dict]:
        if not self.client:
            return [
                {
                    "step": 1,
                    "node_id": "missing_key",
                    "reason": "OpenRouter API key missing.",
                }
            ]

        node_ids = allowed_node_ids or extract_node_ids_from_summary(nodes_summary)
        system_msg = build_contract_system_prompt("learning-path-suggest")
        user_prompt = build_suggest_learning_user_prompt(
            nodes_summary=nodes_summary,
            edges_summary=edges_summary,
            file_path=file_path,
            allowed_node_ids=node_ids,
        )

        try:
            completion = self._call_openrouter(
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
            if not isinstance(parsed, dict) or "steps" not in parsed:
                raise ValueError(raw)
            normalized = normalize_learning_steps(
                parsed["steps"],
                allowed_node_ids=node_ids,
                include_step_numbers=True,
            )
            if normalized:
                return normalized
            raise ValueError(raw)
        except APITimeoutError:
            logging.error("OpenRouter API timeout", exc_info=True)
            return [
                {
                    "step": 1,
                    "node_id": "timeout",
                    "reason": "The request to OpenRouter timed out. Please try again.",
                }
            ]
        except ValueError as exc:
            logging.error("Error parsing learning_path JSON: %s", exc, exc_info=True)
            return [
                {
                    "step": 1,
                    "node_id": "parse_error",
                    "reason": "Could not parse the AI response.",
                }
            ]
        except Exception as exc:
            logging.error("Error during suggest_learning_path: %s", exc, exc_info=True)
            return [
                {
                    "step": 1,
                    "node_id": "error",
                    "reason": "An unexpected error occurred.",
                }
            ]
