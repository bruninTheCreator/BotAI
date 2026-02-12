"""
LLM client for planning and suggestions (OpenAI).
Safe-by-default: returns None when not available.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self._client = None

        if self.api_key:
            try:
                from openai import OpenAI  # type: ignore
                self._client = OpenAI(api_key=self.api_key, timeout=self.timeout)
            except Exception:
                self._client = None

    def is_available(self) -> bool:
        return self._client is not None

    def _extract_json(self, text: str) -> Optional[Any]:
        if not text:
            return None

        # 1) Direct JSON parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # 2) JSON inside markdown code block
        block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
        if block_match:
            snippet = block_match.group(1).strip()
            try:
                return json.loads(snippet)
            except Exception:
                pass

        # 3) Try to parse first balanced JSON object/array snippet
        for opener, closer in (("[", "]"), ("{", "}")):
            idx = text.find(opener)
            while idx != -1:
                snippet = self._extract_balanced_snippet(text[idx:], opener, closer)
                if snippet:
                    try:
                        return json.loads(snippet)
                    except Exception:
                        pass
                idx = text.find(opener, idx + 1)

        return None

    def _extract_balanced_snippet(self, text: str, opener: str, closer: str) -> Optional[str]:
        depth = 0
        in_string = False
        escaped = False

        for i, ch in enumerate(text):
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue

            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return text[: i + 1]

        return None

    def _coerce_plan(self, data: Any) -> Optional[List[Dict[str, Any]]]:
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in ("plan", "steps", "actions"):
                value = data.get(key)
                if isinstance(value, list):
                    return value

            if isinstance(data.get("action"), str):
                return [data]

        return None

    def generate_plan(self, command: str, context: str = "") -> Optional[List[Dict[str, Any]]]:
        if not self._client:
            return None

        safe_context = (context or "")[:1200]

        system_prompt = (
            "You are an action planner for a Windows desktop assistant. "
            "Return only JSON, no explanation. "
            "Allowed actions: open_app, type_text, hotkey, click, browse, wait, research_web."
        )
        user_prompt = (
            "Create a step-by-step plan for this command.\n"
            "Output format: JSON array of objects.\n"
            "Examples: [{\"action\":\"open_app\",\"target\":\"notepad\"}]\n"
            f"Command: {command}\n"
            f"Screen context: {safe_context}\n"
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
            )
            content = response.choices[0].message.content or ""
        except Exception:
            return None

        data = self._extract_json(content)
        return self._coerce_plan(data)

    def suggest_action_for_pattern(self, label: str, examples: List[str]) -> Optional[List[Dict[str, Any]]]:
        if not self._client:
            return None

        user_prompt = (
            "Suggest a JSON action plan for this detected pattern. "
            "Use only actions: open_app, type_text, hotkey, click, browse, wait, research_web.\n"
            f"Pattern label: {label}\n"
            f"Examples: {examples[:2]}\n"
            "Return JSON only."
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You return only JSON."},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
            )
            content = response.choices[0].message.content or ""
        except Exception:
            return None

        data = self._extract_json(content)
        return self._coerce_plan(data)
