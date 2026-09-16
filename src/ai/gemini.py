from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from ..models import Candidate, EvaluatedCandidate
from ..pipeline.extract import extract_excerpt
from .schemas import ARTICLE_SCHEMA, EVALUATION_SCHEMA


class GeminiProviderError(RuntimeError):
    pass


class GeminiProvider:
    """Small REST adapter for Gemini JSON output; secrets stay server-side."""

    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, model: str, temperature: float = 0.3, api_key: str | None = None, prompts: dict[str, str] | None = None) -> None:
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.prompts = prompts or {}

    def _generate(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise GeminiProviderError("GEMINI_API_KEY is not configured")
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        }
        request = urllib.request.Request(
            self.endpoint.format(model=self.model),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GeminiProviderError(f"Gemini request failed: {type(exc).__name__}") from exc
        try:
            text = body["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise GeminiProviderError("Gemini returned an invalid structured response") from exc
        if not isinstance(result, dict):
            raise GeminiProviderError("Gemini structured response is not an object")
        return result

    def evaluate(self, candidate: Candidate, history: list[Any]) -> EvaluatedCandidate:
        prompt = (
            self.prompts.get("evaluate", "请评估以下候选文本，只返回 JSON。不要改写原文。") + "\n"
            f"标题：{candidate.title}\n作者：{candidate.author or '未知'}\n分类：{candidate.category or '未分类'}\n"
            f"正文：\n{candidate.text[:12000]}"
        )
        raw = self._generate(prompt, EVALUATION_SCHEMA)
        values = {key: _score(raw.get(key)) for key in EVALUATION_SCHEMA["required"] if key != "reason"}
        return EvaluatedCandidate(candidate=candidate, final_score=round(sum(values.values()) / len(values), 2), reason=str(raw.get("reason", "")), **values)

    def edit(self, selected: EvaluatedCandidate, moment: str) -> dict[str, Any]:
        candidate = selected.candidate
        prompt = (
            self.prompts.get("edit", "请为以下文学文本生成导读 JSON。") + " recommendation 40-80字，introduction 50-150字，afterword 100-250字。"
            "excerpt 必须是 original_text 的连续子串，不得改写或拼接；tts_text 只能包含标题、作者、推荐语和正文。\n"
            f"标题：{candidate.title}\n作者：{candidate.author or '未知'}\n分类：{candidate.category or '未分类'}\n"
            f"original_text：\n{candidate.text[:16000]}"
        )
        raw = self._generate(prompt, ARTICLE_SCHEMA)
        excerpt = str(raw.get("excerpt", ""))
        if not excerpt or excerpt not in candidate.text:
            raise GeminiProviderError("Gemini excerpt is not a contiguous substring of original text")
        raw["moment"] = moment
        return raw


def _score(value: Any) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 0
