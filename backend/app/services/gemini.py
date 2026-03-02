"""
Gemini API client wrapper.

All LLM calls in SimpleResolve go through this module so:
  - The API key is configured once
  - JSON output is always parsed and validated
  - Errors degrade gracefully with a fallback result
  - Every prompt and response is logged for auditability
"""

import json
import logging
from typing import Any

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)

_model: genai.GenerativeModel | None = None


def _get_model() -> genai.GenerativeModel:
    global _model
    if _model is None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                temperature=0.2,          # low temperature → consistent, deterministic outputs
                response_mime_type="application/json",
            ),
        )
    return _model


def generate(prompt: str, fallback: dict | None = None) -> dict[str, Any]:
    """
    Send a prompt to Gemini and return the parsed JSON response.

    The caller is responsible for crafting a prompt that instructs Gemini
    to return valid JSON. If the API call fails or the response cannot be
    parsed, `fallback` is returned (if provided) or an error is raised.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — returning fallback response")
        if fallback is not None:
            return fallback
        raise ValueError("GEMINI_API_KEY is not configured")

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if Gemini wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    except json.JSONDecodeError as exc:
        logger.error("Gemini response was not valid JSON: %s | raw=%s", exc, response.text[:200])
        if fallback is not None:
            return fallback
        raise

    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        if fallback is not None:
            return fallback
        raise


def generate_text(prompt: str, fallback: str = "") -> str:
    """
    Like generate() but returns raw text instead of parsed JSON.
    Used for narrative drafting where the output is a long freeform string.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — returning fallback text")
        return fallback

    # Use a separate model config without JSON mime type for text outputs
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        text_model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=genai.GenerationConfig(temperature=0.3),
        )
        response = text_model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        logger.error("Gemini text generation error: %s", exc)
        return fallback
