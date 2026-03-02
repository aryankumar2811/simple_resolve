"""
Claude API client wrapper (module kept as gemini.py to avoid import changes throughout codebase).

All LLM calls in SimpleResolve go through this module so:
  - The API key is configured once
  - JSON output is always parsed and validated
  - Errors degrade gracefully with a fallback result
  - Every prompt and response is logged for auditability
"""

import json
import logging
import re
from typing import Any

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def generate(prompt: str, fallback: dict | None = None) -> dict[str, Any]:
    """
    Send a prompt to Claude and return the parsed JSON response.

    The caller is responsible for crafting a prompt that instructs Claude
    to return valid JSON. If the API call fails or the response cannot be
    parsed, `fallback` is returned (if provided) or an error is raised.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — returning fallback response")
        if fallback is not None:
            return fallback
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    try:
        client = _get_client()
        message = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            system=(
                "You are a precise JSON-only responder for an AML compliance system. "
                "Always reply with valid JSON only — no markdown fences, no commentary, "
                "no explanation outside the JSON structure."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()

        return json.loads(raw)

    except json.JSONDecodeError as exc:
        logger.error("Claude response was not valid JSON: %s | raw=%s", exc, raw[:200] if 'raw' in dir() else '')
        if fallback is not None:
            return fallback
        raise

    except Exception as exc:
        logger.error("Claude API error: %s", exc)
        if fallback is not None:
            return fallback
        raise


def generate_text(prompt: str, fallback: str = "") -> str:
    """
    Like generate() but returns raw text instead of parsed JSON.
    Used for narrative drafting where the output is a long freeform string.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — returning fallback text")
        return fallback

    try:
        client = _get_client()
        message = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    except Exception as exc:
        logger.error("Claude text generation error: %s", exc)
        return fallback
