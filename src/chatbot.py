from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

BASELINE_SYSTEM = (
    "You are a friendly travel assistant. "
    "Answer the user directly from your own knowledge. "
    "You do NOT have access to live weather, flight prices, or booking APIs—"
    "if the user asks for real-time data, give reasonable general advice and say estimates may be wrong."
)


class TravelChatbotBaseline:
    """Single-shot LLM: no tools (baseline for lab comparison)."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def reply(self, user_message: str) -> str:
        logger.log_event("CHATBOT_START", {"input": user_message, "model": self.llm.model_name})
        result = self.llm.generate(user_message, system_prompt=BASELINE_SYSTEM)
        tracker.track_request(
            result.get("provider", "unknown"),
            self.llm.model_name,
            result.get("usage") or {},
            result.get("latency_ms", 0),
        )
        text = (result.get("content") or "").strip()
        logger.log_event("CHATBOT_END", {"chars": len(text)})
        return text
