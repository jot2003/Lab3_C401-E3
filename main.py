"""
Entry point: baseline chatbot vs travel ReAct agent.
Run from repo root:  python main.py --mode agent
"""
import argparse
import os
import sys

# Repo root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.chatbot import TravelChatbotBaseline
from src.core.provider_factory import build_llm_from_env
from src.tools.registry import get_tool_specs


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Lab 3: Travel chatbot vs ReAct agent")
    parser.add_argument(
        "--mode",
        choices=["chatbot", "agent"],
        default="agent",
        help="chatbot = no tools; agent = ReAct + travel tools",
    )
    parser.add_argument(
        "-q",
        "--question",
        type=str,
        default=(
            "I want to fly from Hanoi (HAN) to Da Nang (DAD) on 2026-04-15. "
            "Budget 8000000 VND total for 2 nights. "
            "Hotel about 900000 VND per night. "
            "Check weather in Da Nang and cheapest flight offer, then say if budget still works."
        ),
        help="User question",
    )
    args = parser.parse_args()
    question = args.question

    llm = build_llm_from_env()

    if args.mode == "chatbot":
        bot = TravelChatbotBaseline(llm)
        print("=== Mode: CHATBOT (no tools) ===\n")
        print(bot.reply(question))
        return

    agent = ReActAgent(llm, get_tool_specs(), max_steps=int(os.getenv("AGENT_MAX_STEPS", "8")))
    print("=== Mode: AGENT (ReAct + OpenWeather + Duffel + budget) ===\n")
    print(agent.run(question))


if __name__ == "__main__":
    main()
