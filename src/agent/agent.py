import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker
from src.tools.registry import execute_tool


def _parse_final_answer(text: str) -> Optional[str]:
    m = re.search(r"Final Answer:\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    return m.group(1).strip()


def _parse_action(text: str) -> Optional[Tuple[str, str]]:
    idx = text.rfind("Action:")
    if idx == -1:
        return None
    rest = text[idx + len("Action:") :].strip()
    line = rest.split("\n", 1)[0].strip()
    m = re.match(r"^(\w+)\s*\(\s*(.*)\s*\)\s*$", line, re.DOTALL)
    if not m:
        return None
    return m.group(1), m.group(2)


class ReActAgent:
    """
    Travel ReAct agent: Thought → Action → Observation until Final Answer.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 8):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        tool_lines = []
        for t in self.tools:
            args = t.get("args", [])
            sig = f"{t['name']}({', '.join(args)})"
            tool_lines.append(f"- {sig}: {t['description']}")

        tools_block = "\n".join(tool_lines)
        return f"""You are a travel planning assistant using the ReAct pattern.

Available tools (call exactly one per step when you need data):
{tools_block}

Required output format for EACH turn (use English labels exactly):
Thought: your reasoning.
Action: tool_name(arg1, arg2, ...)
OR when you are done:
Thought: brief wrap-up.
Final Answer: clear answer for the user (can be in Vietnamese).

Rules:
- Use only these tool names: {", ".join(t["name"] for t in self.tools)}.
- For search_flights use IATA airport codes: HAN (Hanoi), DAD (Da Nang), SGN (Ho Chi Minh City).
- Pass string cities to get_weather in English, e.g. Da Nang or "Hanoi, VN".
- Numbers in Action must not use thousand separators (use 5000000 not 5,000,000).
- After you output Action, STOP and wait; the user message will append Observation.
- Do not invent Observation yourself.
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        self.history = []

        scratchpad = ""
        steps = 0
        system = self.get_system_prompt()

        while steps < self.max_steps:
            prompt = (
                f"Question: {user_input}\n\n"
                f"{scratchpad}\n"
                "Continue with the next Thought (and Action or Final Answer) only.\n"
            ).strip()

            result = self.llm.generate(prompt, system_prompt=system)
            tracker.track_request(
                result.get("provider", "unknown"),
                self.llm.model_name,
                result.get("usage") or {},
                result.get("latency_ms", 0),
            )

            raw = (result.get("content") or "").strip()
            logger.log_event("AGENT_LLM_STEP", {"step": steps + 1, "raw_preview": raw[:800]})

            fa = _parse_final_answer(raw)
            if fa is not None:
                logger.log_event("AGENT_FINAL_ANSWER", {"step": steps + 1, "length": len(fa)})
                logger.log_event("AGENT_END", {"steps": steps + 1, "outcome": "final_answer"})
                self.history.append({"step": steps + 1, "llm": raw, "final": True})
                return fa

            action = _parse_action(raw)
            if action is None:
                logger.log_event(
                    "AGENT_PARSE_ERROR",
                    {"step": steps + 1, "detail": "No Final Answer and no parseable Action"},
                )
                scratchpad += f"\n{raw}\nObservation: Model did not provide a valid Action. "
                scratchpad += (
                    "Reply again with exactly: Thought: ... then either "
                    "Action: tool_name(args) or Final Answer: ...\n"
                )
                steps += 1
                continue

            tool_name, arg_str = action
            logger.log_event(
                "AGENT_TOOL_CALL",
                {"step": steps + 1, "tool": tool_name, "args_raw": arg_str[:500]},
            )

            obs = execute_tool(tool_name, arg_str)
            logger.log_event(
                "AGENT_OBSERVATION",
                {"step": steps + 1, "tool": tool_name, "observation_preview": obs[:1500]},
            )

            scratchpad += f"\n{raw}\nObservation: {obs}\n"
            self.history.append(
                {
                    "step": steps + 1,
                    "llm": raw,
                    "tool": tool_name,
                    "observation": obs,
                }
            )
            steps += 1

        logger.log_event("AGENT_END", {"steps": steps, "outcome": "max_steps"})
        return (
            "Agent stopped after max_steps without a Final Answer. "
            "See logs/ for the last model output and observations."
        )
