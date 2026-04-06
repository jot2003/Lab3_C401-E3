import os

from dotenv import load_dotenv

from src.core.llm_provider import LLMProvider


def build_llm_from_env() -> LLMProvider:
    load_dotenv()
    provider = os.getenv("DEFAULT_PROVIDER", "google").strip().lower()
    model = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash").strip()

    if provider == "google":
        from src.core.gemini_provider import GeminiProvider

        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("DEFAULT_PROVIDER=google nhưng thiếu GEMINI_API_KEY trong .env")
        return GeminiProvider(model_name=model, api_key=key)

    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider

        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("DEFAULT_PROVIDER=openai nhưng thiếu OPENAI_API_KEY trong .env")
        return OpenAIProvider(model_name=model or "gpt-4o", api_key=key)

    if provider == "local":
        from src.core.local_provider import LocalProvider

        path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=path)

    raise ValueError(f"DEFAULT_PROVIDER không hợp lệ: {provider} (google | openai | local)")
