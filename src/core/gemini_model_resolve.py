"""
Chọn model ID hợp lệ cho Google AI Studio (tránh 404 khi model cũ bị gỡ).
"""
from __future__ import annotations

from typing import Set

import google.generativeai as genai

from src.telemetry.logger import logger


def _strip_models_prefix(name: str) -> str:
    n = name.strip()
    if n.startswith("models/"):
        return n[len("models/") :]
    return n


def list_generate_content_model_ids(api_key: str) -> Set[str]:
    genai.configure(api_key=api_key)
    out: Set[str] = set()
    for m in genai.list_models():
        methods = m.supported_generation_methods or []
        if "generateContent" not in methods:
            continue
        out.add(_strip_models_prefix(m.name))
    return out


def resolve_gemini_model_id(api_key: str, requested: str) -> str:
    """
    Nếu `requested` không còn trên API, chọn model flash mới nhất có sẵn.
    """
    req = _strip_models_prefix(requested)
    if not api_key:
        return req

    available = list_generate_content_model_ids(api_key)
    if req in available:
        return req

    preferences = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash-001",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite",
        "gemini-pro-latest",
    ]
    for p in preferences:
        if p in available:
            logger.log_event(
                "GEMINI_MODEL_FALLBACK",
                {"requested": req, "resolved": p, "reason": "requested_not_in_api"},
            )
            return p

    for name in sorted(available):
        if "flash" in name.lower() and "tts" not in name.lower() and "image" not in name.lower():
            logger.log_event(
                "GEMINI_MODEL_FALLBACK",
                {"requested": req, "resolved": name, "reason": "first_flash_like"},
            )
            return name

    if available:
        picked = sorted(available)[0]
        logger.log_event(
            "GEMINI_MODEL_FALLBACK",
            {"requested": req, "resolved": picked, "reason": "first_alphabetical"},
        )
        return picked

    return req
