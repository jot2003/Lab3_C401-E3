import os
import time
import google.generativeai as genai
from typing import Dict, Any, Optional, Generator

from google.api_core import exceptions as google_api_exceptions

from src.core.llm_provider import LLMProvider
from src.core.gemini_model_resolve import resolve_gemini_model_id


class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        genai.configure(api_key=self.api_key)
        resolved = resolve_gemini_model_id(self.api_key or "", model_name)
        self.model_name = resolved
        self.model = genai.GenerativeModel(resolved)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        
        # In Gemini, system instruction is passed during model initialization or as a prefix
        # For simplicity in this lab, we'll prepend it if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        max_attempts = max(1, int(os.getenv("GEMINI_MAX_RETRIES", "5")))
        response = None
        for attempt in range(max_attempts):
            try:
                response = self.model.generate_content(full_prompt)
                break
            except google_api_exceptions.ResourceExhausted as e:
                # 429: RPM/RPD free tier — chờ rồi thử lại; nếu hết quota ngày thì retry vẫn fail.
                if attempt >= max_attempts - 1:
                    raise
                wait_s = min(120.0, 20.0 + attempt * 12.0)
                time.sleep(wait_s)

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        try:
            content = (response.text or "") if response else ""
        except (ValueError, AttributeError):
            content = ""
            if getattr(response, "candidates", None):
                parts = []
                for c in response.candidates:
                    for p in getattr(c.content, "parts", []) or []:
                        if getattr(p, "text", None):
                            parts.append(p.text)
                content = "\n".join(parts)

        um = getattr(response, "usage_metadata", None)
        if um is not None:
            usage = {
                "prompt_tokens": getattr(um, "prompt_token_count", 0) or 0,
                "completion_tokens": getattr(um, "candidates_token_count", 0) or 0,
                "total_tokens": getattr(um, "total_token_count", 0) or 0,
            }
        else:
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "google"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        response = self.model.generate_content(full_prompt, stream=True)
        for chunk in response:
            yield chunk.text
